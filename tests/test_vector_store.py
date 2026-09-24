"""Tests for vector store with restaurant_id filtering."""

from unittest.mock import MagicMock, patch

from restaurant_bot import vector_store


@patch("restaurant_bot.vector_store._get_container")
def test_upsert_chunk_includes_restaurant_id(mock_get_container):
    """Upserted chunk includes restaurant_id field."""
    mock_container = MagicMock()
    mock_get_container.return_value = mock_container

    vector_store.upsert_chunk(
        chunk_id="ch1",
        source_filename="doc.txt",
        chunk_index=0,
        text="Some text",
        embedding=[0.1, 0.2],
        uploaded_at="2026-09-24T00:00:00Z",
        restaurant_id="mexican",
    )

    mock_container.upsert_item.assert_called_once()
    call_args = mock_container.upsert_item.call_args
    upserted_item = call_args[0][0]
    assert upserted_item["restaurant_id"] == "mexican"


@patch("restaurant_bot.vector_store._get_container")
def test_upsert_chunk_defaults_to_shared(mock_get_container):
    """Upserted chunk defaults to 'shared' restaurant_id when not specified."""
    mock_container = MagicMock()
    mock_get_container.return_value = mock_container

    vector_store.upsert_chunk(
        chunk_id="ch1",
        source_filename="doc.txt",
        chunk_index=0,
        text="Some text",
        embedding=[0.1, 0.2],
        uploaded_at="2026-09-24T00:00:00Z",
    )

    mock_container.upsert_item.assert_called_once()
    call_args = mock_container.upsert_item.call_args
    upserted_item = call_args[0][0]
    assert upserted_item["restaurant_id"] == "shared"


@patch("restaurant_bot.vector_store._get_container")
def test_query_similar_filters_by_restaurant_id(mock_get_container):
    """Query includes WHERE clause to filter by restaurant_id."""
    mock_container = MagicMock()
    mock_container.query_items.return_value = []
    mock_get_container.return_value = mock_container

    vector_store.query_similar(query_embedding=[0.1, 0.2], top_k=5, restaurant_id="chinese")

    mock_container.query_items.assert_called_once()
    call_args = mock_container.query_items.call_args
    query = call_args[1]["query"]
    assert "c.restaurant_id = @restaurant_id OR c.restaurant_id = 'shared'" in query

    parameters = call_args[1]["parameters"]
    restaurant_param = next(p for p in parameters if p["name"] == "@restaurant_id")
    assert restaurant_param["value"] == "chinese"


@patch("restaurant_bot.vector_store._get_container")
def test_query_similar_defaults_to_shared(mock_get_container):
    """Query defaults to 'shared' restaurant_id when not specified."""
    mock_container = MagicMock()
    mock_container.query_items.return_value = []
    mock_get_container.return_value = mock_container

    vector_store.query_similar(query_embedding=[0.1, 0.2], top_k=5)

    call_args = mock_container.query_items.call_args
    parameters = call_args[1]["parameters"]
    restaurant_param = next(p for p in parameters if p["name"] == "@restaurant_id")
    assert restaurant_param["value"] == "shared"
