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