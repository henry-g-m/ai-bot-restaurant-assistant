const sessionId = crypto.randomUUID();
const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const cartEl = document.getElementById("cart");

function appendMessage(className, text) {
  const div = document.createElement("div");
  div.className = className;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function renderCart(cart, total) {
  if (!cart.length) {
    cartEl.textContent = "Cart: empty";
    return;
  }
  const lines = cart.map((line) => `${line.quantity}x ${line.name}`);
  cartEl.textContent = `Cart: ${lines.join(", ")} — Total: $${total.toFixed(2)}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  appendMessage("msg-user", `You: ${message}`);
  input.value = "";

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  const data = await response.json();
  appendMessage("msg-bot", `Bot: ${data.reply}`);
  renderCart(data.cart, data.total);
});

renderCart([], 0);
