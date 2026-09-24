"""Restaurant state management for multi-restaurant support."""

from typing import Literal

_active_restaurant: Literal["chinese", "mexican"] = "chinese"


def get_active_restaurant() -> Literal["chinese", "mexican"]:
    """Return the currently active restaurant."""
    global _active_restaurant
    return _active_restaurant


def set_active_restaurant(restaurant: Literal["chinese", "mexican"]) -> None:
    """Set the active restaurant. Validates the input."""
    global _active_restaurant
    if restaurant not in ("chinese", "mexican"):
        raise ValueError(f"Invalid restaurant: {restaurant}. Must be 'chinese' or 'mexican'.")
    _active_restaurant = restaurant
