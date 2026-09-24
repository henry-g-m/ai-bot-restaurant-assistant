const sessionId = crypto.randomUUID();
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const cartEl = document.getElementById("cart");
const restaurantNameEl = document.getElementById("restaurant-name");
const restaurantStatusEl = document.getElementById("restaurant-status");
const adminLink = document.getElementById("admin-link");

let currentRestaurant = "chinese";

// Initialize
async function init() {
  await loadRestaurantInfo();
  setupTabNavigation();
  setupAdminLink();
  setupChatForm();
}

// Load restaurant info from /admin/status
async function loadRestaurantInfo() {
  try {
    const response = await fetch("/admin/status");
    const data = await response.json();
    currentRestaurant = data.active_restaurant;
    const restaurantName = data.active_restaurant.charAt(0).toUpperCase() + data.active_restaurant.slice(1);
    restaurantNameEl.textContent = restaurantName + " Restaurant";
    restaurantStatusEl.textContent = `${data.menu_items_count} items on menu`;
  } catch (error) {
    console.error("Failed to load restaurant info:", error);
    restaurantStatusEl.textContent = "Unable to load restaurant info";
  }
}

// Tab navigation
function setupTabNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      // Remove active class from all tabs and content
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((content) => {
        content.classList.remove("active");
      });

      // Add active class to clicked tab and corresponding content
      tab.classList.add("active");
      const tabName = tab.getAttribute("data-tab");
      const content = document.getElementById(tabName);
      if (content) {
        content.classList.add("active");
      }
    });
  });
}

// Chat form handling
function setupChatForm() {
  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;
    appendMessage("msg-user", `You: ${message}`);
    chatInput.value = "";

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message }),
      });
      const data = await response.json();
      appendMessage("msg-bot", `Bot: ${data.reply}`);
      renderCart(data.cart, data.total);
    } catch (error) {
      console.error("Chat error:", error);
      appendMessage("msg-bot", "Bot: Sorry, I'm having trouble connecting.");
    }
  });
}

function appendMessage(className, text) {
  const div = document.createElement("div");
  div.className = className;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function renderCart(cart, total) {
  if (!cart.length) {
    cartEl.innerHTML = "<h3>🛒 Cart</h3><p>Your cart is empty.</p>";
    return;
  }
  const lines = cart.map((line) => `${line.quantity}x ${line.name}`);
  const listHtml = lines.map((line) => `<li>${line}</li>`).join("");
  cartEl.innerHTML = `
    <h3>🛒 Cart</h3>
    <ul id="cart-list">${listHtml}</ul>
    <div id="cart-total">Total: $${total.toFixed(2)}</div>
  `;
}

// Admin link
function setupAdminLink() {
  adminLink.addEventListener("click", (e) => {
    e.preventDefault();
    window.location.href = "/admin.html";
  });
}

// Start
init();
renderCart([], 0);
