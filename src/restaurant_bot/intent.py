import json
import logging
from typing import Literal

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


def parse_intent(message: str, menu: Menu, restaurant_id: Literal["chinese", "mexican"] = "chinese") -> dict:
    menu_text = "\n".join(f"#{item.number} {item.name}" for item in menu.items)

    # Use personality-based system prompt from rag module
    personality_prompt = rag._RESTAURANT_PERSONALITIES.get(
        restaurant_id,
        "You are extracting a customer's order changes from their message."
    )

    system_prompt = (
        f"{personality_prompt}\n\n"
        f"Menu:\n{menu_text}\n\n"
        "INSTRUCTIONS:\n"
        "- If the message contains order instructions (add/remove/change items), extract cart changes using the cart_action tool.\n"
        "- If the message is a greeting, question, or conversation (no cart changes), respond naturally WITHOUT using the tool.\n"
        "- Only match items that are actually on the menu."
    )

    try:
        response = rag._get_client().chat.completions.create(
            model=secrets.get_secret("azure-openai-deployment"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            tools=[_TOOL],
            tool_choice="auto",  # Let LLM decide: extract actions or respond conversationally
            temperature=0.1,  # Slightly higher for more natural conversation
        )

        # Check if the LLM called the cart_action tool
        if response.choices[0].message.tool_calls:
            # Extract cart actions
            arguments = response.choices[0].message.tool_calls[0].function.arguments
            return json.loads(arguments)
        else:
            # LLM chose not to use tool - return empty with response flag
            return {"items": [], "response": response.choices[0].message.content}
    except Exception:
        logger.exception("Intent parsing failed")
        return {"items": []}
