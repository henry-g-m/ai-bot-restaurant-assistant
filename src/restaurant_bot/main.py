from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from restaurant_bot import admin, bot, documents, embeddings, secrets, vector_store
from restaurant_bot.config import KEY_VAULT_URL, MENU_PATH
from restaurant_bot.menu import get_menu_by_restaurant, load_menu
from restaurant_bot.order import get_or_create_cart
from restaurant_bot.scope_gate import is_gate_enabled, is_in_scope, set_gate_enabled

app = FastAPI()

_admin_password: str | None = None


def _verify_admin_password(password: str) -> bool:
    """Verify admin password against the one stored in Key Vault."""
    global _admin_password
    if _admin_password is None:
        return False
    return password == _admin_password


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    cart: list[dict]
    total: float


class ScopeGateRequest(BaseModel):
    enabled: bool


class ScopeGateResponse(BaseModel):
    enabled: bool


class AdminAuthRequest(BaseModel):
    password: str


class AdminStatusResponse(BaseModel):
    active_restaurant: str
    menu_items_count: int


class AdminSwitchRestaurantRequest(BaseModel):
    restaurant: str
    password: str


@app.on_event("startup")
def on_startup() -> None:
    import sys

    global _admin_password

    # Verify KEY_VAULT_URL is configured before attempting to load RAG components
    if not KEY_VAULT_URL:
        print("FATAL: KEY_VAULT_URL environment variable not set. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Pre-load both restaurant menus (fast operation)
    load_menu(MENU_PATH)
    get_menu_by_restaurant("chinese")
    get_menu_by_restaurant("mexican")

    # Load admin password from Key Vault (fail-fast if misconfigured)
    try:
        _admin_password = secrets.get_secret("admin-upload-password")
    except Exception as e:
        print(f"FATAL: Failed to load admin password from Key Vault: {e}", file=sys.stderr)
        sys.exit(1)

    # Note: scope gate model loads lazily on first request to avoid 504 timeout on Azure startup


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    active_restaurant = admin.get_active_restaurant()
    reply = bot.handle_message(request.session_id, request.message, restaurant_id=active_restaurant)
    cart = get_or_create_cart(request.session_id)
    return ChatResponse(reply=reply, cart=cart.as_list(), total=cart.total())


@app.get("/menu")
def menu() -> list[dict]:
    active_restaurant = admin.get_active_restaurant()
    menu_data = get_menu_by_restaurant(active_restaurant)
    return [{"number": item.number, "name": item.name, "price": item.price} for item in menu_data.items]


@app.get("/scope-gate", response_model=ScopeGateResponse)
def get_scope_gate() -> ScopeGateResponse:
    return ScopeGateResponse(enabled=is_gate_enabled())


@app.post("/scope-gate", response_model=ScopeGateResponse)
def set_scope_gate(request: ScopeGateRequest) -> ScopeGateResponse:
    set_gate_enabled(request.enabled)
    return ScopeGateResponse(enabled=is_gate_enabled())


@app.get("/admin/status", response_model=AdminStatusResponse)
def admin_status() -> AdminStatusResponse:
    active_restaurant = admin.get_active_restaurant()
    menu = get_menu_by_restaurant(active_restaurant)
    return AdminStatusResponse(active_restaurant=active_restaurant, menu_items_count=len(menu.items))


@app.post("/admin/switch-restaurant", response_model=AdminStatusResponse)
def admin_switch_restaurant(request: AdminSwitchRestaurantRequest) -> AdminStatusResponse:
    if not _verify_admin_password(request.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")
    try:
        admin.set_active_restaurant(request.restaurant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    active_restaurant = admin.get_active_restaurant()
    menu = get_menu_by_restaurant(active_restaurant)
    return AdminStatusResponse(active_restaurant=active_restaurant, menu_items_count=len(menu.items))


@app.post("/documents")
async def upload_documents(
    file: UploadFile = File(...),
    password: str = Form(...),
    restaurant_id: str = Form(default="shared"),
) -> dict:
    """Upload and index documents for RAG. Requires admin password."""
    if not _verify_admin_password(password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    # Read file content
    content = await file.read()

    # Extract and chunk text
    try:
        text = documents.extract_text(file.filename or "", content)
        chunks = documents.chunk_text(text)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Embed and upsert chunks
    chunk_count = 0
    try:
        for chunk_index, chunk in enumerate(chunks):
            chunk_id = f"{file.filename or 'doc'}_{chunk_index}"
            embedding = embeddings.embed(chunk)
            vector_store.upsert_chunk(
                chunk_id=chunk_id,
                source_filename=file.filename or "unknown",
                chunk_index=chunk_index,
                text=chunk,
                embedding=embedding,
                uploaded_at="2026-09-24T00:00:00Z",  # TODO: use actual timestamp
                restaurant_id=restaurant_id,
            )
            chunk_count += 1
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to index document: {e}")

    return {"message": f"Uploaded {chunk_count} chunks from {file.filename}", "chunk_count": chunk_count}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
