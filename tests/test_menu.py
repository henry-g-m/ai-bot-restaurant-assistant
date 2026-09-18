from restaurant_bot.menu import load_menu


def test_load_menu():
    menu = load_menu("data/menu.yaml")
    assert len(menu.items) == 3
    coke = menu.find("coke")
    assert coke is not None
    assert coke.price == 2.50
