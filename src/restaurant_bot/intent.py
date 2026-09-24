import json
import logging

from restaurant_bot import rag, secrets
from restaurant_bot.menu import Menu

logger = logging.getLogger(__name__)

#OpenAI's documented tool/function-calling schema
# Pass the model a description of a function signature;
# the model's only job is to output arguments that match that schema as JSON text.
# It's closer to "fill in this form" than "call this function."
_TOOL = {
    "type": "function",
    "function": {
        "name": "cart_action",
        "description": "Extract the cart changes implied by a restaurant customer's message.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": (
                        "The order changes implied by the message. Leave empty if the message "
                        "isn't about changing the order (e.g. it's a question)."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "menu_item_number": {
                                "type": "integer",
                                "description": "The '#' number of the item from the menu list.",
                            },
                            "operation": {
                                "type": "string",
                                "enum": ["add", "remove", "set_quantity"],
                                "description": (
                                    "'add' adds quantity to the cart (default 1 if omitted). "
                                    "'remove' removes quantity from the cart, or the whole item "
                                    "if quantity is omitted. 'set_quantity' sets the cart line "
                                    "to exactly quantity."
                                ),
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "How many. Required for 'set_quantity'.",
                            },
                        },
                        "required": ["menu_item_number", "operation"],
                    },
                },
            },
            "required": ["items"],
        },
    },
}


def parse_intent(message: str, menu: Menu) -> dict:
    menu_text = "\n".join(f"#{item.number} {item.name}" for item in menu.items)
    system_prompt = (
        "You are extracting a restaurant customer's order changes from their message.\n"
        f"Menu:\n{menu_text}\n"
        "Only match items that are actually on the menu above."
    )

    try:
        response = rag._get_client().chat.completions.create(
            model=secrets.get_secret("azure-openai-deployment"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            tools=[_TOOL],
            #Other options: auto, required (call once or more) or forced function call (call exactly once, the function mentioned in the tool_choice)
            tool_choice={"type": "function", "function": {"name": "cart_action"}},
            temperature=0,
        )
        arguments = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(arguments)
    except Exception:
        logger.exception("Intent parsing failed")
        return {"items": []}
