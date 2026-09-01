"""
Agent tool registry: maps tool names to actual API calls via HTTP.
Each tool has typed input/output and calls the FastAPI commerce endpoints.
"""
import httpx
from typing import Any, Dict, Optional
from app.config import settings

BASE_URL = f"http://localhost:{settings.API_PORT}"


class CommerceToolkit:
    """Structured toolkit for AI buyer agents to interact with the commerce API."""

    def __init__(self, session_id: str, base_url: str = None):
        self.session_id = session_id
        self.base_url = base_url or BASE_URL
        self.headers = {"X-Session-Id": session_id}

    def search_products(self, query: str = None, category: str = None,
                        min_price: float = None, max_price: float = None,
                        color: str = None, brand: str = None, limit: int = 10) -> Dict[str, Any]:
        """Search products with filters."""
        payload = {k: v for k, v in {
            "query": query, "category": category,
            "min_price": min_price, "max_price": max_price,
            "color": color, "brand": brand, "limit": limit,
        }.items() if v is not None}
        return self._post("/api/v1/tools/search_products", payload)

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get full product details."""
        return self._get(f"/api/v1/tools/products/{product_id}")

    def check_stock(self, product_id: str) -> Dict[str, Any]:
        """Check stock availability."""
        return self._get(f"/api/v1/tools/products/{product_id}/stock")

    def create_cart(self) -> Dict[str, Any]:
        """Create a new cart for this session."""
        return self._post("/api/v1/tools/cart", {"session_id": self.session_id})

    def add_to_cart(self, cart_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a product to cart."""
        return self._post(f"/api/v1/tools/cart/{cart_id}/items",
                          {"product_id": product_id, "quantity": quantity})

    def create_order(self, cart_id: str) -> Dict[str, Any]:
        """Create order from cart."""
        return self._post("/api/v1/tools/orders",
                          {"cart_id": cart_id, "session_id": self.session_id})

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check order status."""
        return self._get(f"/api/v1/tools/orders/{order_id}")

    def create_checkout(self, order_id: str) -> Dict[str, Any]:
        """Initiate checkout/payment."""
        return self._post(f"/api/v1/tools/orders/{order_id}/checkout", {})

    def _get(self, path: str) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{self.base_url}{path}", headers=self.headers, timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": f"HTTP error: {str(e)}"}

    def _post(self, path: str, payload: dict) -> Dict[str, Any]:
        try:
            r = httpx.post(f"{self.base_url}{path}", json=payload, headers=self.headers, timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": f"HTTP error: {str(e)}"}

    @staticmethod
    def get_tool_descriptions() -> list:
        """Return list of available tools with descriptions for LLM function calling."""
        return [
            {"name": "search_products", "description": "Search products by query, category, price range, color, brand", "parameters": {"query": "str", "category": "str", "min_price": "float", "max_price": "float", "color": "str", "brand": "str"}},
            {"name": "get_product", "description": "Get full details of a product by ID", "parameters": {"product_id": "str"}},
            {"name": "check_stock", "description": "Check stock availability of a product", "parameters": {"product_id": "str"}},
            {"name": "create_cart", "description": "Create a new shopping cart", "parameters": {}},
            {"name": "add_to_cart", "description": "Add product to cart", "parameters": {"cart_id": "str", "product_id": "str", "quantity": "int"}},
            {"name": "create_order", "description": "Create order from cart", "parameters": {"cart_id": "str"}},
            {"name": "get_order_status", "description": "Check order status", "parameters": {"order_id": "str"}},
            {"name": "create_checkout", "description": "Initiate payment for order", "parameters": {"order_id": "str"}},
        ]
