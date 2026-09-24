import threading

from azure.cosmos import CosmosClient

from restaurant_bot import secrets
from restaurant_bot.config import COSMOS_CONTAINER_NAME, COSMOS_DATABASE_NAME

_container = None
_container_lock = threading.Lock()


def _get_container():
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                client = CosmosClient(secrets.get_secret("cosmos-endpoint"), secrets.get_secret("cosmos-key"))
                database = client.get_database_client(COSMOS_DATABASE_NAME)
                _container = database.get_container_client(COSMOS_CONTAINER_NAME)
    return _container


def upsert_chunk(
    chunk_id: str, source_filename: str, chunk_index: int, text: str, embedding: list[float], uploaded_at: str, restaurant_id: str = "shared"
) -> None:
    _get_container().upsert_item(
        {
            "id": chunk_id,
            "source_filename": source_filename,
            "chunk_index": chunk_index,
            "text": text,
            "embedding": embedding,
            "uploaded_at": uploaded_at,
            "restaurant_id": restaurant_id,
        }
    )


def query_similar(query_embedding: list[float], top_k: int, restaurant_id: str = "shared") -> list[dict]:
    query = (
        "SELECT TOP @top_k c.text, c.source_filename, "
        "VectorDistance(c.embedding, @query_vector) AS score "
        "FROM c WHERE c.restaurant_id = @restaurant_id OR c.restaurant_id = 'shared' "
        "ORDER BY VectorDistance(c.embedding, @query_vector)"
    )
    parameters = [
        {"name": "@top_k", "value": top_k},
        {"name": "@query_vector", "value": query_embedding},
        {"name": "@restaurant_id", "value": restaurant_id},
    ]
    return list(
        _get_container().query_items(query=query, parameters=parameters, enable_cross_partition_query=True)
    )
