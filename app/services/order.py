"""
Order service: create order from cart, get order status, update status.
Server-side price calculation, duplicate order prevention.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Order, Cart, CartItem, Product
from app.schemas import OrderOut, OrderItemOut


def create_order(db: Session, cart_id: str, session_id: str) -> dict:
    """
    Create an order from a cart. 
    Server-side price calculation. Prevents duplicate orders from same cart.
    """
    # Validate cart exists
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        return {"success": False, "error": f"Cart '{cart_id}' not found."}

    # Check cart belongs to session
    if cart.session_id != session_id:
        return {"success": False, "error": "Cart does not belong to this session."}

    # Prevent duplicate order from same cart
    existing_order = db.query(Order).filter(Order.cart_id == cart_id).first()
    if existing_order:
        return {
            "success": False,
            "error": f"An order already exists for this cart (Order ID: {existing_order.id}). Duplicate order prevented.",
        }

    # Check cart has items
    if not cart.items or len(cart.items) == 0:
        return {"success": False, "error": "Cart is empty. Add items before creating an order."}

    # Check cart is active
    if cart.status != "active":
        return {"success": False, "error": f"Cart is already {cart.status}."}

    # Server-side price calculation (never trust client price)
    total_amount = 0.0
    items_snapshot = []
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            return {"success": False, "error": f"Product '{item.product_id}' no longer exists."}
        if not product.available:
            return {"success": False, "error": f"Product '{product.name}' is no longer available."}
        if product.stock < item.quantity:
            return {
                "success": False,
                "error": f"Insufficient stock for '{product.name}'. Requested: {item.quantity}, Available: {product.stock}.",
            }

        # Use current server price
        subtotal = product.price * item.quantity
        total_amount += subtotal
        items_snapshot.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit_price": product.price,
            "subtotal": subtotal,
        })

    if total_amount <= 0:
        return {"success": False, "error": "Invalid order amount. Total must be greater than 0."}

    # Create order
    order = Order(
        id=f"ord_{uuid.uuid4().hex[:12]}",
        cart_id=cart_id,
        session_id=session_id,
        status="pending",
        total_amount=total_amount,
        currency="INR",
        items_snapshot=items_snapshot,
    )
    db.add(order)

    # Mark cart as checked_out
    cart.status = "checked_out"

    # Decrement stock
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock -= item.quantity
        if product.stock <= 0:
            product.available = False

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "data": _order_to_schema(order),
        "message": f"Order created successfully. Total: ₹{total_amount}",
    }


def get_order_status(db: Session, order_id: str) -> OrderOut | None:
    """Get order details and status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None
    return _order_to_schema(order)


def update_order_status(db: Session, order_id: str, status: str, **kwargs) -> bool:
    """Update order status and optional fields (razorpay IDs etc.)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return False
    order.status = status
    order.updated_at = datetime.now(timezone.utc)
    for key, value in kwargs.items():
        if hasattr(order, key):
            setattr(order, key, value)
    db.commit()
    return True


def get_all_orders(db: Session) -> list:
    """Get all orders for dashboard."""
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [_order_to_schema(o) for o in orders]


def _order_to_schema(order: Order) -> OrderOut:
    """Convert Order ORM to OrderOut schema."""
    items = []
    if order.items_snapshot:
        for item in order.items_snapshot:
            items.append(OrderItemOut(
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"],
            ))

    return OrderOut(
        order_id=order.id,
        cart_id=order.cart_id,
        session_id=order.session_id,
        status=order.status,
        total_amount=order.total_amount,
        currency=order.currency,
        items=items,
        razorpay_order_id=order.razorpay_order_id,
        razorpay_payment_id=order.razorpay_payment_id,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
