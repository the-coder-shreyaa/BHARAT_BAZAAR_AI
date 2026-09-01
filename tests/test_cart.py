"""
Tests for the cart service and API endpoints.
"""


def test_create_cart(client):
    """Creating a cart returns a valid cart object."""
    resp = client.post("/api/v1/tools/cart", json={"session_id": "test-session-cart"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "cart_id" in data["data"]
    assert data["data"]["session_id"] == "test-session-cart"
    assert data["data"]["status"] == "active"


def test_add_to_cart(client):
    """Adding a product to a cart works correctly."""
    # Create cart
    cart_resp = client.post("/api/v1/tools/cart", json={"session_id": "test-session-add"})
    cart_id = cart_resp.json()["data"]["cart_id"]

    # Get a product
    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product_id = search_resp.json()["data"]["products"][0]["product_id"]

    # Add to cart
    resp = client.post(
        f"/api/v1/tools/cart/{cart_id}/items",
        json={"product_id": product_id, "quantity": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["item_count"] >= 1


def test_add_invalid_product_to_cart(client):
    """Adding a non-existent product to cart fails gracefully."""
    cart_resp = client.post("/api/v1/tools/cart", json={"session_id": "test-session-invalid"})
    cart_id = cart_resp.json()["data"]["cart_id"]

    resp = client.post(
        f"/api/v1/tools/cart/{cart_id}/items",
        json={"product_id": "nonexistent_product", "quantity": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False


def test_add_to_invalid_cart(client):
    """Adding to a non-existent cart fails gracefully."""
    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product_id = search_resp.json()["data"]["products"][0]["product_id"]

    resp = client.post(
        "/api/v1/tools/cart/nonexistent_cart/items",
        json={"product_id": product_id, "quantity": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
