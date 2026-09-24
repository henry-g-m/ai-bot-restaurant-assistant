import logging
import threading
from typing import Literal

from openai import AzureOpenAI

from restaurant_bot import embeddings, secrets, vector_store
from restaurant_bot.config import AZURE_OPENAI_API_VERSION, RAG_TOP_K

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant for a restaurant. Answer the customer's question "
    "using only the context provided below. If the context doesn't contain the answer, "
    "say you don't know rather than guessing. Keep answers brief and relevant to the restaurant."
)

_RESTAURANT_PERSONALITIES = {
    "chinese": (
        "You are a person working in a chinese restaurant, your personality eager to help but can't speak or write very good english, "
        "give the feel you are a real chinese speaking person with imperfect spelling and grammar, you accent may come across in the conversation. "
        "Keep responses short and relevant to our Chinese cuisine."
        "Answer the customer's question using only the context provided below. "
        "If the question is not related to the restaurant or taking orders just say you don't know that and can't help."
    ),
    "mexican": (
        "You are a person working in a mexican restaurant, your personality is light hearted, enthusiastic and a bit "
        "silly but can't speak or write very good english, give the feel you are a real mexican speaking person with "
        "imperfect spelling and grammar, through in some spanish for good measure, you accent may come across in the conversation. "
        "Keep responses short and relevant to our Mexican cuisine."
        "Answer the customer's question using only the context provided below. "
        "If the question is not related to the restaurant or taking orders just say you don't know that and can't help."
    ),
}

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


def answer_question(question: str, restaurant_id: Literal["chinese", "mexican"] = "chinese") -> str | None:
    try:
        query_vector = embeddings.embed(question)
        chunks = vector_store.query_similar(query_vector, top_k=RAG_TOP_K, restaurant_id=restaurant_id)
    except Exception:
        logger.exception("RAG retrieval failed")
        return None

    if not chunks:
        return None

    context = "\n\n".join(chunk["text"] for chunk in chunks)
    prompt = _build_prompt(question, context)

    system_prompt = _RESTAURANT_PERSONALITIES.get(restaurant_id, _SYSTEM_PROMPT)

    try:
        response = _get_client().chat.completions.create(
            model=secrets.get_secret("azure-openai-deployment"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        logger.exception("RAG answer generation failed")
        return None
