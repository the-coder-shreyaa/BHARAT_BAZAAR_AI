"""
Tests for the order service and API endpoints.
"""


def _create_full_cart(client, session_id="test-session-order"):
    """Helper: create cart, add an item, return cart_id and product_id."""
    cart_resp = client.post("/api/v1/tools/cart", json={"session_id": session_id})
    cart_id = cart_resp.json()["data"]["cart_id"]

    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product_id = search_resp.json()["data"]["products"][0]["product_id"]

    client.post(
        f"/api/v1/tools/cart/{cart_id}/items",
        json={"product_id": product_id, "quantity": 1},
    )
    return cart_id, product_id


def test_create_order(client):
    """Creating an order from a cart works correctly."""
    session_id = "test-session-order-create"
    cart_id, _ = _create_full_cart(client, session_id)

    resp = client.post(
        "/api/v1/tools/orders",
        json={"cart_id": cart_id, "session_id": session_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "order_id" in data["data"]
    assert data["data"]["status"] == "pending"
    assert data["data"]["total_amount"] > 0


def test_duplicate_order_prevention(client):
    """Creating two orders from the same cart is prevented."""
    session_id = "test-session-dup-order"
    cart_id, _ = _create_full_cart(client, session_id)

    # First order
    resp1 = client.post("/api/v1/tools/orders", json={"cart_id": cart_id, "session_id": session_id})
    assert resp1.json()["success"] is True

    # Second order — should fail
    resp2 = client.post("/api/v1/tools/orders", json={"cart_id": cart_id, "session_id": session_id})
    assert resp2.json()["success"] is False
    assert "duplicate" in resp2.json()["error"].lower() or "already exists" in resp2.json()["error"].lower()


def test_get_order_status(client):
    """Getting order status by ID works correctly."""
    session_id = "test-session-order-status"
    cart_id, _ = _create_full_cart(client, session_id)

    order_resp = client.post("/api/v1/tools/orders", json={"cart_id": cart_id, "session_id": session_id})
    order_id = order_resp.json()["data"]["order_id"]

    resp = client.get(f"/api/v1/tools/orders/{order_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["order_id"] == order_id


def test_get_order_invalid(client):
    """Getting a non-existent order returns error."""
    resp = client.get("/api/v1/tools/orders/nonexistent_order")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False


def test_order_from_empty_cart(client):
    """Creating an order from an empty cart fails."""
    session_id = "test-session-empty-cart"
    cart_resp = client.post("/api/v1/tools/cart", json={"session_id": session_id})
    cart_id = cart_resp.json()["data"]["cart_id"]

    resp = client.post("/api/v1/tools/orders", json={"cart_id": cart_id, "session_id": session_id})
    assert resp.json()["success"] is False
    assert "empty" in resp.json()["error"].lower()
