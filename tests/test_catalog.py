"""
Tests for the catalog service and API endpoints.
"""


def test_search_products_basic(client):
    """Search with a general query returns results."""
    resp = client.post("/api/v1/tools/search_products", json={"query": "sneakers"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["total_found"] > 0
    products = data["data"]["products"]
    assert len(products) > 0
    # Check product fields
    p = products[0]
    assert "product_id" in p
    assert "name" in p
    assert "price" in p


def test_search_products_by_category(client):
    """Filter by category returns matching products."""
    resp = client.post("/api/v1/tools/search_products", json={"category": "shoes"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    for p in data["data"]["products"]:
        assert p["category"].lower() == "shoes"


def test_search_products_price_range(client):
    """Filter by price range works correctly."""
    resp = client.post(
        "/api/v1/tools/search_products",
        json={"min_price": 1000, "max_price": 2000},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    for p in data["data"]["products"]:
        assert 1000 <= p["price"] <= 2000


def test_get_product_valid(client):
    """Get product by valid ID returns full details."""
    # First search to get a product ID
    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product_id = search_resp.json()["data"]["products"][0]["product_id"]

    resp = client.get(f"/api/v1/tools/products/{product_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["product_id"] == product_id


def test_get_product_invalid(client):
    """Get product by invalid ID returns error."""
    resp = client.get("/api/v1/tools/products/nonexistent_id")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_check_stock_valid(client):
    """Check stock for a valid product."""
    search_resp = client.post("/api/v1/tools/search_products", json={"limit": 1})
    product_id = search_resp.json()["data"]["products"][0]["product_id"]

    resp = client.get(f"/api/v1/tools/products/{product_id}/stock")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "available" in data["data"]
    assert "stock" in data["data"]


def test_check_stock_invalid(client):
    """Check stock for invalid product returns error."""
    resp = client.get("/api/v1/tools/products/fake_product/stock")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
