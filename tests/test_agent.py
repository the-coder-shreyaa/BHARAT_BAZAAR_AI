"""
End-to-end agent flow test: search → product → stock → cart → order → checkout.
"""


def test_full_agent_flow(client):
    """Simulate a complete AI buyer agent purchasing flow."""
    session_id = "test-agent-e2e"

    # Step 1: Search
    search_resp = client.post(
        "/api/v1/tools/search_products",
        json={"query": "sneakers", "limit": 5},
        headers={"x-session-id": session_id},
    )
    assert search_resp.json()["success"] is True
    products = search_resp.json()["data"]["products"]
    assert len(products) > 0
    product_id = products[0]["product_id"]

    # Step 2: Get product details
    detail_resp = client.get(
        f"/api/v1/tools/products/{product_id}",
        headers={"x-session-id": session_id},
    )
    assert detail_resp.json()["success"] is True
    assert detail_resp.json()["data"]["product_id"] == product_id

    # Step 3: Check stock
    stock_resp = client.get(
        f"/api/v1/tools/products/{product_id}/stock",
        headers={"x-session-id": session_id},
    )
    assert stock_resp.json()["success"] is True
    assert stock_resp.json()["data"]["available"] is True

    # Step 4: Create cart
    cart_resp = client.post(
        "/api/v1/tools/cart",
        json={"session_id": session_id},
    )
    assert cart_resp.json()["success"] is True
    cart_id = cart_resp.json()["data"]["cart_id"]

    # Step 5: Add to cart
    add_resp = client.post(
        f"/api/v1/tools/cart/{cart_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers={"x-session-id": session_id},
    )
    assert add_resp.json()["success"] is True

    # Step 6: Create order
    order_resp = client.post(
        "/api/v1/tools/orders",
        json={"cart_id": cart_id, "session_id": session_id},
    )
    assert order_resp.json()["success"] is True
    order_id = order_resp.json()["data"]["order_id"]
    assert order_resp.json()["data"]["total_amount"] > 0

    # Step 7: Checkout
    checkout_resp = client.post(
        f"/api/v1/tools/orders/{order_id}/checkout",
        headers={"x-session-id": session_id},
    )
    assert checkout_resp.json()["success"] is True
    assert checkout_resp.json()["data"]["amount"] > 0

    # Verify: audit logs should have entries for this session
    audit_resp = client.get(
        "/api/v1/tools/audit/logs",
        params={"session_id": session_id},
    )
    assert audit_resp.json()["success"] is True
    logs = audit_resp.json()["data"]
    assert len(logs) >= 6  # At least 6 tool calls logged

    # Verify: order appears in list
    orders_resp = client.get("/api/v1/tools/orders")
    assert orders_resp.json()["success"] is True


def test_discovery_manifest(client):
    """Discovery manifest returns a valid merchant description."""
    resp = client.get("/.well-known/ai-commerce.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "merchant_name" in data
    assert "tools" in data
    assert len(data["tools"]) >= 8


def test_health_endpoint(client):
    """Health endpoint returns OK."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
