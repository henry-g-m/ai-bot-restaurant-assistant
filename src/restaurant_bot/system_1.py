import os
from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient, NoulAnswer, Choice

TYPESAFE_MODEL = "jev-latest"
QUESTIONS_NOUL = {
"restaurant_operations": "Is the user asking about restaurant operations, such as hours, location, or menu?",
"menu_request": "Is the user asking for the menu or specific items on the menu?",
"checkout_request": "Is the user asking to checkout or confirm their order?",
"out_of_scope": "Is the user asking about something unrelated to ordering food from this restaurant?",
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

client = TypeSafeClient(
    api_key=os.environ.get("TYPESAFE_API_KEY", "cache-only"),  # keyless kernels replay the cache
    timeout=120.0
)

def evaluate(text: str) -> dict:
    response = client.system_one(
        state=text,
        questions=all_questions,
        model=TYPESAFE_MODEL)
    return response

def route(nouls: dict[str, float], severity: float ) -> str:
    """
    Route the message based on the nouls and severity.
    """
    if severity > 0.7:
        return "out_of_scope"
    elif nouls.get("menu_request", 0) > 0.5:
        return "menu_request"
    elif nouls.get("checkout_request", 0) > 0.5:
        return "checkout_request"
    else:
        return "in_scope"

#Test
response = evaluate("Can you tell me what time the restaurant opens and closes?")
print(response)
print({key: response.answers[key].noul for key in QUESTIONS_NOUL})