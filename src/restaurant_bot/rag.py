import logging
import threading

from openai import AzureOpenAI

from restaurant_bot import embeddings, secrets, vector_store
from restaurant_bot.config import AZURE_OPENAI_API_VERSION, RAG_TOP_K

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant for a restaurant. Answer the customer's question "
    "using only the context provided below. If the context doesn't contain the answer, "
    "say you don't know rather than guessing. Keep answers brief and relevant to the restaurant."
)

_client = None
_client_lock = threading.Lock()


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = AzureOpenAI(
                    azure_endpoint=secrets.get_secret("azure-openai-endpoint"),
                    api_key=secrets.get_secret("azure-openai-key"),
                    api_version=AZURE_OPENAI_API_VERSION,
                )
    return _client


def _build_prompt(question: str, context: str) -> str:
    return f"Context:\n{context}\n\nQuestion: {question}"


def answer_question(question: str) -> str | None:
    try:
        query_vector = embeddings.embed(question)
        chunks = vector_store.query_similar(query_vector, top_k=RAG_TOP_K)
    except Exception:
        logger.exception("RAG retrieval failed")
        return None

    if not chunks:
        return None

    context = "\n\n".join(chunk["text"] for chunk in chunks)
    prompt = _build_prompt(question, context)

    try:
        response = _get_client().chat.completions.create(
            model=secrets.get_secret("azure-openai-deployment"),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        logger.exception("RAG answer generation failed")
        return None
