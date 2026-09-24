from restaurant_bot.config import EMBEDDING_DIM
from restaurant_bot.embeddings import embed


def test_embed_returns_expected_dimension():
    vector = embed("test")
    assert len(vector) == EMBEDDING_DIM
    assert all(isinstance(v, float) for v in vector)
