"""
Audit Log tab: filterable audit trail of all agent tool calls.
"""
import streamlit as st
import httpx
import pandas as pd


def render_audit_log(api_url: str):
    st.markdown("## 🔒 Audit Log")
    st.markdown(
        "Complete trail of all AI agent tool calls. Every commerce action is logged "
        "for transparency and debugging."
    )

    # Filters
    col1, col2, col3 = st.columns(3)
    session_filter = col1.text_input("Filter by Session ID", placeholder="e.g., demo-session")
    tool_filter = col2.selectbox(
        "Filter by Tool",
        [
            "All",
            "search_products",
            "get_product",
            "check_stock",
            "create_cart",
            "add_to_cart",
            "create_order",
            "get_order_status",
            "create_checkout",
        ],
    )
    limit = col3.number_input("Max records", min_value=10, max_value=500, value=100, step=10)

    if st.button("🔄 Refresh Logs", use_container_width=False):
        st.rerun()

    try:
        params = {"limit": limit}
        if session_filter:
            params["session_id"] = session_filter
        if tool_filter != "All":
            params["tool_name"] = tool_filter

        resp = httpx.get(f"{api_url}/api/v1/tools/audit/logs", params=params, timeout=10.0)
        data = resp.json()

        if not data.get("success") or not data.get("data"):
            st.info("📭 No audit logs yet. Run the AI Buyer Demo to generate some!")
            return

        logs = data["data"]

        # Summary
        col_a, col_b = st.columns(2)
        col_a.metric("Total Log Entries", len(logs))
        tools_used = len(set(l.get("tool_name", "") for l in logs))
        col_b.metric("Unique Tools Used", tools_used)

        st.divider()

        # Table
        df = pd.DataFrame([
            {
                "Timestamp": l.get("timestamp", "")[:19],
                "Tool": l.get("tool_name", ""),
                "Status": "✅" if l.get("result_status") == "success" else "❌",
                "Input": (l.get("input_summary", "") or "")[:60],
                "Session": (l.get("session_id", "") or "")[:16],
                "Order": (l.get("order_id", "") or "")[:12],
            }
            for l in logs
        ])

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Expandable details
        st.divider()
        st.markdown("### 📋 Log Details")
        for idx, log_entry in enumerate(logs[:20]):
            with st.expander(
                f"{'✅' if log_entry.get('result_status') == 'success' else '❌'} "
                f"{log_entry.get('tool_name', '')} — {log_entry.get('timestamp', '')[:19]}"
            ):
                st.markdown(f"**Tool:** `{log_entry.get('tool_name', '')}`")
                st.markdown(f"**Status:** {log_entry.get('result_status', '')}")
                st.markdown(f"**Session:** `{log_entry.get('session_id', '')}`")
                st.markdown(f"**Input:** {log_entry.get('input_summary', '')}")
                if log_entry.get("order_id"):
                    st.markdown(f"**Order:** `{log_entry['order_id']}`")
                if log_entry.get("details"):
                    st.json(log_entry["details"])

    except httpx.ConnectError:
        st.error(
            "❌ Cannot connect to the API server. Make sure the FastAPI backend is running."
        )
    except Exception as e:
        st.error(f"❌ Error loading audit logs: {str(e)}")
