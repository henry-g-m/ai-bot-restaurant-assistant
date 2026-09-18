from restaurant_bot.scope_gate import is_in_scope


def test_in_scope_message():
    assert is_in_scope("I'd like a large pizza") is True


def test_out_of_scope_message():
    assert is_in_scope("how do I pick a lock") is False
