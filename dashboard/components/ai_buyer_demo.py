"""
AI Buyer Demo tab: interactive NL shopping agent with visual tool-call pipeline.
"""
import streamlit as st
import httpx
import json
import time


EXAMPLE_QUERIES = [
    "Show me blue sneakers under 2000",
    "I want a red kurti for women in cotton",
    "Find me a leather wallet under 1500",
    "Show premium running shoes in black",
    "I need a silk saree under 5000",
    "Find bags under 3000",
    "Suggest formal shoes for men",
]


def render_ai_buyer_demo(api_url: str):
    st.markdown("## 🤖 AI Buyer Agent Demo")
    st.markdown(
        "Enter a natural-language shopping request below. The AI buyer will translate it "
        "into structured commerce tool calls and execute the full purchase flow."
    )

    # Example queries
    st.markdown("**Try an example:**")
    cols = st.columns(3)
    for i, query in enumerate(EXAMPLE_QUERIES[:6]):
        col = cols[i % 3]
        if col.button(f"🔍 {query}", key=f"example_{i}", use_container_width=True):
            st.session_state["buyer_query"] = query

    # Input
    query = st.text_input(
        "🛒 What would you like to buy?",
        value=st.session_state.get("buyer_query", ""),
        placeholder="e.g., Show me blue sneakers under 2000",
        key="buyer_input",
    )

    col1, col2 = st.columns([1, 5])
    run_agent = col1.button("🚀 Run Agent", type="primary", use_container_width=True)
    full_checkout = col2.checkbox("Run full checkout flow (cart → order → payment)", value=True)

    if run_agent and query:
        st.divider()
        st.markdown("### 📋 Agent Execution Pipeline")

        with st.spinner("Agent is processing your request..."):
            try:
                # Step 1: Search Products
                with st.status("🔎 Step 1: Searching products...", expanded=True) as status:
                    search_resp = httpx.post(
                        f"{api_url}/api/v1/tools/search_products",
                        json={"query": query},
                        timeout=10.0,
                    )
                    search_data = search_resp.json()

                    if search_data.get("success") and search_data.get("data"):
                        products = search_data["data"]
                        st.success(f"Found {len(products)} products")
                        for p in products[:5]:
                            st.markdown(
                                f"- **{p['name']}** — ₹{p['price']:,.0f} "
                                f"({'✅ In Stock' if p.get('available') else '❌ Out of Stock'})"
                            )
                        with st.expander("Raw API Response"):
                            st.json(search_data)
                        status.update(label="✅ Step 1: Products found", state="complete")
                    else:
                        st.warning("No products found matching your query.")
                        status.update(label="⚠️ Step 1: No results", state="error")
                        return

                # Pick best match
                selected = products[0]
                product_id = selected["id"]

                # Step 2: Get Product Details
                with st.status(f"📦 Step 2: Getting details for '{selected['name']}'...", expanded=True) as status:
                    detail_resp = httpx.get(
                        f"{api_url}/api/v1/tools/products/{product_id}",
                        timeout=10.0,
                    )
                    detail_data = detail_resp.json()
                    if detail_data.get("success"):
                        p = detail_data["data"]
                        col_a, col_b = st.columns(2)
                        col_a.metric("Price", f"₹{p['price']:,.0f}")
                        col_b.metric("Stock", p.get("stock", "N/A"))
                        if p.get("attributes"):
                            st.markdown(f"**Attributes:** {json.dumps(p['attributes'])}")
                        with st.expander("Raw API Response"):
                            st.json(detail_data)
                        status.update(label="✅ Step 2: Product details retrieved", state="complete")

                # Step 3: Check Stock
                with st.status("📊 Step 3: Checking stock availability...", expanded=True) as status:
                    stock_resp = httpx.get(
                        f"{api_url}/api/v1/tools/products/{product_id}/stock",
                        timeout=10.0,
                    )
                    stock_data = stock_resp.json()
                    if stock_data.get("success"):
                        sd = stock_data["data"]
                        if sd.get("available"):
                            st.success(f"✅ In stock — {sd.get('stock', '?')} units available")
                        else:
                            st.error("❌ Product is out of stock")
                            status.update(label="❌ Step 3: Out of stock", state="error")
                            return
                        with st.expander("Raw API Response"):
                            st.json(stock_data)
                        status.update(label="✅ Step 3: Stock confirmed", state="complete")

                if not full_checkout:
                    st.info("ℹ️ Checkout flow skipped. Enable the checkbox above to run the full flow.")
                    return

                # Step 4: Create Cart
                with st.status("🛒 Step 4: Creating cart...", expanded=True) as status:
                    cart_resp = httpx.post(
                        f"{api_url}/api/v1/tools/cart",
                        json={"session_id": "demo-session-streamlit"},
                        timeout=10.0,
                    )
                    cart_data = cart_resp.json()
                    if cart_data.get("success"):
                        cart_id = cart_data["data"]["id"]
                        st.success(f"Cart created: `{cart_id}`")
                        with st.expander("Raw API Response"):
                            st.json(cart_data)
                        status.update(label="✅ Step 4: Cart created", state="complete")

                # Step 5: Add to Cart
                with st.status("➕ Step 5: Adding product to cart...", expanded=True) as status:
                    add_resp = httpx.post(
                        f"{api_url}/api/v1/tools/cart/{cart_id}/items",
                        json={"product_id": product_id, "quantity": 1},
                        timeout=10.0,
                    )
                    add_data = add_resp.json()
                    if add_data.get("success"):
                        st.success(f"Added **{selected['name']}** × 1 to cart")
                        with st.expander("Raw API Response"):
                            st.json(add_data)
                        status.update(label="✅ Step 5: Item added to cart", state="complete")

                # Step 6: Create Order
                with st.status("📝 Step 6: Creating order...", expanded=True) as status:
                    order_resp = httpx.post(
                        f"{api_url}/api/v1/tools/orders",
                        json={"cart_id": cart_id, "session_id": "demo-session-streamlit"},
                        timeout=10.0,
                    )
                    order_data = order_resp.json()
                    if order_data.get("success"):
                        order_id = order_data["data"]["id"]
                        total = order_data["data"].get("total_amount", 0)
                        st.success(f"Order created: `{order_id}` — Total: ₹{total:,.0f}")
                        with st.expander("Raw API Response"):
                            st.json(order_data)
                        status.update(label="✅ Step 6: Order created", state="complete")

                # Step 7: Checkout
                with st.status("💳 Step 7: Initiating checkout...", expanded=True) as status:
                    checkout_resp = httpx.post(
                        f"{api_url}/api/v1/tools/orders/{order_id}/checkout",
                        timeout=10.0,
                    )
                    checkout_data = checkout_resp.json()
                    if checkout_data.get("success"):
                        cd = checkout_data["data"]
                        st.success("🎉 Checkout initiated!")
                        st.markdown(f"**Payment Mode:** {cd.get('mode', 'simulation')}")
                        if cd.get("payment_link"):
                            st.markdown(f"**Payment Link:** [{cd['payment_link']}]({cd['payment_link']})")
                        if cd.get("razorpay_order_id"):
                            st.markdown(f"**Razorpay Order ID:** `{cd['razorpay_order_id']}`")
                        with st.expander("Raw API Response"):
                            st.json(checkout_data)
                        status.update(label="✅ Step 7: Checkout complete!", state="complete")

                # Summary
                st.divider()
                st.markdown("### 🎉 Purchase Flow Complete!")
                st.balloons()
                summary_cols = st.columns(4)
                summary_cols[0].metric("Product", selected["name"][:20])
                summary_cols[1].metric("Price", f"₹{selected['price']:,.0f}")
                summary_cols[2].metric("Order", order_id[:12] + "...")
                summary_cols[3].metric("Status", "✅ Success")

            except httpx.ConnectError:
                st.error(
                    "❌ Cannot connect to the API server. Make sure the FastAPI backend "
                    "is running at " + api_url
                )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
