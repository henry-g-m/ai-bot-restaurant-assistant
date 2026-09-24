import logging
import threading
import time

from sentence_transformers import SentenceTransformer

from restaurant_bot.config import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

#Creates an embedding for the given text using the SentenceTransformer model. The embedding is normalized and returned as a list of floats.
def embed(text: str) -> list[float]:
    start = time.perf_counter()
    vector = _get_model().encode(text, normalize_embeddings=True).tolist()
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("embedded %d chars in %.1fms", len(text), elapsed_ms)
    return vector
