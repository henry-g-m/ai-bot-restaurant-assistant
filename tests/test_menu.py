from restaurant_bot.menu import get_menu_by_restaurant, load_menu


def test_load_menu():
    menu = load_menu("data/menu.yaml")
    assert len(menu.items) == 3
    coke = menu.find("coke")
    assert coke is not None
    assert coke.price == 2.50


def test_get_menu_by_restaurant_chinese():
    """Load Chinese restaurant menu."""
    menu = get_menu_by_restaurant("chinese")
    assert len(menu.items) == 10
    kung_pao = menu.find("kung pao")
    assert kung_pao is not None
    assert kung_pao.name == "Kung Pao Chicken"
    assert kung_pao.price == 10.50


def test_get_menu_by_restaurant_mexican():
    """Load Mexican restaurant menu."""
    menu = get_menu_by_restaurant("mexican")
    assert len(menu.items) == 10
    tacos = menu.find("tacos")
    assert tacos is not None
    assert tacos.name == "Beef Tacos (3 pcs)"
    assert tacos.price == 10.50


def test_get_menu_by_restaurant_caching():
    """Menu cache returns same object on repeated calls."""
    menu1 = get_menu_by_restaurant("chinese")
    menu2 = get_menu_by_restaurant("chinese")
    assert menu1 is menu2


def test_get_menu_by_restaurant_separate_caches():
    """Chinese and Mexican menus are cached separately."""
    chinese = get_menu_by_restaurant("chinese")
    mexican = get_menu_by_restaurant("mexican")
    assert chinese is not mexican
    assert len(chinese.items) == len(mexican.items) == 10


def test_get_menu_by_restaurant_find_by_number():
    """Can find items by number in both restaurant menus."""
    chinese = get_menu_by_restaurant("chinese")
    mexican = get_menu_by_restaurant("mexican")

    # First items are #1
    assert chinese.find_by_number(1).name == "Kung Pao Chicken"
    assert mexican.find_by_number(1).name == "Chicken Enchiladas"
