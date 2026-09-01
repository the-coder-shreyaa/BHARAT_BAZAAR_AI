"""
Catalog service: product search, lookup, and stock check.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
from app.models import Product
from app.schemas import ProductOut, SearchProductsResponse, StockCheckResponse


def search_products(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    size: Optional[str] = None,
    limit: int = 10,
) -> SearchProductsResponse:
    """Search products with filters. Full-text search on name/description."""
    q = db.query(Product)

    filters_applied = []

    if category:
        q = q.filter(func.lower(Product.category) == category.lower())
        filters_applied.append(f"category={category}")

    if min_price is not None:
        q = q.filter(Product.price >= min_price)
        filters_applied.append(f"min_price={min_price}")

    if max_price is not None:
        q = q.filter(Product.price <= max_price)
        filters_applied.append(f"max_price={max_price}")

    if query:
        search_term = f"%{query.lower()}%"
        q = q.filter(
            or_(
                func.lower(Product.name).like(search_term),
                func.lower(Product.description).like(search_term),
            )
        )
        filters_applied.append(f"query='{query}'")

    # Filter by attributes (color, brand, size) stored in JSON
    if color:
        # SQLite JSON: filter where attributes->color contains the color
        q = q.filter(
            func.lower(func.json_extract(Product.attributes, "$.color")).like(f"%{color.lower()}%")
        )
        filters_applied.append(f"color={color}")

    if brand:
        q = q.filter(
            func.lower(func.json_extract(Product.attributes, "$.brand")).like(f"%{brand.lower()}%")
        )
        filters_applied.append(f"brand={brand}")

    if size:
        q = q.filter(
            func.json_extract(Product.attributes, "$.size").like(f"%{size}%")
        )
        filters_applied.append(f"size={size}")

    # Only show available products by default
    q = q.filter(Product.available == True)

    total = q.count()
    products = q.limit(limit).all()

    product_list = [
        ProductOut(
            product_id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            price=p.price,
            currency=p.currency,
            stock=p.stock,
            available=p.available,
            attributes=p.attributes or {},
            related_products=p.related_products or [],
            image_url=p.image_url,
        )
        for p in products
    ]

    summary = f"Found {total} products"
    if filters_applied:
        summary += f" matching: {', '.join(filters_applied)}"

    return SearchProductsResponse(
        products=product_list,
        total_found=total,
        query_summary=summary,
    )


def get_product(db: Session, product_id: str) -> Optional[ProductOut]:
    """Get full product details by ID."""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return None
    return ProductOut(
        product_id=p.id,
        name=p.name,
        description=p.description,
        category=p.category,
        price=p.price,
        currency=p.currency,
        stock=p.stock,
        available=p.available,
        attributes=p.attributes or {},
        related_products=p.related_products or [],
        image_url=p.image_url,
    )


def check_stock(db: Session, product_id: str) -> Optional[StockCheckResponse]:
    """Check stock availability for a product."""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return None

    if not p.available:
        message = f"{p.name} is currently unavailable."
    elif p.stock == 0:
        message = f"{p.name} is out of stock."
    elif p.stock < 5:
        message = f"{p.name} is available but low on stock ({p.stock} left)."
    else:
        message = f"{p.name} is in stock ({p.stock} units available)."

    return StockCheckResponse(
        product_id=p.id,
        name=p.name,
        available=p.available and p.stock > 0,
        stock=p.stock,
        message=message,
    )


def get_all_products(db: Session) -> List[ProductOut]:
    """Get all products (for dashboard)."""
    products = db.query(Product).all()
    return [
        ProductOut(
            product_id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            price=p.price,
            currency=p.currency,
            stock=p.stock,
            available=p.available,
            attributes=p.attributes or {},
            related_products=p.related_products or [],
            image_url=p.image_url,
        )
        for p in products
    ]


def get_category_counts(db: Session) -> dict:
    """Get product counts by category."""
    results = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    return {cat: count for cat, count in results}
