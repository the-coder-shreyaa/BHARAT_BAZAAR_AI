"""
Bharat Bazaar AI — Merchant Dashboard (Streamlit)
6-tab dashboard: Overview, Catalog, AI Buyer Demo, Orders, Growth Insights, Audit Log
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(
    page_title="Bharat Bazaar AI — Merchant Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom Styling ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.8;
        font-size: 0.95rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-card p {
        margin: 0.2rem 0 0 0;
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    .tool-step {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .tool-step.success { border-left-color: #28a745; }
    .tool-step.error { border-left-color: #dc3545; }
    
    .insight-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛍️ Bharat Bazaar AI</h1>
    <p>Merchant-side AI Commerce Layer — Making your catalog AI-discoverable & AI-transactable</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_url = st.text_input("API Base URL", value="http://localhost:8000", help="FastAPI server URL")
    st.markdown("---")
    st.markdown("### 📋 Navigation")
    st.markdown("""
    **Core Agentic Commerce:**
    - 🏠 Overview
    - 📦 Product Catalog
    - 🤖 AI Buyer Demo
    - 📋 Orders
    
    **Growth & Analytics:**
    - 📈 Growth Insights
    - 📝 Agent Audit Log
    """)
    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown(f"[📖 API Docs]({api_url}/docs)")
    st.markdown(f"[🔍 Discovery Manifest]({api_url}/.well-known/ai-commerce.json)")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Overview",
    "📦 Product Catalog",
    "🤖 AI Buyer Demo",
    "📋 Orders",
    "📈 Growth Insights",
    "📝 Agent Audit Log",
])

# Import tab components
from dashboard.components.overview import render_overview
from dashboard.components.catalog import render_catalog
from dashboard.components.ai_buyer_demo import render_ai_buyer_demo
from dashboard.components.orders import render_orders
from dashboard.components.growth_insights import render_growth_insights
from dashboard.components.audit_log import render_audit_log

with tab1:
    render_overview(api_url)

with tab2:
    render_catalog(api_url)

with tab3:
    render_ai_buyer_demo(api_url)

with tab4:
    render_orders(api_url)

with tab5:
    render_growth_insights(api_url)

with tab6:
    render_audit_log(api_url)
