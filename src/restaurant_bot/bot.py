import re

from restaurant_bot import intent, rag
from restaurant_bot.config import MENU_PATH
from restaurant_bot.menu import load_menu
from restaurant_bot.order import get_or_create_cart
from restaurant_bot.scope_gate import is_gate_enabled, is_in_scope

REFUSAL_TEXT = "I can only help with ordering food from this restaurant."
HELP_TEXT = "Sorry, I didn't understand that. Try asking for the menu, an item, or to checkout."

_menu = None


def _get_menu():
    global _menu
    if _menu is None:
        _menu = load_menu(MENU_PATH)
    return _menu


def _format_menu() -> str:
    menu = _get_menu()
    lines = [f"#{item.number}. {item.name}: ${item.price:.2f}" for item in menu.items]
    return "Here's our menu:\n" + "\n".join(lines)


def _format_checkout(cart) -> str:
    if not cart.items:
        return "Your cart is empty."
    lines = [f"- {line.quantity}x {line.name}: ${line.unit_price * line.quantity:.2f}" for line in cart.items]
    total = cart.total()
    summary = "Order confirmed:\n" + "\n".join(lines) + f"\nTotal: ${total:.2f}"
    cart.clear()
    return summary


def handle_message(session_id: str, message: str) -> str:
    cart = get_or_create_cart(session_id)
    lowered = message.lower()
    if "menu" in lowered:
        return _format_menu()
    if "checkout" in lowered or "confirm" in lowered:
        return _format_checkout(cart)
    if is_gate_enabled() and not is_in_scope(message):
        return REFUSAL_TEXT


    menu = _get_menu()

    hash_match = re.search(r"#(\d+)", lowered)
    if hash_match:
        item = menu.find_by_number(int(hash_match.group(1)))
        if item is not None:
            qty_match = re.search(r"(\d+)\s*x?\s*#\d+", lowered)
            quantity = int(qty_match.group(1)) if qty_match else 1
            cart.add(item.name, item.price, quantity)
            return f"Added {quantity}x {item.name} to your cart."
        return HELP_TEXT

    #Quick match didn't work, try parsing the intent
    result = intent.parse_intent(message, menu)
    changes = []
    for entry in result.get("items", []):
        item = menu.find_by_number(entry.get("menu_item_number"))
        if item is None:
            continue
        operation = entry.get("operation")
        quantity = entry.get("quantity")

        if operation == "add":
            quantity = quantity or 1
            cart.add(item.name, item.price, quantity)
            changes.append(f"Added {quantity}x {item.name}")
        elif operation == "remove":
            if quantity is None:
                quantity = next((line.quantity for line in cart.items if line.name == item.name), 0)
            if quantity > 0:
                cart.remove(item.name, quantity)
                changes.append(f"Removed {quantity}x {item.name}")
        elif operation == "set_quantity" and quantity is not None:
            cart.set_quantity(item.name, item.price, quantity)
            changes.append(f"Set {item.name} to {quantity}x")

    if changes:
        return ", ".join(changes) + "."

    answer = rag.answer_question(message)
    if answer is not None:
        return answer

    return HELP_TEXT
