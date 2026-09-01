"""
Product Catalog tab: searchable product table with filters.
"""
import streamlit as st
import httpx
import pandas as pd


def render_catalog(api_url: str):
    st.markdown("## 📦 Product Catalog")
    st.markdown("Browse and search the merchant's AI-discoverable product catalog.")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_query = st.text_input("🔍 Search", placeholder="e.g., blue sneakers")
    with col2:
        category = st.selectbox("📂 Category", ["All", "clothing", "shoes", "accessories", "bags"])
    with col3:
        min_price = st.number_input("Min Price (₹)", min_value=0, value=0, step=100)
    with col4:
        max_price = st.number_input("Max Price (₹)", min_value=0, value=5000, step=100)

    # Fetch products
    params = {"limit": 50}
    if search_query:
        params["query"] = search_query
    if category != "All":
        params["category"] = category
    if min_price > 0:
        params["min_price"] = min_price
    if max_price > 0 and max_price < 5000:
        params["max_price"] = max_price

    try:
        resp = httpx.post(f"{api_url}/api/v1/tools/search_products", json=params, timeout=5).json()
    except Exception as e:
        st.error(f"❌ Cannot connect to API: {e}")
        return

    if not resp.get("success"):
        st.warning(f"Search error: {resp.get('error')}")
        return

    products = resp["data"]["products"]
    total = resp["data"]["total_found"]

    st.markdown(f"**{total} products found** — {resp['data']['query_summary']}")

    if not products:
        st.info("No products match your filters. Try adjusting your search.")
        return

    # Product cards
    for i in range(0, len(products), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(products):
                p = products[i + j]
                with col:
                    attrs = p.get("attributes", {})
                    stock_badge = "🟢 In Stock" if p["available"] and p["stock"] > 0 else "🔴 Out of Stock"
                    if p["available"] and 0 < p["stock"] < 5:
                        stock_badge = "🟡 Low Stock"

                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px;
                                padding: 1rem; margin-bottom: 0.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                        <div style="font-size: 0.75rem; color: #888; text-transform: uppercase;">{p['category']}</div>
                        <div style="font-size: 1.05rem; font-weight: 600; margin: 0.3rem 0;">{p['name']}</div>
                        <div style="font-size: 1.3rem; font-weight: 700; color: #667eea;">₹{p['price']:,.0f}</div>
                        <div style="font-size: 0.8rem; margin-top: 0.3rem;">{stock_badge} ({p['stock']} units)</div>
                        <div style="font-size: 0.75rem; color: #666; margin-top: 0.3rem;">
                            {f"Color: {attrs.get('color', 'N/A')} | Brand: {attrs.get('brand', 'N/A')}"}
                        </div>
                        <div style="font-size: 0.7rem; color: #999; margin-top: 0.2rem;">ID: {p['product_id']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # Raw data table
    with st.expander("📊 View as Table"):
        df = pd.DataFrame(products)
        display_cols = ["product_id", "name", "category", "price", "stock", "available"]
        st.dataframe(df[display_cols], use_container_width=True)
