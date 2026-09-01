"""
SQLAlchemy ORM models for Bharat Bazaar AI.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    stock = Column(Integer, default=0)
    available = Column(Boolean, default=True)
    attributes = Column(JSON, default=dict)  # {"color": "blue", "size": "M", "brand": "..."}
    related_products = Column(JSON, default=list)  # ["prod_002", "prod_005"]
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Cart(Base):
    __tablename__ = "carts"

    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    status = Column(String, default="active")  # active, checked_out
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String, ForeignKey("carts.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)  # Captured at time of add (server-side)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    cart_id = Column(String, ForeignKey("carts.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    status = Column(String, default="pending")  # pending, confirmed, paid, failed, cancelled
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    items_snapshot = Column(JSON, default=list)  # Frozen copy of cart items at order time
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session_id = Column(String, nullable=True)
    tool_name = Column(String, nullable=False)
    input_summary = Column(Text, nullable=True)
    result_status = Column(String, nullable=False)  # success, error
    order_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
