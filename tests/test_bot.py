from unittest.mock import patch

from restaurant_bot import bot
from restaurant_bot.scope_gate import set_gate_enabled


def test_out_of_scope_is_refused():
    reply = bot.handle_message("s1", "how do I pick a lock")
    assert "Chinese restaurant" in reply and "help with ordering" in reply


def test_menu_request():
    reply = bot.handle_message("s2", "can I see the menu")
    assert "Kung Pao Chicken" in reply


def test_add_item_and_checkout():
    intent_result = {"items": [{"menu_item_number": 3, "operation": "add", "quantity": 2}]}
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=intent_result):
        bot.handle_message("s3", "I'd like 2 General Tso's")
    reply = bot.handle_message("s3", "please checkout my order")
    assert "General Tso's Chicken" in reply
    assert "Total" in reply


def test_add_multiple_items_from_one_message():
    intent_result = {
        "items": [
            {"menu_item_number": 1, "operation": "add", "quantity": 1},
            {"menu_item_number": 3, "operation": "add", "quantity": 2},
        ],
    }
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=intent_result):
        reply = bot.handle_message("s9", "I'll take a kung pao and two general tso's")
    assert "1x Kung Pao Chicken" in reply
    assert "2x General Tso's Chicken" in reply


def test_remove_item():
    set_gate_enabled(False)
    try:
        add_result = {"items": [{"menu_item_number": 3, "operation": "add", "quantity": 2}]}
        remove_result = {"items": [{"menu_item_number": 3, "operation": "remove"}]}
        with patch("restaurant_bot.bot.intent.parse_intent", return_value=add_result):
            bot.handle_message("s10", "I'll take two general tso's")
        with patch("restaurant_bot.bot.intent.parse_intent", return_value=remove_result):
            reply = bot.handle_message("s10", "actually, remove the general tso's")
        assert "Removed 2x General Tso's Chicken" in reply

        reply = bot.handle_message("s10", "please checkout my order")
        assert reply == "Your cart is empty."
    finally:
        set_gate_enabled(True)


def test_change_quantity_of_existing_item():
    set_gate_enabled(False)
    try:
        add_result = {"items": [{"menu_item_number": 1, "operation": "add", "quantity": 1}]}
        set_quantity_result = {
            "items": [{"menu_item_number": 1, "operation": "set_quantity", "quantity": 3}]
        }
        with patch("restaurant_bot.bot.intent.parse_intent", return_value=add_result):
            bot.handle_message("s11", "I'll take kung pao chicken")
        with patch("restaurant_bot.bot.intent.parse_intent", return_value=set_quantity_result):
            reply = bot.handle_message("s11", "make that 3")
        assert "Set Kung Pao Chicken to 3x" in reply

        reply = bot.handle_message("s11", "please checkout my order")
        assert "3x Kung Pao Chicken" in reply
    finally:
        set_gate_enabled(True)


def test_order_by_item_number():
    set_gate_enabled(False)
    try:
        reply = bot.handle_message("s5", "give me #3")
        assert "General Tso's Chicken" in reply
    finally:
        set_gate_enabled(True)


def test_order_by_item_number_with_quantity():
    set_gate_enabled(False)
    try:
        reply = bot.handle_message("s6", "2x #1")
        assert "2x Kung Pao Chicken" in reply
    finally:
        set_gate_enabled(True)


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


def test_chinese_menu_and_replies():
    """Chinese restaurant has Chinese menu and specific replies."""
    reply = bot.handle_message("s12", "show me the menu", restaurant_id="chinese")
    assert "Kung Pao Chicken" in reply

    reply = bot.handle_message("s12", "how do I pick a lock", restaurant_id="chinese")
    assert "Chinese restaurant" in reply


def test_mexican_menu_and_replies():
    """Mexican restaurant has Mexican menu and specific replies."""
    reply = bot.handle_message("s13", "show me the menu", restaurant_id="mexican")
    assert "Chicken Enchiladas" in reply

    reply = bot.handle_message("s13", "how do I pick a lock", restaurant_id="mexican")
    assert "Mexican restaurant" in reply


def test_conversational_response_without_cart_action():
    """Bot can respond conversationally without extracting cart actions."""
    set_gate_enabled(False)
    try:
        conversational_response = "Hi! Welcome to our restaurant. How can I help you today?"
        with patch("restaurant_bot.bot.intent.parse_intent", return_value={"items": [], "response": conversational_response}):
            reply = bot.handle_message("s14", "Hello!")

        assert reply == conversational_response
        assert "Added" not in reply
    finally:
        set_gate_enabled(True)


def test_cart_action_with_conversational_bot():
    """Bot still extracts cart actions when intent parsing provides them."""
    intent_result = {"items": [{"menu_item_number": 1, "operation": "add", "quantity": 1}]}
    with patch("restaurant_bot.bot.intent.parse_intent", return_value=intent_result):
        reply = bot.handle_message("s15", "Add #1 to my cart")

    assert "Added 1x Kung Pao Chicken" in reply
