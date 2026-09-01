"""
Orders tab: order list with status badges, detail view with items and payment info.
"""
import streamlit as st
import httpx
import pandas as pd


STATUS_BADGES = {
    "pending": "🟡 Pending",
    "confirmed": "🔵 Confirmed",
    "paid": "🟢 Paid",
    "failed": "🔴 Failed",
    "cancelled": "⚫ Cancelled",
}


def render_orders(api_url: str):
    st.markdown("## 📋 Orders")
    st.markdown("View all orders placed through the AI commerce layer.")

    # Refresh button
    if st.button("🔄 Refresh Orders", use_container_width=False):
        st.rerun()

    try:
        resp = httpx.get(f"{api_url}/api/v1/tools/orders", timeout=10.0)
        data = resp.json()

        if not data.get("success") or not data.get("data"):
            st.info("📭 No orders yet. Use the AI Buyer Demo to create orders!")
            return

        orders = data["data"]

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Orders", len(orders))
        paid = sum(1 for o in orders if o.get("status") == "paid")
        col2.metric("Paid", paid)
        pending = sum(1 for o in orders if o.get("status") == "pending")
        col3.metric("Pending", pending)
        total_rev = sum(o.get("total_amount", 0) for o in orders if o.get("status") == "paid")
        col4.metric("Revenue", f"₹{total_rev:,.0f}")

        st.divider()

        # Status filter
        status_filter = st.selectbox(
            "Filter by status",
            ["All"] + list(STATUS_BADGES.keys()),
            format_func=lambda x: STATUS_BADGES.get(x, "📊 All"),
        )

        filtered = orders
        if status_filter != "All":
            filtered = [o for o in orders if o.get("status") == status_filter]

        if not filtered:
            st.info(f"No orders with status: {status_filter}")
            return

        # Orders table
        df = pd.DataFrame([
            {
                "Order ID": o.get("id", "")[:12] + "...",
                "Full ID": o.get("id", ""),
                "Status": STATUS_BADGES.get(o.get("status", ""), o.get("status", "")),
                "Total": f"₹{o.get('total_amount', 0):,.0f}",
                "Created": o.get("created_at", "")[:19],
                "Session": o.get("session_id", "")[:16],
            }
            for o in filtered
        ])

        st.dataframe(
            df[["Order ID", "Status", "Total", "Created", "Session"]],
            use_container_width=True,
            hide_index=True,
        )

        # Detail view
        st.divider()
        st.markdown("### 🔍 Order Detail")
        order_ids = {o.get("id", "")[:12] + "...": o.get("id", "") for o in filtered}
        selected_label = st.selectbox("Select an order", list(order_ids.keys()))

        if selected_label:
            full_id = order_ids[selected_label]
            detail_resp = httpx.get(
                f"{api_url}/api/v1/tools/orders/{full_id}", timeout=10.0
            )
            detail = detail_resp.json()
            if detail.get("success") and detail.get("data"):
                od = detail["data"]
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Status", STATUS_BADGES.get(od.get("status", ""), od.get("status", "")))
                col_b.metric("Total", f"₹{od.get('total_amount', 0):,.0f}")
                col_c.metric("Currency", od.get("currency", "INR"))

                st.markdown(f"**Order ID:** `{od.get('id', '')}`")
                st.markdown(f"**Cart ID:** `{od.get('cart_id', '')}`")
                st.markdown(f"**Session:** `{od.get('session_id', '')}`")
                if od.get("razorpay_order_id"):
                    st.markdown(f"**Razorpay Order:** `{od['razorpay_order_id']}`")
                if od.get("razorpay_payment_id"):
                    st.markdown(f"**Razorpay Payment:** `{od['razorpay_payment_id']}`")
                st.markdown(f"**Created:** {od.get('created_at', '')}")
                st.markdown(f"**Updated:** {od.get('updated_at', '')}")

                with st.expander("📦 Raw Order Data"):
                    st.json(detail)

    except httpx.ConnectError:
        st.error(
            "❌ Cannot connect to the API server. Make sure the FastAPI backend is running."
        )
    except Exception as e:
        st.error(f"❌ Error loading orders: {str(e)}")
