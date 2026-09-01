"""
Pydantic schemas for request/response validation across all commerce tools.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Generic Response Envelope ───────────────────────────────────────────────

class ToolResponse(BaseModel):
    """Standard response envelope for all agent-readable tools."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    tool: str = ""


# ─── Product Schemas ─────────────────────────────────────────────────────────

class ProductOut(BaseModel):
    product_id: str
    name: str
    description: str
    category: str
    price: float
    currency: str = "INR"
    stock: int
    available: bool
    attributes: Dict[str, Any] = {}
    related_products: List[str] = []
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class SearchProductsRequest(BaseModel):
    query: Optional[str] = Field(None, description="Free-text search query")
    category: Optional[str] = Field(None, description="Filter by category: clothing, shoes, accessories, bags")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price in INR")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price in INR")
    color: Optional[str] = Field(None, description="Filter by color")
    brand: Optional[str] = Field(None, description="Filter by brand")
    size: Optional[str] = Field(None, description="Filter by size")
    limit: int = Field(10, ge=1, le=50, description="Max results to return")


class SearchProductsResponse(BaseModel):
    products: List[ProductOut]
    total_found: int
    query_summary: str


class StockCheckResponse(BaseModel):
    product_id: str
    name: str
    available: bool
    stock: int
    message: str


# ─── Cart Schemas ────────────────────────────────────────────────────────────

class CreateCartRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for the AI buyer agent")


class CartItemOut(BaseModel):
    product_id: str
    product_name: str = ""
    quantity: int
    unit_price: float
    subtotal: float = 0.0

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    cart_id: str
    session_id: str
    status: str
    items: List[CartItemOut] = []
    total: float = 0.0
    item_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AddToCartRequest(BaseModel):
    product_id: str = Field(..., description="Product ID to add")
    quantity: int = Field(1, ge=1, le=10, description="Quantity to add (1-10)")


# ─── Order Schemas ───────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    cart_id: str = Field(..., description="Cart ID to convert into an order")
    session_id: str = Field(..., description="Session ID of the buyer agent")


class OrderItemOut(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderOut(BaseModel):
    order_id: str
    cart_id: str
    session_id: str
    status: str
    total_amount: float
    currency: str
    items: List[OrderItemOut] = []
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    order_id: str
    razorpay_order_id: Optional[str] = None
    payment_url: Optional[str] = None
    amount: float
    currency: str
    status: str
    message: str
    payment_mode: str = "razorpay"  # "razorpay" or "simulation"


# ─── Growth Insight Schemas ──────────────────────────────────────────────────

class GrowthInsight(BaseModel):
    recommended_product_id: str
    recommended_product_name: str
    reason: str
    target_context: str
    estimated_additional_value: float
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    category: str = ""


# ─── Audit Log Schemas ──────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    timestamp: Optional[datetime]
    session_id: Optional[str]
    tool_name: str
    input_summary: Optional[str]
    result_status: str
    order_id: Optional[str]
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ─── Discovery Schema ───────────────────────────────────────────────────────

class ToolSchema(BaseModel):
    name: str
    description: str
    method: str
    path: str
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}


class MerchantManifest(BaseModel):
    merchant_name: str
    merchant_description: str
    api_version: str = "1.0"
    currency: str = "INR"
    tools: List[ToolSchema]
    supported_categories: List[str]
    total_products: int
