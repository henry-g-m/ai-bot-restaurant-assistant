"""Tests for restaurant state management (admin.py)."""

import pytest

from restaurant_bot.admin import get_active_restaurant, set_active_restaurant


def test_get_active_restaurant_default():
    """Default active restaurant is Chinese."""
    restaurant = get_active_restaurant()
    assert restaurant == "chinese"


def test_set_active_restaurant():
    """Can set active restaurant to Mexican and get it back."""
    set_active_restaurant("mexican")
    assert get_active_restaurant() == "mexican"
    # Reset to default for other tests
    set_active_restaurant("chinese")


def test_set_active_restaurant_invalid():
    """Setting invalid restaurant raises ValueError."""
    with pytest.raises(ValueError, match="Invalid restaurant"):
        set_active_restaurant("italian")


def test_set_active_restaurant_roundtrip():
    """Restaurant state persists across get/set cycles."""
    set_active_restaurant("mexican")
    assert get_active_restaurant() == "mexican"

    set_active_restaurant("chinese")
    assert get_active_restaurant() == "chinese"

    set_active_restaurant("mexican")
    assert get_active_restaurant() == "mexican"
