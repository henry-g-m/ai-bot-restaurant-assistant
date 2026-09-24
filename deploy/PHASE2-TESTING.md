# Phase 2 Manual Testing Checklist

Complete this checklist before deploying Phase 2 to Azure.

## Setup
- [ ] Install dev dependencies: `pip install -e ".[dev]"`
- [ ] Start dev server: `uvicorn restaurant_bot.main:app --reload`
- [ ] Open browser to `http://localhost:8000/`
- [ ] Verify app loads without errors
- [ ] Check console for Key Vault connection warnings

## Customer Chat UI (index.html)

### Header & Navigation
- [ ] Header displays "Chinese Restaurant" (or current active restaurant)
- [ ] Header shows menu item count (e.g., "10 items on menu")
- [ ] Navigation tabs are visible and clickable
- [ ] Tab content changes when clicking different tabs (About, Menu, Hours, etc.)
- [ ] Chat panel on right side stays visible at all times

### Chat Functionality
- [ ] Send message: "show menu" displays Chinese menu items
- [ ] Message appears in chat log with "You:" prefix
- [ ] Bot response appears with "Bot:" prefix
- [ ] Chat auto-scrolls to latest message
- [ ] Input field clears after sending message

### Menu & Ordering
- [ ] Type "#1" → bot confirms adding item #1
- [ ] Cart displays item name, quantity, and total price
- [ ] Type "checkout" → bot shows order confirmation and clears cart
- [ ] Type "remove [item]" → bot removes item from cart

### Tab Switching
- [ ] Click each tab (About, Menu, Hours, Contact, Reservations, Reviews)
- [ ] Tab content updates correctly
- [ ] Chat remains visible and functional

### Mobile/Responsive
- [ ] Resize browser to mobile width (< 600px)
- [ ] Layout stacks vertically
- [ ] Chat and content remain usable

---

## Admin Panel (admin.html)

### Setup
- [ ] Click "System Admin?" in chat footer
- [ ] Navigate to `http://localhost:8000/admin.html`
- [ ] Admin panel loads without errors
- [ ] Current restaurant displays as "Chinese"
- [ ] Menu count displays correctly

### Restaurant Switcher
- [ ] Try switching to "Mexican" with wrong password
  - [ ] Error message appears: "Invalid password" or similar
- [ ] Switch to "Mexican" with correct password (set via Key Vault)
  - [ ] Status updates to "Mexican Restaurant"
  - [ ] Menu count updates
- [ ] Switch back to "Chinese"
  - [ ] Status updates to "Chinese Restaurant"

### Document Upload
- [ ] Create test.txt file with restaurant description
- [ ] Drag file onto upload area
  - [ ] File name displays below upload button
  - [ ] Upload button becomes enabled
- [ ] Try uploading with wrong password
  - [ ] Error message appears
- [ ] Upload with correct password
  - [ ] Success message shows number of chunks uploaded (e.g., "Uploaded 2 chunks")
- [ ] Upload file as "Shared" restaurant
  - [ ] Should be accessible from both Chinese and Mexican chats

---

## Multi-Restaurant Features

### Restaurant Switching (Integration)
- [ ] Switch to Mexican via admin panel
- [ ] Go back to chat
  - [ ] Header should show "Mexican Restaurant"
  - [ ] Menu should show Mexican items (#1 = Chicken Enchiladas, etc.)
- [ ] Type "show menu" in chat
  - [ ] Displays Mexican menu
- [ ] Type "help" (out-of-scope message)
  - [ ] Bot responds with "Mexican restaurant" variant (if personality enabled)
- [ ] Checkout → cart clears
- [ ] Switch back to Chinese
  - [ ] Menu and bot replies change back

### Document Segregation
- [ ] Upload doc1.txt as "Chinese Only" restaurant
- [ ] Upload doc2.txt as "Mexican Only" restaurant
- [ ] Upload doc3.txt as "Shared" restaurant
- [ ] Chat in Chinese restaurant
  - [ ] RAG answers should use doc1 + doc3 (not doc2)
- [ ] Chat in Mexican restaurant
  - [ ] RAG answers should use doc2 + doc3 (not doc1)

---

## Bot Personality (If Enabled)

### Chinese Restaurant
- [ ] Type natural question (e.g., "What do you recommend?")
- [ ] Bot responds with Chinese accent/imperfect English
- [ ] Responses are short and relevant to Chinese cuisine

### Mexican Restaurant
- [ ] Switch to Mexican restaurant
- [ ] Type natural question
- [ ] Bot responds with Mexican/Spanish accent, enthusiastic tone
- [ ] Occasional Spanish words or phrases
- [ ] Responses are short and relevant to Mexican cuisine

---

## Error Handling

### Invalid Inputs
- [ ] Type out-of-scope question (e.g., "How do I hack a website?")
  - [ ] Bot refuses if scope gate is enabled
  - [ ] Response mentions restaurant only
- [ ] Type gibberish / random text
  - [ ] Bot responds with help text (not an error)

### Missing/Invalid Data
- [ ] Try ordering invalid item number (e.g., "#99")
  - [ ] Bot responds with help text
- [ ] Admin: Try uploading unsupported file type (.exe, .zip)
  - [ ] Error message displayed (invalid file)

---

## Performance & Reliability

### Load Times
- [ ] First chat message takes < 5 seconds (scope gate warmup)
- [ ] Subsequent messages take < 2 seconds
- [ ] Menu loads instantly
- [ ] Admin panel loads instantly

### State Persistence
- [ ] Add items to cart (e.g., 2x #1, 1x #3)
- [ ] Refresh page
  - [ ] Cart is cleared (session is reset, expected)
  - [ ] Reconnect with same session_id → cart restored
- [ ] Switch restaurants → cart is cleared (expected)

### Concurrent Requests
- [ ] Open chat in two browser tabs with different session_ids
- [ ] Send messages in both simultaneously
  - [ ] Both receive correct responses
  - [ ] Carts don't interfere with each other

---

## API Verification (curl/Postman)

### GET /menu
```bash
curl http://localhost:8000/menu
# Should return Chinese menu by default
```

### GET /admin/status
```bash
curl http://localhost:8000/admin/status
# Should return {"active_restaurant": "chinese", "menu_items_count": 10}
```

### POST /admin/switch-restaurant
```bash
curl -X POST http://localhost:8000/admin/switch-restaurant \
  -H "Content-Type: application/json" \
  -d '{"restaurant": "mexican", "password": "<password>"}'
# Should return {"active_restaurant": "mexican", "menu_items_count": 10}
```

### POST /chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session", "message": "show menu"}'
# Should return chat response with menu
```

### POST /documents
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@test.txt" \
  -F "password=<password>" \
  -F "restaurant_id=chinese"
# Should return {"chunk_count": N, "message": "Uploaded..."}
```

---

## Test Results Summary

- [ ] All 68 unit tests pass: `pytest tests/ -q`
- [ ] No Python errors or warnings in console
- [ ] All endpoints respond with correct status codes
- [ ] Database connections work (if using real Cosmos DB)
- [ ] File uploads process correctly

---

## Sign-Off

- [ ] Tester Name: ___________________
- [ ] Date: ___________________
- [ ] All checks passed: [ ] Yes [ ] No
- [ ] Issues found: (describe below)

```
[Issues or notes]
```
