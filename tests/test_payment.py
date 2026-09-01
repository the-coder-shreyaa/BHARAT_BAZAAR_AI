"""
Tests for the payment/checkout flow.
"""


def _create_pending_order(client, session_id="test-session-payment"):
    """Helper: create a pending order ready for checkout."""
    cart_resp = client.post("/api/v1/tools/cart", json={"session_id": session_id})
    cart_id = cart_resp.json()["data"]["cart_id"]

    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product_id = search_resp.json()["data"]["products"][0]["product_id"]

    client.post(
        f"/api/v1/tools/cart/{cart_id}/items",
        json={"product_id": product_id, "quantity": 1},
    )

    order_resp = client.post(
        "/api/v1/tools/orders",
        json={"cart_id": cart_id, "session_id": session_id},
    )
    return order_resp.json()["data"]["order_id"]


def test_checkout_creates_payment(client):
    """Checkout for a pending order creates a payment (simulation mode)."""
    order_id = _create_pending_order(client, "test-session-checkout")

    resp = client.post(f"/api/v1/tools/orders/{order_id}/checkout")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["order_id"] == order_id
    assert data["data"]["amount"] > 0
    assert "payment_mode" in data["data"]


def test_checkout_invalid_order(client):
    """Checkout for a non-existent order fails."""
    resp = client.post("/api/v1/tools/orders/fake_order/checkout")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_checkout_amount_matches_order(client):
    """Checkout amount matches the order total."""
    session_id = "test-session-amount"
    cart_resp = client.post("/api/v1/tools/cart", json={"session_id": session_id})
    cart_id = cart_resp.json()["data"]["cart_id"]

    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product = search_resp.json()["data"]["products"][0]
    product_id = product["product_id"]

    client.post(
        f"/api/v1/tools/cart/{cart_id}/items",
        json={"product_id": product_id, "quantity": 2},
    )

    order_resp = client.post(
        "/api/v1/tools/orders",
        json={"cart_id": cart_id, "session_id": session_id},
    )
    order_data = order_resp.json()["data"]
    order_id = order_data["order_id"]

    checkout_resp = client.post(f"/api/v1/tools/orders/{order_id}/checkout")
    checkout_data = checkout_resp.json()["data"]
    assert checkout_data["amount"] == order_data["total_amount"]
