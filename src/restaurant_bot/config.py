import os

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "facebook/bart-large-mnli"
MENU_PATH = "data/menu.yaml"

CHUNK_TARGET_WORDS = 180
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".pdf"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

KEY_VAULT_URL = os.environ.get("KEY_VAULT_URL", "")

COSMOS_DATABASE_NAME = "restaurant_bot"
COSMOS_CONTAINER_NAME = "documents"
RAG_TOP_K = 10

AZURE_OPENAI_API_VERSION = "2024-02-01"
