AI Restaurant Ordering Bot (demo)
==================================

A small FastAPI app that lets a user order food via chat. Messages are
gated by a Huggingface zero-shot classifier so the bot only responds to
restaurant/food-ordering requests; anything else is refused.
Features:

  The bot extracts a structured cart intent from free-form text using Azure OpenAI tool-calling.
  - Prompt includes the actual numbered menu (#1 Margherita Pizza, #3 Coke, ...) so the model can only reference real items.
  - Returns {"action": "add_item", "items": [{"menu_item_number": N, "quantity": Q}, ...]} or {"action": "none"}.
  - Any exception (network, missing secrets, malformed response) degrades to {"action": "none"}

  For a single-item substring-matching loop is replaced with a call to intent.parse_intent; each returned item is
  re-validated against the real menu via menu.find_by_number before touching the cart — the LLM only ever points at a menu slot, it never supplies its own price or item text.
  Multiple items in one message are all added, and the confirmation lists them all: "Added 1x Margherita Pizza, 2x Coke to your cart."

  Examples —
  "I feel like having the chicken pasta tonight, add to the order"
  "I'll take a pizza and two cokes" correctly adds both lines"



Dependencies are managed with uv (pyproject.toml + uv.lock).


Requirements
------------
- uv (https://docs.astral.sh/uv/) — install it, then everything else
  below is handled by uv itself.
- Python >=3.12 (uv will fetch a matching interpreter automatically if
  one isn't already installed).
- ~2GB free disk space for the downloaded model (facebook/bart-large-mnli).


Setup
-----
From the repo root:

     uv sync

This creates a .venv/ and installs everything pinned in uv.lock
(fastapi, uvicorn, transformers, torch, pyyaml, pydantic).


Running locally
----------------
   uv run uvicorn restaurant_bot.main:app --reload

Then open http://127.0.0.1:8000/ in a browser for the chat UI.

First request after startup may be slow: the ~1.6GB zero-shot model
downloads from the Huggingface Hub on first use and is cached locally
(default cache: ~/.cache/huggingface/hub). Subsequent runs are fast.


API endpoints
-------------
POST /chat
    Body:   {"session_id": "<any string>", "message": "<user text>"}
    Reply:  {"reply": "<bot text>", "cart": [...], "total": <float>}

    Recognized message patterns:
      - "menu"                 -> shows the numbered menu
      - "<item name>"          -> adds that item to the cart (e.g.
                                   "I'd like a margherita pizza")
      - "#<number>"            -> adds the item with that menu number
                                   (e.g. "give me #3", "2x #1")
      - "checkout" / "confirm" -> shows order summary + total, clears cart
      - anything unrelated to food ordering -> refused

GET /menu
    Returns the menu as JSON: [{"number", "name", "price"}, ...]

GET /scope-gate
    Returns {"enabled": <bool>} — whether the out-of-scope gate is active.

POST /scope-gate
    Body:  {"enabled": <bool>}
    Toggles the out-of-scope gate on/off at runtime. Intended for
    demo/testing only — disabling it removes the safety check that keeps
    the bot restricted to food ordering.

GET /
    Serves the static chat UI (static/index.html, static/app.js).


Running tests
-------------
   uv sync --extra dev        (if pytest is declared as a dev dependency)
   uv run pytest tests/ -q

First test run that touches the scope gate will also download the model
(same one-time cost as above).


Menu data
---------
Menu items live in data/menu.yaml, e.g.:

   items:
     - number: 1
       name: Margherita Pizza
       price: 9.50

Edit this file to change what's on the menu. Each item needs a unique
number, name, and price.


Deployment (Azure App Service)
-------------------------------
This deploys the app as-is to a Linux Python App Service, no Docker.

1. Export a requirements.txt from the uv lockfile so Azure's Oryx
   builder (which uses pip, not uv) can install the same pinned
   versions:

     uv export --no-dev --format requirements-txt > requirements.txt

   Commit this file alongside pyproject.toml, or regenerate it right
   before each deploy.

2. Log in and deploy from the repo root:

     az login
     az webapp up --runtime "PYTHON:3.12" --sku B1 --name <your-app-name>

3. Set the startup command (uvicorn isn't auto-detected the way
   Flask/Django are):

     az webapp config set --name <your-app-name> \
         --resource-group <your-resource-group> \
         --startup-file "uvicorn restaurant_bot.main:app --host 0.0.0.0 --port 8000"

   (Also documented in deploy/azure/startup.txt.)

4. Browse to https://<your-app-name>.azurewebsites.net/

Known limitation: the first request after a cold start triggers the
~1.6GB model download from the Huggingface Hub. On a low-tier SKU (e.g.
B1) this can be slow enough to risk hitting App Service's startup/health
check timeout. Not fixed in this demo; if it becomes a problem, the fix
would be to pre-bake the model into a container image and deploy via Web
App for Containers instead of plain App Service.


Known limitations (by design, demo scope)
------------------------------------------
- No database — the cart is stored in memory per session_id and is lost
  on server restart.
- Item matching by name requires the full item name to appear in the
  message (e.g. "margherita pizza", not just "pizza"). Use the "#<number>"
  form for a more reliable match.
- Single-word messages (e.g. just "checkout") can occasionally be
  misclassified as out-of-scope by the zero-shot model since they lack
  food-related context on their own.
- The classifier call is synchronous and blocks while running, so
  concurrent requests are effectively serialized. Fine for a demo, not
  for production load.

Secrets and Credentials
------------------------
Non-secret local configuration (currently just the Key Vault URL) is
read from a .env file in the repo root via python-dotenv. Copy the
template and fill in your vault:

     cp .env.example .env

.env is gitignored — never commit it. Actual secrets (Cosmos DB
endpoint/key, Azure OpenAI endpoint/key/deployment, admin upload
password) are NOT stored in .env — they live in Azure Key Vault and are
fetched at runtime via DefaultAzureCredential (see secrets.py). Locally,
authenticate once with:

     az login

On Azure App Service, the app instead needs a system-assigned managed
identity granted the "Key Vault Secrets User" role on the vault (a
deployment-time step, not needed for local dev).

See deploy/azure/keyvault-setup.txt for the full one-time setup
(creating the vault, granting yourself access, and populating all six
required secrets) and deploy/azure/cosmos-setup.txt for the Cosmos DB
container + vector index setup.
