
JEV

TYPESAFE_API_KEY=

Questions by type
Is the user :
*Noul*
- Asking something related to restaurant operations?
- Asking something related to reservations?
- Is a question related to the menu?
- Something else
- Related to a specific item.
- Asking for a special request or dietary restriction?
- Requesting a modification to a dish?
- Asking for assistance or support from a human?
- Asking about delivery status or tracking? 

  *Score*
-  How expressive is the user in their request?
  [very, somewhat, not very]
-  What's his level of satisfaction in this session so far?
  [grateful, very satisfied, satisfied, indifferent, frustrated, angry]

  *Choice*
- Commanding an action like placing an order, canceling, or modifying an order?
  [placing, adding, canceling, modifying]
- Asking about delivery or pickup options?
  [pickup, delivery, dine-in]
- Complaining about an order or service?
  [order,service,billing,delivery,pickup,other]
- Requesting delivery or pickup for his order?
  [pickup, delivery, dine-in]



Routes
out_of_scope -> reject
restaurant_operations -> RAG operations
menu_request -> RAG menu
item_request -> RAG menu
checkout_request -> checkout action
human_interaction -> human support
delivery_request -> delivery action
  delivery_options -> options for delivery action
cart_action -> cart action
complaint -> handle complaint



