"""
Commerce API: Agent-readable structured tool endpoints.
Each endpoint has clear input/output schemas, validation, and audit logging.
"""
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import (
    ToolResponse, SearchProductsRequest, CreateCartRequest,
    AddToCartRequest, CreateOrderRequest,
)
from app.services import catalog as catalog_svc
from app.services import cart as cart_svc
from app.services import order as order_svc
from app.services import payment as payment_svc
from app.services import audit as audit_svc
from app.services import growth as growth_svc

router = APIRouter(prefix="/api/v1/tools", tags=["Agent Commerce Tools"])


@router.post("/search_products", response_model=ToolResponse)
def search_products(
    req: SearchProductsRequest,
    db: Session = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """Search the product catalog with filters."""
    try:
        result = catalog_svc.search_products(
            db, query=req.query, category=req.category,
            min_price=req.min_price, max_price=req.max_price,
            color=req.color, brand=req.brand, size=req.size,
            limit=req.limit,
        )
        audit_svc.log_action(
            db, tool_name="search_products", result_status="success",
            session_id=x_session_id,
            input_summary=f"query={req.query} category={req.category} price={req.min_price}-{req.max_price} color={req.color}",
            details={"total_found": result.total_found},
        )
        return ToolResponse(success=True, data=result.model_dump(), tool="search_products")
    except Exception as e:
        audit_svc.log_action(db, tool_name="search_products", result_status="error",
                             session_id=x_session_id, input_summary=str(req.model_dump()), details={"error": str(e)})
        return ToolResponse(success=False, error=str(e), tool="search_products")


@router.get("/products/{product_id}", response_model=ToolResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """Get full product details by ID."""
    product = catalog_svc.get_product(db, product_id)
    if not product:
        audit_svc.log_action(db, tool_name="get_product", result_status="error",
                             session_id=x_session_id, input_summary=f"product_id={product_id}",
                             details={"error": "Product not found"})
        return ToolResponse(success=False, error=f"Product '{product_id}' not found.", tool="get_product")
    audit_svc.log_action(db, tool_name="get_product", result_status="success",
                         session_id=x_session_id, input_summary=f"product_id={product_id}")
    return ToolResponse(success=True, data=product.model_dump(), tool="get_product")


@router.get("/products/{product_id}/stock", response_model=ToolResponse)
def check_stock(
    product_id: str,
    db: Session = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """Check stock availability for a product."""
    stock_info = catalog_svc.check_stock(db, product_id)
    if not stock_info:
        audit_svc.log_action(db, tool_name="check_stock", result_status="error",
                             session_id=x_session_id, input_summary=f"product_id={product_id}",
                             details={"error": "Product not found"})
        return ToolResponse(success=False, error=f"Product '{product_id}' not found.", tool="check_stock")
    audit_svc.log_action(db, tool_name="check_stock", result_status="success",
                         session_id=x_session_id, input_summary=f"product_id={product_id}",
                         details={"available": stock_info.available, "stock": stock_info.stock})
    return ToolResponse(success=True, data=stock_info.model_dump(), tool="check_stock")


@router.post("/cart", response_model=ToolResponse)
def create_cart(
    req: CreateCartRequest,
    db: Session = Depends(get_db),
):
    """Create a new shopping cart for an agent session."""
    try:
        cart = cart_svc.create_cart(db, session_id=req.session_id)
        audit_svc.log_action(db, tool_name="create_cart", result_status="success",
                             session_id=req.session_id, input_summary=f"session_id={req.session_id}",
                             details={"cart_id": cart.cart_id})
        return ToolResponse(success=True, data=cart.model_dump(), tool="create_cart")
    except Exception as e:
        audit_svc.log_action(db, tool_name="create_cart", result_status="error",
                             session_id=req.session_id, details={"error": str(e)})
        return ToolResponse(success=False, error=str(e), tool="create_cart")


@router.post("/cart/{cart_id}/items", response_model=ToolResponse)
def add_to_cart(
    cart_id: str,
    req: AddToCartRequest,
    db: Session = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """Add a product to an existing cart."""
    result = cart_svc.add_to_cart(db, cart_id=cart_id, product_id=req.product_id, quantity=req.quantity)
    status = "success" if result["success"] else "error"
    audit_svc.log_action(
        db, tool_name="add_to_cart", result_status=status,
        session_id=x_session_id,
        input_summary=f"cart_id={cart_id} product_id={req.product_id} qty={req.quantity}",
        details={"message": result.get("message") or result.get("error")},
    )
    if result["success"]:
        return ToolResponse(success=True, data=result["data"].model_dump(), tool="add_to_cart")
    return ToolResponse(success=False, error=result["error"], tool="add_to_cart")


@router.post("/orders", response_model=ToolResponse)
def create_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
):
    """Create an order from a cart. Server-side price calculation."""
    result = order_svc.create_order(db, cart_id=req.cart_id, session_id=req.session_id)
    status = "success" if result["success"] else "error"
    order_id = result["data"].order_id if result["success"] else None
    audit_svc.log_action(
        db, tool_name="create_order", result_status=status,
        session_id=req.session_id,
        input_summary=f"cart_id={req.cart_id}",
        order_id=order_id,
        details={"message": result.get("message") or result.get("error")},
    )
    if result["success"]:
        return ToolResponse(success=True, data=result["data"].model_dump(), tool="create_order")
    return ToolResponse(success=False, error=result["error"], tool="create_order")


@router.get("/orders/{order_id}", response_model=ToolResponse)
def get_order_status(
    order_id: str,
    db: Session = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """Get order details and current status."""
    order = order_svc.get_order_status(db, order_id)
    if not order:
        audit_svc.log_action(db, tool_name="get_order_status", result_status="error",
                             session_id=x_session_id, input_summary=f"order_id={order_id}",
                             details={"error": "Order not found"})
        return ToolResponse(success=False, error=f"Order '{order_id}' not found.", tool="get_order_status")
    audit_svc.log_action(db, tool_name="get_order_status", result_status="success",
                         session_id=x_session_id, input_summary=f"order_id={order_id}", order_id=order_id)
    return ToolResponse(success=True, data=order.model_dump(), tool="get_order_status")


@router.post("/orders/{order_id}/checkout", response_model=ToolResponse)
def create_checkout(
    order_id: str,
    db: Session = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """Initiate payment/checkout for an order."""
    order = order_svc.get_order_status(db, order_id)
    if not order:
        audit_svc.log_action(db, tool_name="create_checkout", result_status="error",
                             session_id=x_session_id, input_summary=f"order_id={order_id}",
                             details={"error": "Order not found"})
        return ToolResponse(success=False, error=f"Order '{order_id}' not found.", tool="create_checkout")

    if order.status not in ("pending",):
        audit_svc.log_action(db, tool_name="create_checkout", result_status="error",
                             session_id=x_session_id, input_summary=f"order_id={order_id}",
                             order_id=order_id, details={"error": f"Order status is '{order.status}', expected 'pending'"})
        return ToolResponse(success=False, error=f"Cannot checkout: order status is '{order.status}'.", tool="create_checkout")

    checkout = payment_svc.create_checkout(order_id, order.total_amount, order.currency)

    # Update order with razorpay info
    if checkout.razorpay_order_id:
        order_svc.update_order_status(
            db, order_id, "payment_pending",
            razorpay_order_id=checkout.razorpay_order_id,
        )

    audit_svc.log_action(
        db, tool_name="create_checkout", result_status="success",
        session_id=x_session_id, input_summary=f"order_id={order_id}",
        order_id=order_id,
        details={"payment_mode": checkout.payment_mode, "amount": checkout.amount},
    )
    return ToolResponse(success=True, data=checkout.model_dump(), tool="create_checkout")


# ─── Dashboard-Facing Endpoints ──────────────────────────────────────────────

@router.get("/orders", response_model=ToolResponse)
def list_orders(
    db: Session = Depends(get_db),
):
    """List all orders (for merchant dashboard)."""
    try:
        orders = order_svc.get_all_orders(db)
        data = [o.model_dump() for o in orders]
        return ToolResponse(success=True, data=data, tool="list_orders")
    except Exception as e:
        return ToolResponse(success=False, error=str(e), tool="list_orders")


@router.get("/audit/logs", response_model=ToolResponse)
def get_audit_logs(
    session_id: Optional[str] = Query(None),
    tool_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve audit logs with optional filters."""
    try:
        logs = audit_svc.get_audit_logs(db, session_id=session_id, tool_name=tool_name, limit=limit)
        data = [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "session_id": l.session_id,
                "tool_name": l.tool_name,
                "input_summary": l.input_summary,
                "result_status": l.result_status,
                "order_id": l.order_id,
                "details": l.details,
            }
            for l in logs
        ]
        return ToolResponse(success=True, data=data, tool="audit_logs")
    except Exception as e:
        return ToolResponse(success=False, error=str(e), tool="audit_logs")


@router.get("/growth/insights", response_model=ToolResponse)
def get_growth_insights(
    db: Session = Depends(get_db),
):
    """Get AI-generated growth insights (upsell/cross-sell recommendations)."""
    try:
        insights = growth_svc.get_growth_insights(db)
        data = [
            {
                "recommended_product": i.recommended_product_name,
                "reason": i.reason,
                "target_context": i.target_context,
                "estimated_value": i.estimated_additional_value,
                "confidence": i.confidence_score,
                "type": "cross_sell" if "cross" in i.reason.lower() or "diversity" in i.reason.lower() else "upsell",
                "category": i.category,
                "source_product": i.target_context,
            }
            for i in insights
        ]
        return ToolResponse(success=True, data=data, tool="growth_insights")
    except Exception as e:
        return ToolResponse(success=False, error=str(e), tool="growth_insights")
