"""
Cart service: create cart, add items, get cart with validation.
"""
import uuid
from sqlalchemy.orm import Session
from app.models import Cart, CartItem, Product
from app.schemas import CartOut, CartItemOut


def create_cart(db: Session, session_id: str) -> CartOut:
    """Create a new shopping cart for a session."""
    cart = Cart(
        id=f"cart_{uuid.uuid4().hex[:12]}",
        session_id=session_id,
        status="active",
    )
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return _cart_to_schema(cart)


def add_to_cart(db: Session, cart_id: str, product_id: str, quantity: int = 1) -> dict:
    """
    Add a product to a cart. Returns dict with success/error info.
    Validates: cart exists, cart is active, product exists, product available, sufficient stock.
    """
    # Validate cart
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        return {"success": False, "error": f"Cart '{cart_id}' not found."}
    if cart.status != "active":
        return {"success": False, "error": f"Cart '{cart_id}' is already {cart.status}. Cannot add items."}

    # Validate product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"success": False, "error": f"Product '{product_id}' not found."}
    if not product.available:
        return {"success": False, "error": f"Product '{product.name}' is currently unavailable."}

    # Validate quantity
    if quantity < 1:
        return {"success": False, "error": "Quantity must be at least 1."}
    if quantity > 10:
        return {"success": False, "error": "Maximum quantity per item is 10."}

    # Check stock
    # Calculate existing quantity in cart for this product
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == product_id,
    ).first()

    current_qty = existing_item.quantity if existing_item else 0
    total_qty = current_qty + quantity

    if total_qty > product.stock:
        return {
            "success": False,
            "error": f"Insufficient stock for '{product.name}'. Requested: {total_qty}, Available: {product.stock}.",
        }

    # Add or update cart item (price captured server-side)
    if existing_item:
        existing_item.quantity = total_qty
        existing_item.unit_price = product.price  # Always use current server price
    else:
        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,  # Server-side price capture
        )
        db.add(item)

    db.commit()
    db.refresh(cart)

    return {
        "success": True,
        "data": _cart_to_schema(cart),
        "message": f"Added {quantity}x '{product.name}' to cart. Unit price: ₹{product.price}",
    }


def get_cart(db: Session, cart_id: str) -> CartOut | None:
    """Get cart with all items."""
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        return None
    return _cart_to_schema(cart)


def _cart_to_schema(cart: Cart) -> CartOut:
    """Convert Cart ORM object to CartOut schema."""
    items = []
    total = 0.0
    for item in cart.items:
        subtotal = item.quantity * item.unit_price
        total += subtotal
        product_name = item.product.name if item.product else "Unknown"
        items.append(CartItemOut(
            product_id=item.product_id,
            product_name=product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=subtotal,
        ))

    return CartOut(
        cart_id=cart.id,
        session_id=cart.session_id,
        status=cart.status,
        items=items,
        total=total,
        item_count=len(items),
        created_at=cart.created_at,
    )
