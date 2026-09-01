"""
Growth insights service: upsell/cross-sell recommendations from catalog and order data.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.models import Product, Order
from app.schemas import GrowthInsight


def get_growth_insights(db: Session) -> List[GrowthInsight]:
    """Generate upsell/cross-sell recommendations from catalog relationships and order data."""
    insights = []

    # Strategy 1: Related product recommendations (catalog-based)
    products = db.query(Product).filter(Product.available == True).all()
    product_map = {p.id: p for p in products}

    for product in products:
        if not product.related_products:
            continue
        for related_id in product.related_products[:2]:
            related = product_map.get(related_id)
            if not related or not related.available:
                continue

            # Cross-category recommendations score higher
            cross_category = product.category != related.category
            confidence = 0.82 if cross_category else 0.68

            insights.append(GrowthInsight(
                recommended_product_id=related.id,
                recommended_product_name=related.name,
                reason=f"Frequently browsed together with '{product.name}'. "
                       f"{'Cross-category pairing increases basket diversity.' if cross_category else 'Same-category complement.'}",
                target_context=f"Customers viewing {product.name} (₹{product.price})",
                estimated_additional_value=related.price,
                confidence_score=round(confidence, 2),
                category=related.category,
            ))

    # Strategy 2: Order-based co-purchase patterns
    orders = db.query(Order).filter(Order.status.in_(["paid", "confirmed", "pending"])).all()
    co_purchase_map = {}
    for order in orders:
        if not order.items_snapshot:
            continue
        product_ids = [item["product_id"] for item in order.items_snapshot]
        for i, pid1 in enumerate(product_ids):
            for pid2 in product_ids[i+1:]:
                pair = tuple(sorted([pid1, pid2]))
                co_purchase_map[pair] = co_purchase_map.get(pair, 0) + 1

    for (pid1, pid2), count in co_purchase_map.items():
        if count < 1:
            continue
        p1, p2 = product_map.get(pid1), product_map.get(pid2)
        if not p1 or not p2:
            continue
        insights.append(GrowthInsight(
            recommended_product_id=p2.id,
            recommended_product_name=p2.name,
            reason=f"Co-purchased {count} time(s) with '{p1.name}'. Strong buying signal.",
            target_context=f"Buyers of {p1.name}",
            estimated_additional_value=p2.price,
            confidence_score=min(0.95, 0.6 + count * 0.15),
            category=p2.category,
        ))

    # Deduplicate by recommended product, keep highest confidence
    seen = {}
    for insight in insights:
        key = insight.recommended_product_id
        if key not in seen or insight.confidence_score > seen[key].confidence_score:
            seen[key] = insight

    result = sorted(seen.values(), key=lambda x: x.confidence_score, reverse=True)
    return result[:20]
