// Admin panel functionality

const currentRestaurantEl = document.getElementById("current-restaurant");
const menuCountEl = document.getElementById("menu-count");
const restaurantSelectSwitch = document.getElementById("restaurant-select");
const adminPasswordSwitch = document.getElementById("admin-password-switch");
const switchButton = document.getElementById("switch-button");
const switchMessageEl = document.getElementById("switch-message");

const fileInput = document.getElementById("file-input");
const fileNameEl = document.getElementById("file-name");
const restaurantSelectUpload = document.getElementById("restaurant-select-upload");
const adminPasswordUpload = document.getElementById("admin-password-upload");
const uploadButton = document.getElementById("upload-button");
const uploadMessageEl = document.getElementById("upload-message");

let selectedFile = null;

// Initialize
async function init() {
  await loadStatus();
  setupRestaurantSwitch();
  setupFileUpload();
  setupUploadForm();
}

// Load and display current status
async function loadStatus() {
  try {
    const response = await fetch("/admin/status");
    const data = await response.json();
    const restaurantName = data.active_restaurant.charAt(0).toUpperCase() + data.active_restaurant.slice(1);
    currentRestaurantEl.textContent = restaurantName;
    menuCountEl.textContent = data.menu_items_count;
    restaurantSelectSwitch.value = data.active_restaurant;
  } catch (error) {
    console.error("Failed to load status:", error);
    currentRestaurantEl.textContent = "Error loading status";
    menuCountEl.textContent = "—";
  }
}

// Restaurant switcher
function setupRestaurantSwitch() {
  switchButton.addEventListener("click", async () => {
    const restaurant = restaurantSelectSwitch.value;
    const password = adminPasswordSwitch.value.trim();

    if (!password) {
      showMessage(switchMessageEl, "Please enter admin password", "error");
      return;
    }

    showMessage(switchMessageEl, "Switching restaurant...", "loading");
    switchButton.disabled = true;

    try {
      const response = await fetch("/admin/switch-restaurant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ restaurant, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to switch restaurant");
      }

      const data = await response.json();
      const restaurantName = data.active_restaurant.charAt(0).toUpperCase() + data.active_restaurant.slice(1);
      currentRestaurantEl.textContent = restaurantName;
      menuCountEl.textContent = data.menu_items_count;
      adminPasswordSwitch.value = "";
      showMessage(switchMessageEl, `✓ Switched to ${restaurantName}`, "success");
    } catch (error) {
      console.error("Switch error:", error);
      showMessage(switchMessageEl, `✗ ${error.message}`, "error");
    } finally {
      switchButton.disabled = false;
    }
  });
}

// File upload handling
function setupFileUpload() {
  fileInput.addEventListener("change", (e) => {
    selectedFile = e.target.files[0];
    if (selectedFile) {
      fileNameEl.textContent = `Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
      uploadButton.disabled = false;
    } else {
      fileNameEl.textContent = "";
      uploadButton.disabled = true;
    }
  });

  // Drag and drop
  const fileInputLabel = document.querySelector(".file-input-label");
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    fileInputLabel.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    fileInputLabel.addEventListener(eventName, () => {
      fileInputLabel.style.background = "#e8f4f8";
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    fileInputLabel.addEventListener(eventName, () => {
      fileInputLabel.style.background = "#f9f9f9";
    });
  });

  fileInputLabel.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      const changeEvent = new Event("change", { bubbles: true });
      fileInput.dispatchEvent(changeEvent);
    }
  });
}

// Upload form
function setupUploadForm() {
  uploadButton.addEventListener("click", async () => {
    if (!selectedFile) {
      showMessage(uploadMessageEl, "Please select a file", "error");
      return;
    }

    const password = adminPasswordUpload.value.trim();
    if (!password) {
      showMessage(uploadMessageEl, "Please enter admin password", "error");
      return;
    }

    showMessage(uploadMessageEl, "Uploading document...", "loading");
    uploadButton.disabled = true;

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("password", password);
      formData.append("restaurant_id", restaurantSelectUpload.value);

      const response = await fetch("/documents", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
      selectedFile = null;
      fileInput.value = "";
      fileNameEl.textContent = "";
      adminPasswordUpload.value = "";
      showMessage(uploadMessageEl, `✓ Uploaded ${data.chunk_count} chunks from ${data.message}`, "success");
    } catch (error) {
      console.error("Upload error:", error);
      showMessage(uploadMessageEl, `✗ ${error.message}`, "error");
    } finally {
      uploadButton.disabled = selectedFile ? false : true;
    }
  });
}

// Helper to show messages
function showMessage(element, text, type) {
  element.className = `message ${type}`;
  element.textContent = text;
}

// Start
init();
