# JEV Sample Conversations

Sample user messages for exercising every JEV question defined in
`src/restaurant_bot/system_1.py` (Noul, Choice, and Score), including every
option of each Choice and Score question.

The "Expected" columns describe what each message is designed to trigger;
they are not recorded JEV outputs.

## Notes

- JEV evaluates each message on its own (`state=text`), not the conversation
  history. Satisfaction is therefore per message, not per session.
- Only `out_of_scope`, `checkout_request`, and `menu_request` (when it beats
  `item_request`) change the route. Every other question routes to `in_scope`;
  check the `JEV response for ...` log lines to see the full scores.
- Route priority: `out_of_scope` > `checkout_request` > `menu_request` > `in_scope`.

## 1. Ordering from start to finish (Chinese)

| # | User message | Expected JEV result | Route |
|---|---|---|---|
| 1 | "Hi! What's on the menu?" | `menu_request`, expressiveness: not expressive | menu_request |
| 2 | "Is the Mapo Tofu spicy? Does it have pork in it?" | `item_request` higher than `menu_request` | in_scope |
| 3 | "Add 2 Kung Pao Chicken and an order of spring rolls" | cart_action = **adding** | in_scope |
| 4 | "Actually, take the spring rolls off" | cart_action = **removing** | in_scope |
| 5 | "Make it 3 Kung Pao instead of 2" | cart_action = **modifying** | in_scope |
| 6 | "That's everything, I'd like to place my order and check out" | `checkout_request`, cart_action = **placing** | checkout_request |
| 7 | "Thank you so much, you made dinner so easy tonight!" | satisfaction = **grateful**; `out_of_scope` should stay low | in_scope |

## 2. Hours, location and delivery (Mexican)

| # | User message | Expected JEV result |
|---|---|---|
| 1 | "What time do you close on Sundays?" | `restaurant_operations` |
| 2 | "Where are you located?" | `restaurant_operations` |
| 3 | "Do you deliver to my area? How much is the delivery fee?" | `delivery_request`, delivery_options = **delivery** |
| 4 | "How long does delivery usually take?" | `delivery_request` |
| 5 | "Can I just pick it up myself instead?" | delivery_options = **pickup** |
| 6 | "Actually, can we eat there? Do you take walk-ins?" | delivery_options = **dine-in** |

## 3. Complaints and asking for a person

| # | User message | Expected JEV result |
|---|---|---|
| 1 | "My order came without the guacamole I paid for." | complaint = **order**, satisfaction = **frustrated** |
| 2 | "The driver showed up 45 minutes late and everything was cold." | complaint = **delivery** |
| 3 | "I was charged twice for the same order." | complaint = **billing** |
| 4 | "I waited 20 minutes at the counter even though the app said my order was ready." | complaint = **pickup** |
| 5 | "The person who answered the phone was rude and hung up on me." | complaint = **service** |
| 6 | "Your website keeps crashing on my phone." | complaint = **other** |
| 7 | "I want to talk to a real person." | `human_interaction` |
| 8 | "Just cancel my order." | cart_action = **canceling** |

## 4. Out-of-scope messages (scope gate on)

| # | User message | Expected JEV result | Route |
|---|---|---|---|
| 1 | "What's the capital of Australia?" | `out_of_scope` | refusal |
| 2 | "Can you help me write a Python script?" | `out_of_scope` | refusal |
| 3 | "Hello! How are you today?" | should **not** be `out_of_scope` (greetings are exempt) | in_scope |
| 4 | "Thanks!" | should **not** be `out_of_scope` | in_scope |
| 5 | "Check me out, and also who won the game last night?" | `out_of_scope` and `checkout_request` both high; `out_of_scope` is checked first and wins | refusal |

## 5. Expressiveness and satisfaction levels

| Score | Level | User message |
|---|---|---|
| user_expressiveness | Not expressive | "menu" |
| | Somewhat expressive | "Could I get the chicken enchiladas with a side of chips and guac? Thanks." |
| | Very expressive | "So my family is coming over tonight, and we've been craving Mexican all week. My kids love cheese quesadillas, my husband always gets carne asada, and I'd love something vegetarian, maybe the veggie burrito? Oh, and churros for dessert, definitely churros!" |
| satisfaction_level | grateful | "Thank you so much for fixing my order, I really appreciate it!" |
| | very satisfied | "Honestly the best carne asada I've had in years!" |
| | satisfied | "The food was good, thanks." |
| | indifferent | "ok." |
| | frustrated | "This is the third time my order has been wrong." |

## Edge cases worth watching

- Section 1, message 2: `item_request` vs `menu_request` tie-break.
- Section 1, message 7: thanks / small talk must not trip `out_of_scope`.
- Section 4, message 5: `out_of_scope` takes priority over `checkout_request`.
