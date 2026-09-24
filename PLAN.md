# PLAN.md

## Project Description
An AI bot assistant  to help user order food from a restaurant. The bot will take user input, process the order, and provide confirmation.
The important features of the bot include:
- It can't be exploited to be used for something else, like asking for illegal activities or personal information, coding problems, etc.
- The bot only responds to questions related to the restaurant and food ordering process.
This is a demo/learning excercise. Keep the bot simple and focused on the task of food ordering.

## Tech Stack
- Python
- FastAPI
- Azure deployment
- Huggingface zero-shot classification model for intent detection

## Future improvements:
- Langchain for LLM orchestration
- RAG

## Implementation Plan

### Key decisions
- `requires-python` relaxed from `>=3.14` to `>=3.12` in `pyproject.toml` for realistic torch/transformers wheel availability (verified locally on the only available interpreter, 3.14 — installed cleanly).
- Menu file format: YAML (`data/menu.yaml`), not JSON.
- Azure deploy: plain App Service via `az webapp up`, no Docker. First cold start may be slow while the ~1.6GB `bart-large-mnli` model downloads — documented limitation, not solved.
- Intent detection is binary only: in-scope (food ordering) vs out-of-scope, via Huggingface zero-shot classification. No sub-intent classification — order parsing/state is rule-based (keyword/substring matching), not ML.
- No database — in-memory cart per session (`session_id` generated client-side, sent with every request).
- The scope gate can be toggled on/off at runtime via a `/scope-gate` API endpoint (demo/testing use only).

### Project structure
```
ai_bot_restaurant-assistant/
├── pyproject.toml                 # requires-python>=3.12, deps: fastapi, uvicorn, transformers, torch, pyyaml, pydantic
├── README.md                      # setup/run/deploy instructions
├── data/
│   └── menu.yaml                  # menu items + prices
├── src/
│   └── restaurant_bot/
│       ├── __init__.py
│       ├── main.py                # FastAPI app, endpoints, static mount, startup loading
│       ├── config.py              # model name constant, menu file path constant
│       ├── menu.py                # load_menu(), Menu/MenuItem, find()
│       ├── scope_gate.py          # is_in_scope(text), gate enable/disable toggle
│       ├── order.py               # Cart/session state: add/remove/view/checkout
│       └── bot.py                 # gate -> parse -> cart -> reply text
├── static/
│   ├── index.html                 # single-page chat UI
│   └── app.js                     # fetch() calls to /chat, session id, rendering
├── tests/
│   ├── test_scope_gate.py
│   ├── test_order.py
│   └── test_menu.py
└── deploy/
    └── azure/
        └── startup.txt            # documented App Service startup command
```

### API endpoints (`main.py`)
- `GET /` and `/app.js` — served via `StaticFiles(directory="static", html=True)`.
- `POST /chat` — `{session_id, message}` -> `{reply, cart, total}`, delegates to `bot.handle_message`.
- `GET /menu` — returns the loaded menu as JSON.
- `GET /scope-gate` / `POST /scope-gate {enabled}` — read/toggle whether the scope gate runs.
- Startup event loads the menu and warms the HF pipeline once (module-level singletons).

### Scope gate (`scope_gate.py`)
- `transformers.pipeline("zero-shot-classification", model="facebook/bart-large-mnli")`, loaded once.
- Candidate labels: `["ordering food at a restaurant", "something unrelated to ordering food"]`.
- `is_in_scope(text) -> bool` compares top-1 label under `multi_label=False`.
- `is_gate_enabled()` / `set_gate_enabled(enabled)` back the `/scope-gate` endpoint; `bot.handle_message` only enforces the gate when enabled.

### Order processing (`order.py`, `bot.py`)
- `Cart` dataclass with `CartLine(name, unit_price, quantity)`; `add`, `remove`, `total`, `as_list`, `clear`. In-memory `_sessions: dict[str, Cart]`.
- `bot.handle_message(session_id, message)`: gate check (if enabled) -> keyword routing (`"menu"`, `"checkout"`/`"confirm"`, item name substring match with optional quantity) -> cart mutation -> reply string.

### Implementation order (with verification)
1. `pyproject.toml` deps/version — verify `pip install -e .` succeeds. **Done.**
2. Scaffold package structure — verify `import restaurant_bot` works. **Done.**
3. `menu.py` + `data/menu.yaml` — verify via `test_menu.py`. **Done.**
4. `scope_gate.py` — verify `is_in_scope` on sample in/out-of-scope messages. **Done.**
5. `order.py` — verify via `test_order.py` (add/total/checkout). **Done.**
6. `bot.py` — verify via message-routing tests. **Done.**
7. `main.py` endpoints — verify via `uvicorn --reload` + curl. **Done.**
8. `static/index.html` + `app.js` — verify manually in browser. **Done.**
9. `README.txt` — verify by following it from a clean checkout. **Done.**
10. Azure deployment via `az webapp up` — verify deployed URL behaves like local. **In progress** — see "Azure Deployment" section below.

Also done: migrated dependency management from pip to uv (`uv.lock`, `[build-system]`/`[tool.setuptools.packages.find]` added to `pyproject.toml` so uv can build/install the local package; `pytest`/`httpx` moved to a `[dependency-groups] dev` group via `uv add --dev`); added explicit `number` field to menu items so users can order by `#<number>`.

Full detailed plan (design rationale, assumptions, data formats): `C:\Users\enriq\.claude\plans\async-discovering-whale.md`.

## RAG Extension (Cosmos DB vector search + Azure OpenAI + document upload UI)

### Key decisions
- Vector store: Azure Cosmos DB for NoSQL, native vector search (vector embedding + vector index policy on the container). Container created manually (documented in `deploy/azure/cosmos-setup.txt`), not by app code.
- Embeddings: local `sentence-transformers/all-MiniLM-L6-v2` (384-dim), lazy-singleton pattern like `scope_gate.py`.
- Answer generation: Azure OpenAI chat completion (`openai` package's `AzureOpenAI` client), using retrieved chunks as context.
- Secrets: Azure Key Vault via `DefaultAzureCredential` (Azure CLI login locally, managed identity on App Service). Secret names: `cosmos-endpoint`, `cosmos-key`, `azure-openai-endpoint`, `azure-openai-key`, `azure-openai-deployment`, `admin-upload-password`.
- Upload UI: new `static/admin.html` + `POST /documents` in the same FastAPI app, protected by a shared password (from Key Vault).
- Chunking: paragraph-then-sentence-aware, ~180-word target (matches MiniLM's real ~256-token capacity, avoids silent truncation), no overlap.
- Partition key: `/source_filename`.
- Testing: unit tests cover chunking/prompt-building/fallback logic only; Cosmos/Key Vault/Azure OpenAI integration verified manually against real resources.
- Existing rule-based flow in `bot.py` (gate → menu → checkout → `#number` → item-name match) is untouched; RAG only replaces the final `HELP_TEXT` fallback.

### New files
```
src/restaurant_bot/
├── secrets.py       # Key Vault singleton, get_secret(name)
├── embeddings.py     # SentenceTransformer singleton, embed(text) -> list[float]
├── vector_store.py    # Cosmos client singleton, upsert_chunk(...), query_similar(embedding, top_k)
├── documents.py      # extract_text(filename, bytes) for .txt/.pdf, chunk_text(text)
└── rag.py          # answer_question(question) -> str | None
static/
├── admin.html       # upload form (file + password), reachable at /admin.html via existing StaticFiles mount
└── admin.js
tests/
├── test_documents.py  # chunking + extraction, no Azure deps
└── test_rag.py      # prompt construction + fallback behavior, mocked vector_store/openai
deploy/azure/
├── cosmos-setup.txt    # az cosmosdb sql container create with vector policy
└── keyvault-setup.txt   # secret creation + managed identity access grant
```

### New dependencies
```
uv add azure-cosmos sentence-transformers openai azure-keyvault-secrets azure-identity pypdf
```

### Implementation order (with verification)
1. `documents.py` (extraction + chunking) — verify via `test_documents.py`.
2. `embeddings.py` — verify `embed("test")` returns a 384-length list.
3. `secrets.py` + manually create Key Vault secrets — verify `get_secret(...)` works locally via `az login`.
4. Manually create Cosmos container with vector policy — verify via `az cosmosdb sql container show`.
5. `vector_store.py` — verify manually (upsert test items, confirm nearest-neighbor query works).
6. `main.py` `/documents` endpoint + `static/admin.html`/`admin.js` — verify by uploading a `.txt` and checking Cosmos.
7. `rag.py` — verify manually against real uploaded content; confirm `None` on broken OpenAI key.
8. `bot.py` fallback wiring — verify existing test suite still passes, then manually confirm RAG/HELP_TEXT behavior.
9. Startup secret-warming in `main.py` — verify fail-fast behavior on misconfigured Key Vault URL.
10. Full regression: `uv run pytest tests/ -q` + manual smoke test of chat + admin UI.

Full detailed plan (design rationale, assumptions, Cosmos schema): `C:\Users\enriq\.claude\plans\humble-puzzling-tarjan.md`. 

## Azure Deployment

### Key decisions
- **Resource group:** `rg-chat-bot` (existing — already holds `small-openai` Azure OpenAI resource and `restaurant-bot-kv` Key Vault). **Region:** `eastus2`. **App name:** `chat-bot-restaurant-egm` → `https://chat-bot-restaurant-egm.azurewebsites.net/`.
- **SKU: F1 (Free tier)**, not the B1 originally planned. This subscription had **zero App Service Plan quota** for any Linux SKU (F1 and B1 both) in `eastus2` at deploy time — nothing had ever been deployed on it. A self-service increase via `az quota update` was rejected outright (`QuotaNotAvailableForResource`); the fix was a quota request through the Azure Portal's Quotas blade, which Azure granted for **both F1 and B1**. F1 was chosen anyway to keep the deployment free, since this is a demo project.
- **Firewall tradeoff (deliberate, accepted risk):** `small-openai`'s network ACL was originally locked to `defaultAction: Deny` with only `vnet01/subnet-1` (in this same resource group) allowed via a VNet service-endpoint rule — not a private endpoint. F1 does **not** support Regional VNet Integration (that requires Basic tier or above), so the app can't reach Azure OpenAI through that VNet rule. Instead, `small-openai`'s `defaultAction` was set to `Allow` (open to all networks). The API key (from Key Vault) is still required for every call — this only removes the network-layer restriction, not authentication. Accepted for this demo's threat model (no PII/payment data); revisit if this ever moves to B1 (quota for it is already granted) to restore VNet integration and re-lock the firewall.
- Container Apps was considered as an alternative (its Consumption plan draws from a separate quota pool, `Microsoft.App` not `Microsoft.Web`, and might not have hit the same wall) but not pursued — would require containerizing the app first (no Dockerfile exists), and its scale-to-zero behavior would reload the ~1.6GB `bart-large-mnli` model into memory on every cold start after idle, which is worse than App Service's one-time cold start for this workload.

### Deploy steps (runbook)
```bash
# 1. Export pinned deps for Azure's Oryx builder (uses pip, not uv)
uv export --no-dev --format requirements-txt > requirements.txt

# 2. Create + deploy the App Service (from repo root)
az webapp up --runtime "PYTHON:3.12" --sku F1 \
    --name chat-bot-restaurant-egm \
    --resource-group rg-chat-bot --location eastus2

# 3. Set the startup command (uvicorn isn't auto-detected for FastAPI)
az webapp config set --name chat-bot-restaurant-egm \
    --resource-group rg-chat-bot \
    --startup-file "uvicorn restaurant_bot.main:app --host 0.0.0.0 --port 8000"

# 4. Enable system-assigned managed identity (so the app can read Key Vault secrets)
az webapp identity assign --name chat-bot-restaurant-egm --resource-group rg-chat-bot

# 5. Grant that identity "Key Vault Secrets User" on restaurant-bot-kv
az role assignment create --role "Key Vault Secrets User" \
    --assignee <principalId from step 4> \
    --scope $(az keyvault show --name restaurant-bot-kv --query id -o tsv)

# 6. Open small-openai's firewall (F1 can't VNet-integrate — see tradeoff above)
az cognitiveservices account update --name small-openai --resource-group rg-chat-bot \
    --network-acls-default-action Allow

# 7. Smoke test
# Browse https://chat-bot-restaurant-egm.azurewebsites.net/ and exercise
# menu, checkout, and a RAG/intent-parsing message end-to-end.
```

If quota is ever requested again for a similar resource, note that `az quota show/update --scope subscriptions/<id>/providers/Microsoft.Web/locations/<region>` (the `quota` CLI extension, after `az provider register --namespace Microsoft.Quota`) can at least *read* current limits instantly — useful for confirming a Portal-submitted request has landed without waiting on a notification.

---

## Phase 2: Multi-Restaurant UI, Document Segregation, Admin Panel

**Status: Design Complete (2026-09-24), Ready for Implementation**

### Overview
Phase 2 adds multi-restaurant support (Chinese/Mexican) with separate menus, bot personalities, and RAG document segregation. System admin can switch active restaurant and upload documents via admin panel. Customer-facing UI redesigned with light theme, 6 placeholder sections, and clear separation from admin interface.

### Key Decisions (Confirmed 2026-09-24)
1. **Restaurant Switching:** Single active restaurant (in-memory module variable, resets on restart — acceptable for demo/admin)
2. **Bot Personality:** Full per-restaurant persona (hardcoded reply strings in bot.py + system prompt in rag.py, not just RAG-generated)
3. **Menus:** Two fixed YAML files (data/menu_chinese.yaml, data/menu_mexican.yaml), admin selects active one
4. **Document Segregation:** One Cosmos container, restaurant_id field + "shared" value for cross-restaurant docs (policies, hours). Query filter: `WHERE restaurant_id = @restaurant_id OR restaurant_id = "shared"`
5. **Customer UI:** Light theme, 6 placeholder tabs (About, Menu Preview, Locations/Hours, Contact, Reservations, Reviews), Chat tab is only working section, "System Admin?" link in footer
6. **Admin Auth:** Password stored in Key Vault (admin-upload-password secret), verified on /documents upload and /admin/switch-restaurant endpoints

### 32-Step Implementation Plan (9 Phases)

#### Phase 2.1: Infrastructure & Data Model
- **admin.py** (NEW, ~30 LOC): Module-level `_active_restaurant` variable, getter/setter with validation
- **data/menu_chinese.yaml** (NEW): 8-10 Chinese dishes, numbers 1-10, prices $7-15
- **data/menu_mexican.yaml** (NEW): 8-10 Mexican dishes, numbers 1-10, prices $8-14
- **menu.py** (MODIFY, +15 LOC): Add `_menu_cache` dict, new `get_menu_by_restaurant(restaurant: str) -> Menu`
- **config.py** (MODIFY, +5 LOC): Add MENU_CHINESE_PATH, MENU_MEXICAN_PATH constants

#### Phase 2.2: Vector Store & RAG Personality
- **vector_store.py** (MODIFY, +10 LOC): Add `restaurant_id: str` param to upsert_chunk() and query_similar(); WHERE clause filters by restaurant_id + "shared"
- **rag.py** (MODIFY, +25 LOC): Pass restaurant_id through; create `_RESTAURANT_PERSONALITIES` dict; build restaurant-specific system prompt

#### Phase 2.3: Bot Personality
- **bot.py** (MODIFY, +40 LOC): Add `restaurant_id: str` param to handle_message(); create `_RESTAURANT_REPLIES` dict; use get_menu_by_restaurant(); replace hardcoded reply strings
- **intent.py** (MODIFY optional, +5 LOC): Add restaurant_id param; enhance system prompt with restaurant name

#### Phase 2.4: Backend API (main.py)
- Add `_verify_admin_password(password: str) -> bool` helper
- Add Pydantic models for auth requests/responses
- **POST /documents** (~60 LOC): Multipart upload (file, password, restaurant_id). Validates auth, file type, size. Extracts, chunks, embeds, upserts with restaurant_id.
- **POST /admin/switch-restaurant**: Toggle active restaurant (password-gated)
- **GET /admin/status**: Return {active_restaurant, menu_items_count} (public, no auth)
- **MODIFY GET /menu**: Use active restaurant to select menu
- **MODIFY POST /chat**: Pass active restaurant to bot.handle_message()
- **MODIFY on_startup()**: Pre-load menus, verify admin password in Key Vault (fail-fast)

#### Phase 2.5: Frontend Redesign (Customer UI)
- **static/index.html** (REPLACE, ~150 LOC): Light theme, header with restaurant name, 6 nav tabs, Chat (active) + placeholders, footer with "System Admin?" link

#### Phase 2.6: Frontend Logic (JavaScript)
- **static/app.js** (MODIFY, +60 LOC): Tab switching, fetch restaurant name + menu preview
- **static/admin.js** (NEW, ~120 LOC): Upload form + toggle buttons with password auth

#### Phase 2.7: Testing
- **tests/test_admin.py** (NEW): State management (get/set, validation)
- **tests/test_vector_store.py** (NEW/EXTEND): Mock Cosmos, verify restaurant_id filtering
- **tests/test_rag.py** (MODIFY, +30 LOC): Verify restaurant_id passed, system prompt includes restaurant name
- **tests/test_bot.py** (MODIFY, +40 LOC): Verify menu + replies differ per restaurant
- **tests/test_menu.py** (MODIFY, +20 LOC): Test get_menu_by_restaurant()

#### Phase 2.8: Integration & Deployment Prep
- Manual E2E test (local): chat, menu preview, admin upload, restaurant toggle
- Full regression: `pytest tests/ -v`
- Export requirements.txt for Azure Oryx
- Manual Cosmos indexing policy update for restaurant_id

#### Phase 2.9: Documentation
- Update PLAN.md with Phase 2 summary
- Update README.md with admin features guide

### Effort & Complexity
- **Total:** ~700 LOC added (6 new files, ~14 modified)
- **Complexity:** ~150 LOC LOW, ~550 LOC MEDIUM, HIGH effort on regression/E2E testing
- **Risk:** LOW (new code isolated, backward-compatible, no breaking changes)

### Critical Files
admin.py, menu_*.yaml, menu.py, vector_store.py, rag.py, bot.py, main.py, index.html, admin.html, app.js, admin.js

### Next Steps
1. Next Claude session starts with this PLAN.md as context
2. Implement Phase 2.1 through 2.9 following dependency order
3. Run full test suite + manual E2E before committing Phase 2