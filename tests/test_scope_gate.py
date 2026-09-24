from restaurant_bot.scope_gate import is_in_scope


def test_in_scope_message():
    assert is_in_scope("I'd like a large pizza") is True
    assert is_in_scope("What sodas do you have?") is True
    assert is_in_scope("Do you deliver?") is True
    assert is_in_scope("How long is the delivery time?") is True
    assert is_in_scope("Can I have the chicken pasta not spicy") is True
    assert is_in_scope("I want the noodles extra hot") is True


def test_out_of_scope_message():
    assert is_in_scope("how do I pick a lock") is False
