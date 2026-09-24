from dataclasses import dataclass
from typing import Literal

import yaml


@dataclass
class MenuItem:
    number: int
    name: str
    price: float


class Menu:
    def __init__(self, items: list[MenuItem]):
        self.items = items

    def find(self, fragment: str) -> MenuItem | None:
        fragment = fragment.lower()
        for item in self.items:
            if fragment in item.name.lower():
                return item
        return None

    def find_by_number(self, number: int) -> MenuItem | None:
        for item in self.items:
            if item.number == number:
                return item
        return None


def load_menu(path: str) -> Menu:
    with open(path) as f:
        data = yaml.safe_load(f)
    items = [MenuItem(number=i["number"], name=i["name"], price=i["price"]) for i in data["items"]]
    return Menu(items)


_menu_cache: dict[str, Menu] = {}


def get_menu_by_restaurant(restaurant: Literal["chinese", "mexican"]) -> Menu:
    """Load and cache menu for a given restaurant."""
    if restaurant not in _menu_cache:
        from restaurant_bot.config import MENU_CHINESE_PATH, MENU_MEXICAN_PATH

        path = MENU_CHINESE_PATH if restaurant == "chinese" else MENU_MEXICAN_PATH
        _menu_cache[restaurant] = load_menu(path)
    return _menu_cache[restaurant]
