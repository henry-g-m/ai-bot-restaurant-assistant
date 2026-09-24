from restaurant_bot.order import Cart, get_or_create_cart


def test_add_and_total():
    cart = Cart()
    cart.add("Coke", 2.50, 2)
    cart.add("Margherita Pizza", 9.50, 1)
    assert cart.total() == 14.50
    assert len(cart.as_list()) == 2


def test_checkout_clears_cart():
    cart = Cart()
    cart.add("Coke", 2.50, 1)
    cart.clear()
    assert cart.total() == 0
    assert cart.as_list() == []


def test_set_quantity_updates_existing_line():
    cart = Cart()
    cart.add("Coke", 2.50, 1)
    cart.set_quantity("Coke", 2.50, 3)
    assert cart.as_list() == [{"name": "Coke", "unit_price": 2.50, "quantity": 3}]


def test_set_quantity_adds_new_line_when_absent():
    cart = Cart()
    cart.set_quantity("Coke", 2.50, 2)
    assert cart.as_list() == [{"name": "Coke", "unit_price": 2.50, "quantity": 2}]


def test_set_quantity_zero_removes_line():
    cart = Cart()
    cart.add("Coke", 2.50, 1)
    cart.set_quantity("Coke", 2.50, 0)
    assert cart.as_list() == []


def test_get_or_create_cart_returns_same_instance():
    cart1 = get_or_create_cart("session-a")
    cart1.add("Coke", 2.50, 1)
    cart2 = get_or_create_cart("session-a")
    assert cart2.total() == 2.50
