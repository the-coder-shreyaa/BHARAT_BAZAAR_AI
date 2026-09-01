"""
Overview tab: key metrics, category distribution, system status.
"""
import streamlit as st
import httpx
import pandas as pd


def render_overview(api_url: str):
    st.markdown("## 🏠 Dashboard Overview")
    st.markdown("Real-time view of your AI-enabled commerce platform.")

    # Fetch data
    try:
        health = httpx.get(f"{api_url}/", timeout=5).json()
        manifest = httpx.get(f"{api_url}/.well-known/ai-commerce.json", timeout=5).json()
        search_resp = httpx.post(f"{api_url}/api/v1/tools/search_products",
                                 json={"limit": 50}, timeout=5).json()
    except Exception as e:
        st.error(f"❌ Cannot connect to API at {api_url}. Make sure the FastAPI server is running.")
        st.code(f"Error: {e}")
        st.info("💡 Start the API server with: `python run.py`")
        return

    # System Status
    col1, col2, col3, col4 = st.columns(4)

    total_products = manifest.get("total_products", 0)
    categories = manifest.get("supported_categories", [])
    tools_count = len(manifest.get("tools", []))
    razorpay = "✅ Active" if health.get("razorpay_enabled") else "🔸 Simulation"

    with col1:
        st.markdown(f"""<div class="metric-card">
            <h3>{total_products}</h3><p>Total Products</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>{len(categories)}</h3><p>Categories</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>{tools_count}</h3><p>Agent Tools</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3>{razorpay}</h3><p>Payment Gateway</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Category Distribution
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📊 Category Distribution")
        if search_resp.get("success"):
            products = search_resp["data"]["products"]
            if products:
                df = pd.DataFrame(products)
                cat_counts = df["category"].value_counts()
                st.bar_chart(cat_counts)

    with col_b:
        st.markdown("### 🛠️ Available Agent Tools")
        for tool in manifest.get("tools", []):
            st.markdown(f"**`{tool['name']}`** — {tool['description'][:80]}...")

    # System Info
    st.markdown("---")
    st.markdown("### 🔧 System Configuration")
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info(f"**Merchant:** {manifest.get('merchant_name', 'N/A')}")
        st.info(f"**Currency:** {manifest.get('currency', 'INR')}")
        st.info(f"**API Version:** {manifest.get('api_version', '1.0')}")
    with info_col2:
        st.info(f"**LLM Enabled:** {'✅ Yes' if health.get('llm_enabled') else '🔸 Rule-based fallback'}")
        st.info(f"**Payment Mode:** {'Razorpay Sandbox' if health.get('razorpay_enabled') else 'Simulation'}")
        st.info(f"**Discovery URL:** `{api_url}/.well-known/ai-commerce.json`")
