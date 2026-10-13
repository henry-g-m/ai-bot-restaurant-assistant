import logging
import os
import threading
from typesafe_sdk import Noul, Score, TypeSafeClient, Choice, SystemOneResponse

from restaurant_bot import secrets

logger = logging.getLogger(__name__)

TYPESAFE_MODEL = "jev-latest"
QUESTIONS_NOUL = {
"restaurant_operations": "Is the user asking about restaurant operations, such as hours, location, or menu?",
"menu_request": "Is the user asking to see the menu or the list of available dishes?",
"checkout_request": "Is the user asking to checkout or confirm their order?",
"out_of_scope": "Is the user asking about something unrelated to this restaurant, its food, ordering, delivery, or its operations? Greetings, thanks, and small talk directed at the restaurant are NOT unrelated.",
"item_request": "Is the user asking about a specific menu item, such as its ingredients or price?",
"human_interaction": "Is the user asking to speak with a human or requesting human assistance?",
"delivery_request": "Is the user asking about delivery options, such as delivery time or fees?",
}

#Choices are in no particular order
QUESTIONS_CHOICE ={
    "cart_action": ("Commanding an action like placing an order, canceling, or modifying an order?",
                    {"placing":"Placing an order", "canceling":"Canceling an order", "modifying":"Modifying an order", "adding":"Adding an item to the cart", "removing":"Removing an item from the cart"}),
    "delivery_options": ("Asking about delivery and other options?",
                         {"delivery": "Delivery", "pickup": "Pickup", "dine-in": "Dine-in"}),
    "complaint": ("Is the user expressing dissatisfaction or making a complaint regarding an order or service?",
                  {"order": "Order-related", "service": "Service-related", "billing": "Billing-related", "delivery": "Delivery-related", "pickup": "Pickup-related", "other": "Other"})
}

#Score levels are ordered
QUESTIONS_SCORE = {
    "user_expressiveness": ("How expressive is the user's message?",
                            ["Not expressive: Short sentences, to the point",
                             "Somewhat expressive: More detailed, but not overly verbose",
                             "Very expressive: Extensive and descriptive"
                             ]
                            ),
    "satisfaction_level": ("What is the user's level of satisfaction?",
                           [  "grateful: The user is thankful for the service received",
                              "very satisfied: The user is highly pleased with the service",
                              "satisfied: The user is content with the service",
                              "indifferent: The user has no strong feelings about the service",
                              "frustrated: The user is dissatisfied with the service"
                           ])
}

questions = {
    key: Noul(instructions=question) for key, question in QUESTIONS_NOUL.items()
}
questions2 = {
    key: Choice(instructions=instructions, criteria=choices)
    for key, (instructions, choices) in QUESTIONS_CHOICE.items()
}
questions3 = {
    key: Score(instructions=instructions, criteria=choices) for key, (instructions, choices) in QUESTIONS_SCORE.items()
}

all_questions = {**questions, **questions2, **questions3}

_client = None
_client_lock = threading.Lock()

def _get_client() -> TypeSafeClient:
    """Create the client on first use; the key comes from TYPESAFE_API_KEY (local dev) or Key Vault."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                api_key = os.environ.get("TYPESAFE_API_KEY") or secrets.get_secret("typesafe-api-key")
                _client = TypeSafeClient(api_key=api_key, timeout=10.0)
    return _client

def evaluate_jev(text: str) -> SystemOneResponse:
    response = _get_client().system_one(
        state=text,
        questions=all_questions,
        model=TYPESAFE_MODEL)
    logger.info("JEV response for %r: %s", text, response)
    return response

def route(response: SystemOneResponse) -> str:
    """
    Route the message based on the JEV noul answers.
    """
    nouls = {key: answer.noul for key, answer in response.nouls.items()}
    if nouls["out_of_scope"] > 0.5:
        return "out_of_scope"
    elif nouls["checkout_request"] > 0.5:
        return "checkout_request"
    elif nouls["menu_request"] > 0.5 and nouls["menu_request"] >= nouls["item_request"]:
        return "menu_request"
    else:
        return "in_scope"

def classify(text: str) -> str:
    """
    Evaluate and route the message. Fails open (in_scope) if JEV is unavailable.
    """
    try:
        return route(evaluate_jev(text))
    except Exception:
        logger.exception("JEV evaluation failed")
        return "in_scope"

if __name__ == "__main__":
    response = evaluate_jev("Can you tell me what time the restaurant opens and closes?")
    print({key: response.answers[key].noul for key in QUESTIONS_NOUL})
    print({key: response.answers[key].choice for key in QUESTIONS_CHOICE})
    print({key: response.answers[key].score for key in QUESTIONS_SCORE})
