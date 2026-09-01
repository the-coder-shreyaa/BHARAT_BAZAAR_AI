"""
Discovery endpoint: makes the merchant programmatically discoverable by AI agents.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.schemas import MerchantManifest, ToolSchema
from app.services.catalog import get_category_counts

router = APIRouter(tags=["Discovery"])


@router.get("/.well-known/ai-commerce.json", response_model=MerchantManifest)
def get_merchant_manifest(db: Session = Depends(get_db)):
    """AI-discoverable merchant manifest with all available commerce tools."""
    cats = get_category_counts(db)
    total = sum(cats.values())

    tools = [
        ToolSchema(
            name="search_products",
            description="Search the product catalog by query, category, price range, color, brand, size.",
            method="POST",
            path="/api/v1/tools/search_products",
            input_schema={"query": "string", "category": "string", "min_price": "number", "max_price": "number", "color": "string", "brand": "string", "size": "string", "limit": "integer"},
            output_schema={"products": "array", "total_found": "integer", "query_summary": "string"},
        ),
        ToolSchema(
            name="get_product",
            description="Get full details of a specific product by its ID.",
            method="GET",
            path="/api/v1/tools/products/{product_id}",
            input_schema={"product_id": "string (path parameter)"},
            output_schema={"product_id": "string", "name": "string", "description": "string", "category": "string", "price": "number", "currency": "string", "stock": "integer", "available": "boolean", "attributes": "object", "related_products": "array"},
        ),
        ToolSchema(
            name="check_stock",
            description="Check real-time stock availability for a product.",
            method="GET",
            path="/api/v1/tools/products/{product_id}/stock",
            input_schema={"product_id": "string (path parameter)"},
            output_schema={"product_id": "string", "name": "string", "available": "boolean", "stock": "integer", "message": "string"},
        ),
        ToolSchema(
            name="create_cart",
            description="Create a new shopping cart for an agent session.",
            method="POST",
            path="/api/v1/tools/cart",
            input_schema={"session_id": "string"},
            output_schema={"cart_id": "string", "session_id": "string", "status": "string", "items": "array", "total": "number"},
        ),
        ToolSchema(
            name="add_to_cart",
            description="Add a product to an existing cart. Validates stock and availability.",
            method="POST",
            path="/api/v1/tools/cart/{cart_id}/items",
            input_schema={"product_id": "string", "quantity": "integer (1-10)"},
            output_schema={"cart_id": "string", "items": "array", "total": "number"},
        ),
        ToolSchema(
            name="create_order",
            description="Convert a cart into an order. Server-side price calculation. Prevents duplicates.",
            method="POST",
            path="/api/v1/tools/orders",
            input_schema={"cart_id": "string", "session_id": "string"},
            output_schema={"order_id": "string", "total_amount": "number", "status": "string", "items": "array"},
        ),
        ToolSchema(
            name="get_order_status",
            description="Check the current status and details of an order.",
            method="GET",
            path="/api/v1/tools/orders/{order_id}",
            input_schema={"order_id": "string (path parameter)"},
            output_schema={"order_id": "string", "status": "string", "total_amount": "number", "items": "array"},
        ),
        ToolSchema(
            name="create_checkout",
            description="Initiate payment/checkout for a pending order. Returns payment link.",
            method="POST",
            path="/api/v1/tools/orders/{order_id}/checkout",
            input_schema={"order_id": "string (path parameter)"},
            output_schema={"order_id": "string", "razorpay_order_id": "string", "payment_url": "string", "amount": "number", "status": "string"},
        ),
    ]

    return MerchantManifest(
        merchant_name=settings.MERCHANT_NAME,
        merchant_description=settings.MERCHANT_DESCRIPTION,
        api_version="1.0",
        currency=settings.MERCHANT_CURRENCY,
        tools=tools,
        supported_categories=list(cats.keys()),
        total_products=total,
    )
