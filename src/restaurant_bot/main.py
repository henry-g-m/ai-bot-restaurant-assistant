from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from restaurant_bot import bot
from restaurant_bot.config import MENU_PATH
from restaurant_bot.menu import load_menu
from restaurant_bot.order import get_or_create_cart
from restaurant_bot.scope_gate import is_gate_enabled, is_in_scope, set_gate_enabled

app = FastAPI()


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


@app.on_event("startup")
def on_startup() -> None:
    load_menu(MENU_PATH)
    is_in_scope("warm up")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    reply = bot.handle_message(request.session_id, request.message)
    cart = get_or_create_cart(request.session_id)
    return ChatResponse(reply=reply, cart=cart.as_list(), total=cart.total())


@app.get("/menu")
def menu() -> list[dict]:
    menu_data = load_menu(MENU_PATH)
    return [{"number": item.number, "name": item.name, "price": item.price} for item in menu_data.items]


@app.get("/scope-gate", response_model=ScopeGateResponse)
def get_scope_gate() -> ScopeGateResponse:
    return ScopeGateResponse(enabled=is_gate_enabled())


@app.post("/scope-gate", response_model=ScopeGateResponse)
def set_scope_gate(request: ScopeGateRequest) -> ScopeGateResponse:
    set_gate_enabled(request.enabled)
    return ScopeGateResponse(enabled=is_gate_enabled())


app.mount("/", StaticFiles(directory="static", html=True), name="static")
