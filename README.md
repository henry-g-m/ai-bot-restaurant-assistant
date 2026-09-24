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



Dependencies are managed with pip and pyproject.toml.


Requirements
------------
- Python >=3.12
- pip (standard Python package manager)
- ~2GB free disk space for the downloaded model (facebook/bart-large-mnli).


Setup
-----
From the repo root:

     pip install -e ".[dev]"

This installs the local package and all dependencies listed in pyproject.toml
(fastapi, uvicorn, transformers, torch, pyyaml, pydantic, etc.).


Running locally
----------------
   uvicorn restaurant_bot.main:app --reload

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

GET /admin/status
    Returns {"active_restaurant": "<name>", "menu_items_count": <int>}
    Shows which restaurant is currently active and item count on its menu.

POST /admin/switch-restaurant
    Body:  {"restaurant": "<chinese|mexican>", "password": "<admin_password>"}
    Switches the active restaurant (password-gated). Password is stored in 
    Key Vault under secret name "admin-upload-password".

GET /admin.html
    Serves the admin panel UI (static/admin.html, static/admin.js).

POST /documents
    Multipart upload for RAG document indexing (password-gated).
    Form data:
      - file: <.txt or .pdf file>
      - password: <admin_password>
      - restaurant_id: <chinese|mexican|shared>
    Extracts text, chunks it (~180 words per chunk), embeds with SentenceTransformer,
    and stores in Cosmos DB with restaurant_id filter for segregated RAG queries.


Phase 2 Features (Multi-Restaurant, Admin Panel, Conversational Bot)
--------------------------------------------------------------------

### Multi-Restaurant Support
The bot now supports multiple restaurants (Chinese and Mexican) with:
- **Per-restaurant menus:** data/menu_chinese.yaml and data/menu_mexican.yaml
- **Per-restaurant personalities:** Chinese (eager to help, imperfect English accent),
  Mexican (enthusiastic, playful, Spanish phrases)
- **Per-restaurant replies:** Refusal and help text adapted to each restaurant
- **Active restaurant state:** In-memory module variable, switched via /admin/switch-restaurant

### Document Segregation & RAG
Documents uploaded via the admin panel are stored in Cosmos DB with a restaurant_id
field for segregation:
- Documents tagged with a restaurant_id are only used by that restaurant's RAG
- Documents tagged "shared" are accessible to all restaurants
- Query filters: `WHERE restaurant_id = @restaurant_id OR restaurant_id = "shared"`

### Admin Panel (http://localhost:8000/admin.html)
Requires authentication with the admin password (from Key Vault).

**Features:**
- View current active restaurant and menu item count
- Switch between Chinese and Mexican restaurants (requires password)
- Upload document files (.txt or .pdf) for RAG knowledge base
- Select restaurant for upload (specific or shared across all)
- Monitor upload status with success/error messages

### Conversational Bot
The bot now handles both natural conversations and order actions:
- **Greetings/Questions:** "Hi!" → conversational response
- **Order Instructions:** "Add #1" → extract cart action
- **Natural Language:** "I'd like kung pao chicken" → understands and adds to cart
- **Intent detection uses LLM with optional tool use** (tool_choice="auto"):
  - If the message is an order instruction, the LLM calls the cart_action tool
  - If the message is a greeting or question, the LLM responds naturally
  - Restaurant personality embedded in the system prompt

### Customer UI Redesign
- **Light theme** with modern, clean design
- **Two-column layout:** Left side has navigation tabs, right side has chat
- **Navigation tabs:** About, Menu, Hours, Contact, Reservations, Reviews (placeholders),
  and Chat (fully functional)
- **Dynamic header:** Shows active restaurant name and menu item count
- **Admin link:** "System Admin?" link in footer for admin panel access


Running tests
-------------
   pip install -e ".[dev]"
   pytest tests/ -q

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

**Deployment** (basic chat bot + multi-restaurant with admin & RAG):
See PLAN.md and deploy/PHASE2-DEPLOY.md for complete runbooks.

Quick steps:
1. az webapp config appsettings set ... (set KEY_VAULT_URL)
2. az webapp up --runtime "PYTHON:3.12" --sku F1 --name <your-app-name>
3. az webapp config set ... (set startup command via gunicorn + uvicorn worker)
4. Enable system-assigned managed identity on App Service
5. Grant "Key Vault Secrets User" role to the managed identity

For Cosmos DB setup, see deploy/azure/cosmos-setup.txt and deploy/azure/cosmos-setup-phase2.txt.
For Key Vault setup, see deploy/azure/keyvault-setup.txt.

Test locally first:
   pip install -e ".[dev]"
   uvicorn restaurant_bot.main:app --reload
   Navigate to http://localhost:8000/ for chat UI
   Navigate to http://localhost:8000/admin.html for admin panel

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

.env is gitignored — never commit it. Actual secrets are NOT stored in .env —
they live in Azure Key Vault and are fetched at runtime via DefaultAzureCredential
(see secrets.py). Locally, authenticate once with:

     az login

**Phase 1 Required Secrets:**
- cosmos-endpoint, cosmos-key (Cosmos DB)
- azure-openai-endpoint, azure-openai-key, azure-openai-deployment (Azure OpenAI)

**Phase 2 Additional Secrets:**
- admin-upload-password (password for admin panel access)

On Azure App Service, the app needs a system-assigned managed identity granted
the "Key Vault Secrets User" role on the vault (a deployment-time step, not
needed for local dev).

**Setup Documentation:**
- Phase 1: See deploy/azure/keyvault-setup.txt for vault creation and secret setup
- Phase 1: See deploy/azure/cosmos-setup.txt for Cosmos DB container + vector index
- Phase 2: See deploy/azure/cosmos-setup-phase2.txt for restaurant_id schema update
- Phase 2: See deploy/PHASE2-DEPLOY.md for full deployment runbook with managed
  identity setup and Cosmos indexing policy updates
