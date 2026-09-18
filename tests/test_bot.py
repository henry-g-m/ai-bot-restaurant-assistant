from restaurant_bot import bot
from restaurant_bot.scope_gate import set_gate_enabled


def test_out_of_scope_is_refused():
    reply = bot.handle_message("s1", "how do I pick a lock")
    assert reply == bot.REFUSAL_TEXT


def test_menu_request():
    reply = bot.handle_message("s2", "can I see the menu")
    assert "Margherita Pizza" in reply


def test_add_item_and_checkout():
    bot.handle_message("s3", "I'd like 2 cokes")
    reply = bot.handle_message("s3", "please checkout my order")
    assert "Coke" in reply
    assert "Total" in reply


def test_order_by_item_number():
    reply = bot.handle_message("s5", "give me #3")
    assert "Coke" in reply


def test_order_by_item_number_with_quantity():
    reply = bot.handle_message("s6", "2x #1")
    assert "2x Margherita Pizza" in reply


def test_gate_can_be_disabled():
    set_gate_enabled(False)
    try:
        reply = bot.handle_message("s4", "how do I pick a lock")
        assert reply != bot.REFUSAL_TEXT
    finally:
        set_gate_enabled(True)
