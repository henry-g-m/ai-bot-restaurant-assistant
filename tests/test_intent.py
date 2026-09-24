import json
from unittest.mock import MagicMock, patch

from restaurant_bot import intent
from restaurant_bot.menu import Menu, MenuItem

_MENU = Menu([
    MenuItem(number=1, name="Margherita Pizza", price=9.50),
    MenuItem(number=3, name="Coke", price=2.50),
])


def _fake_response(arguments: dict):
    response = MagicMock()
    response.choices[0].message.tool_calls[0].function.arguments = json.dumps(arguments)
    return response


def test_parse_intent_returns_add_for_multiple_items():
    fake_response = _fake_response(
        {
            "items": [
                {"menu_item_number": 1, "operation": "add", "quantity": 1},
                {"menu_item_number": 3, "operation": "add", "quantity": 2},
            ],
        }
    )

    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        result = intent.parse_intent("I want item 1 and 2 of item 3", _MENU, restaurant_id="chinese")

    assert result["items"][0]["menu_item_number"] == 1
    assert result["items"][1]["menu_item_number"] == 3


def test_parse_intent_includes_restaurant_in_system_prompt():
    """System prompt includes restaurant name."""
    fake_response = _fake_response({"items": []})

    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        intent.parse_intent("what's good?", _MENU, restaurant_id="mexican")

    call_args = mock_get_client.return_value.chat.completions.create.call_args
    system_message = call_args[1]["messages"][0]["content"]
    assert "mexican restaurant" in system_message.lower()


def test_parse_intent_uses_personality_prompts():
    """parse_intent uses restaurant personality prompts from rag module."""
    fake_response = _fake_response({"items": []})

    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        # Chinese personality should include mention of imperfect English
        intent.parse_intent("show menu", _MENU, restaurant_id="chinese")

    call_args = mock_get_client.return_value.chat.completions.create.call_args
    system_message = call_args[1]["messages"][0]["content"]
    assert "chinese restaurant" in system_message.lower()
    assert "working in" in system_message.lower()

    # Mexican personality should include mention of light-hearted/enthusiastic
    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        intent.parse_intent("show menu", _MENU, restaurant_id="mexican")

    call_args = mock_get_client.return_value.chat.completions.create.call_args
    system_message = call_args[1]["messages"][0]["content"]
    assert "mexican restaurant" in system_message.lower()


def test_parse_intent_returns_remove_operation():
    fake_response = _fake_response({"items": [{"menu_item_number": 3, "operation": "remove"}]})

    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        with patch("restaurant_bot.intent.secrets.get_secret", return_value="fake-deployment"):
            result = intent.parse_intent("remove the coke", _MENU)

    assert result["items"] == [{"menu_item_number": 3, "operation": "remove"}]


def test_parse_intent_returns_set_quantity_operation():
    fake_response = _fake_response(
        {"items": [{"menu_item_number": 1, "operation": "set_quantity", "quantity": 3}]}
    )

    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        with patch("restaurant_bot.intent.secrets.get_secret", return_value="fake-deployment"):
            result = intent.parse_intent("make that 3 pizzas", _MENU)

    assert result["items"] == [{"menu_item_number": 1, "operation": "set_quantity", "quantity": 3}]


def test_parse_intent_returns_empty_items_for_a_question():
    fake_response = _fake_response({"items": []})

    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = fake_response
        with patch("restaurant_bot.intent.secrets.get_secret", return_value="fake-deployment"):
            result = intent.parse_intent("what cheese is on the pizza", _MENU)

    assert result == {"items": []}


def test_parse_intent_returns_empty_items_on_error():
    with patch.object(intent.rag, "_get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.side_effect = RuntimeError("boom")
        with patch("restaurant_bot.intent.secrets.get_secret", return_value="fake-deployment"):
            result = intent.parse_intent("I'll take a pizza", _MENU)

    assert result == {"items": []}
