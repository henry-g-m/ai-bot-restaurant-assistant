from unittest.mock import MagicMock, patch

from restaurant_bot import rag


def test_build_prompt_includes_context_and_question():
    prompt = rag._build_prompt("What are your hours?", "We are open 9-5.")
    assert "We are open 9-5." in prompt
    assert "What are your hours?" in prompt


@patch("restaurant_bot.rag.embeddings.embed", return_value=[0.1, 0.2])
@patch("restaurant_bot.rag.vector_store.query_similar", return_value=[])
def test_answer_question_returns_none_when_no_chunks(mock_query, mock_embed):
    assert rag.answer_question("anything") is None


@patch("restaurant_bot.rag.embeddings.embed", side_effect=RuntimeError("boom"))
def test_answer_question_returns_none_on_retrieval_error(mock_embed):
    assert rag.answer_question("anything") is None


@patch("restaurant_bot.rag.vector_store.query_similar", return_value=[{"text": "Some context chunk."}])
@patch("restaurant_bot.rag.embeddings.embed", return_value=[0.1, 0.2])
def test_answer_question_returns_generated_answer(mock_embed, mock_query):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "Here is your answer."

    with patch.object(rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        with patch("restaurant_bot.rag.secrets.get_secret", return_value="fake-deployment"):
            result = rag.answer_question("What ingredients are in the salad?")

    assert result == "Here is your answer."


@patch("restaurant_bot.rag.vector_store.query_similar", return_value=[{"text": "Some context chunk."}])
@patch("restaurant_bot.rag.embeddings.embed", return_value=[0.1, 0.2])
def test_answer_question_returns_none_on_generation_error(mock_embed, mock_query):
    with patch.object(rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.side_effect = RuntimeError("boom")
        with patch("restaurant_bot.rag.secrets.get_secret", return_value="fake-deployment"):
            result = rag.answer_question("What ingredients are in the salad?")

    assert result is None
