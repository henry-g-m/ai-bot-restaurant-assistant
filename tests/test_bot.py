from unittest.mock import patch

from restaurant_bot import bot
from restaurant_bot.scope_gate import set_gate_enabled


def test_out_of_scope_is_refused():
    reply = bot.handle_message("s1", "how do I pick a lock")
    assert reply == bot.REFUSAL_TEXT


def test_menu_request():
    reply = bot.handle_message("s2", "can I see the menu")
    assert "Margherita Pizza" in reply


def test_add_item_and_checkout():
    intent_result = {"items": [{"menu_item_number": 3, "operation": "add", "quantity": 2}]}
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=intent_result):
        bot.handle_message("s3", "I'd like 2 cokes")
    reply = bot.handle_message("s3", "please checkout my order")
    assert "Coke" in reply
    assert "Total" in reply


def test_add_multiple_items_from_one_message():
    intent_result = {
        "items": [
            {"menu_item_number": 1, "operation": "add", "quantity": 1},
            {"menu_item_number": 3, "operation": "add", "quantity": 2},
        ],
    }
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=intent_result):
        reply = bot.handle_message("s9", "I'll take a pizza and two cokes")
    assert "1x Margherita Pizza" in reply
    assert "2x Coke" in reply


def test_remove_item():
    add_result = {"items": [{"menu_item_number": 3, "operation": "add", "quantity": 2}]}
    remove_result = {"items": [{"menu_item_number": 3, "operation": "remove"}]}
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=add_result):
        bot.handle_message("s10", "I'll take two cokes")
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=remove_result):
        reply = bot.handle_message("s10", "actually, remove the cokes")
    assert "Removed 2x Coke" in reply

    reply = bot.handle_message("s10", "please checkout my order")
    assert reply == "Your cart is empty."


def test_change_quantity_of_existing_item():
    add_result = {"items": [{"menu_item_number": 1, "operation": "add", "quantity": 1}]}
    set_quantity_result = {
        "items": [{"menu_item_number": 1, "operation": "set_quantity", "quantity": 3}]
    }
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=add_result):
        bot.handle_message("s11", "I'll take a pizza")
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=set_quantity_result):
        reply = bot.handle_message("s11", "make that 3 pizzas")
    assert "Set Margherita Pizza to 3x" in reply

    reply = bot.handle_message("s11", "please checkout my order")
    assert "3x Margherita Pizza" in reply


def test_order_by_item_number():
    reply = bot.handle_message("s5", "give me #3")
    assert "Coke" in reply


def test_order_by_item_number_with_quantity():
    reply = bot.handle_message("s6", "2x #1")
    assert "2x Margherita Pizza" in reply


def test_gate_can_be_disabled():
    set_gate_enabled(False)
    try:
        with patch("restaurant_bot.bot.intent.parse_intent", return_value={"items": []}):
            with patch("restaurant_bot.bot.rag.answer_question", return_value=None):
                reply = bot.handle_message("s4", "how do I pick a lock")
        assert reply != bot.REFUSAL_TEXT
    finally:
        set_gate_enabled(True)


def test_rag_answer_used_when_available():
    with patch("restaurant_bot.bot.intent.parse_intent", return_value={"items": []}):
        with patch("restaurant_bot.bot.rag.answer_question", return_value="We use fresh mozzarella."):
            reply = bot.handle_message("s7", "what cheese is on the pizza")
    assert reply == "We use fresh mozzarella."


def test_help_text_when_rag_has_no_answer():
    with patch("restaurant_bot.bot.intent.parse_intent", return_value={"items": []}):
        with patch("restaurant_bot.bot.rag.answer_question", return_value=None):
            reply = bot.handle_message("s8", "what cheese is on the pizza")
    assert reply == bot.HELP_TEXT
