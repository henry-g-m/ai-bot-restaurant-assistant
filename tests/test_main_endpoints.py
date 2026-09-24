"""Tests for Phase 2.4 main.py endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from restaurant_bot import main, secrets
from restaurant_bot.admin import set_active_restaurant

client = TestClient(main.app)


def test_chat_uses_active_restaurant_chinese():
    """Chat endpoint uses active restaurant (Chinese by default)."""
    set_active_restaurant("chinese")
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="chinese"):
        with patch("restaurant_bot.main.bot.handle_message", return_value="Here's our menu:"):
            response = client.post("/chat", json={"session_id": "s1", "message": "show menu"})

    assert response.status_code == 200
    assert "reply" in response.json()


def test_chat_uses_active_restaurant_mexican():
    """Chat endpoint uses active restaurant (Mexican when set)."""
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="mexican"):
        with patch("restaurant_bot.main.bot.handle_message", return_value="Bienvenido!"):
            response = client.post("/chat", json={"session_id": "s2", "message": "hola"})

    assert response.status_code == 200
    assert "reply" in response.json()


def test_menu_endpoint_uses_active_restaurant():
    """Menu endpoint returns active restaurant's menu."""
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="chinese"):
        response = client.get("/menu")

    assert response.status_code == 200
    menu = response.json()
    assert len(menu) > 0
    assert all("number" in item and "name" in item and "price" in item for item in menu)


def test_admin_status_endpoint():
    """GET /admin/status returns active restaurant and menu items count."""
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="chinese"):
        response = client.get("/admin/status")

    assert response.status_code == 200
    data = response.json()
    assert data["active_restaurant"] == "chinese"
    assert data["menu_items_count"] > 0


def test_admin_switch_restaurant_requires_password():
    """POST /admin/switch-restaurant requires valid password."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=False):
        response = client.post(
            "/admin/switch-restaurant",
            json={"restaurant": "mexican", "password": "wrong"}
        )

    assert response.status_code == 403


def test_admin_switch_restaurant_with_valid_password():
    """POST /admin/switch-restaurant succeeds with valid password."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=True):
        with patch("restaurant_bot.main.admin.set_active_restaurant"):
            with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="mexican"):
                response = client.post(
                    "/admin/switch-restaurant",
                    json={"restaurant": "mexican", "password": "correct"}
                )

    assert response.status_code == 200
    data = response.json()
    assert data["active_restaurant"] == "mexican"


def test_admin_switch_restaurant_invalid_restaurant():
    """POST /admin/switch-restaurant rejects invalid restaurant."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=True):
        with patch("restaurant_bot.main.admin.set_active_restaurant", side_effect=ValueError("Invalid")):
            response = client.post(
                "/admin/switch-restaurant",
                json={"restaurant": "invalid", "password": "correct"}
            )

    assert response.status_code == 400


def test_documents_endpoint_requires_password():
    """POST /documents requires valid password."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=False):
        response = client.post(
            "/documents",
            data={"password": "wrong", "restaurant_id": "chinese"},
            files={"file": ("test.txt", b"test content")}
        )

    assert response.status_code == 403


def test_documents_endpoint_with_valid_password():
    """POST /documents succeeds with valid password and valid file."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=True):
        with patch("restaurant_bot.main.documents.extract_text", return_value="extracted text"):
            with patch("restaurant_bot.main.documents.chunk_text", return_value=["chunk1", "chunk2"]):
                with patch("restaurant_bot.main.embeddings.embed", return_value=[0.1, 0.2]):
                    with patch("restaurant_bot.main.vector_store.upsert_chunk"):
                        response = client.post(
                            "/documents",
                            data={"password": "correct", "restaurant_id": "chinese"},
                            files={"file": ("test.txt", b"test content")}
                        )

    assert response.status_code == 200
    data = response.json()
    assert "chunk_count" in data
    assert data["chunk_count"] == 2


def test_documents_endpoint_invalid_file():
    """POST /documents rejects invalid files."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=True):
        with patch("restaurant_bot.main.documents.extract_text", side_effect=ValueError("Invalid file")):
            response = client.post(
                "/documents",
                data={"password": "correct", "restaurant_id": "chinese"},
                files={"file": ("test.xyz", b"invalid")}
            )

    assert response.status_code == 400


def test_menu_endpoint_differs_by_restaurant():
    """Menu endpoint returns different items for Chinese vs Mexican."""
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="chinese"):
        chinese_response = client.get("/menu")

    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="mexican"):
        mexican_response = client.get("/menu")

    assert chinese_response.status_code == 200
    assert mexican_response.status_code == 200

    chinese_menu = chinese_response.json()
    mexican_menu = mexican_response.json()

    # Check that menus have different items
    chinese_names = {item["name"] for item in chinese_menu}
    mexican_names = {item["name"] for item in mexican_menu}

    assert chinese_names != mexican_names
    assert len(chinese_menu) > 0
    assert len(mexican_menu) > 0


def test_chat_bot_responds_differently_per_restaurant():
    """Bot gives different responses based on active restaurant."""
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="chinese"):
        with patch("restaurant_bot.main.bot.handle_message", return_value="Welcome to our Chinese restaurant!"):
            response1 = client.post("/chat", json={"session_id": "s1", "message": "hello"})

    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="mexican"):
        with patch("restaurant_bot.main.bot.handle_message", return_value="Welcome to our Mexican restaurant!"):
            response2 = client.post("/chat", json={"session_id": "s1", "message": "hello"})

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert "Chinese" in response1.json()["reply"]
    assert "Mexican" in response2.json()["reply"]


def test_admin_status_reflects_active_restaurant():
    """Admin status shows the currently active restaurant."""
    with patch("restaurant_bot.main.admin.get_active_restaurant", return_value="mexican"):
        response = client.get("/admin/status")

    assert response.status_code == 200
    data = response.json()
    assert data["active_restaurant"] == "mexican"


def test_documents_upload_with_restaurant_id():
    """POST /documents correctly associates uploads with restaurant."""
    with patch("restaurant_bot.main._verify_admin_password", return_value=True):
        with patch("restaurant_bot.main.documents.extract_text", return_value="content"):
            with patch("restaurant_bot.main.documents.chunk_text", return_value=["chunk"]):
                with patch("restaurant_bot.main.embeddings.embed", return_value=[0.1]):
                    with patch("restaurant_bot.main.vector_store.upsert_chunk") as mock_upsert:
                        response = client.post(
                            "/documents",
                            data={"password": "correct", "restaurant_id": "mexican"},
                            files={"file": ("doc.txt", b"content")}
                        )

    assert response.status_code == 200
    # Verify upsert was called with correct restaurant_id
    assert mock_upsert.called
    call_kwargs = mock_upsert.call_args[1]
    assert call_kwargs["restaurant_id"] == "mexican"
