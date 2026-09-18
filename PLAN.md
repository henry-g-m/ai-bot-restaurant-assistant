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
3. `menu.py` + `data/menu.yaml` — verify via `test_menu.py`.
4. `scope_gate.py` — verify `is_in_scope` on sample in/out-of-scope messages.
5. `order.py` — verify via `test_order.py` (add/total/checkout).
6. `bot.py` — verify via message-routing tests.
7. `main.py` endpoints — verify via `uvicorn --reload` + curl.
8. `static/index.html` + `app.js` — verify manually in browser.
9. `README.md` — verify by following it from a clean checkout.
10. Azure deployment via `az webapp up` — verify deployed URL behaves like local.

Full detailed plan (design rationale, assumptions, data formats): `C:\Users\enriq\.claude\plans\async-discovering-whale.md`. 