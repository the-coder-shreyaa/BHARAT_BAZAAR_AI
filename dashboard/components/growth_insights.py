"""
Growth Insights tab: upsell/cross-sell recommendations with confidence scores.
"""
import streamlit as st
import httpx


def render_growth_insights(api_url: str):
    st.markdown("## 📈 AI Growth Insights")
    st.markdown(
        "Smart recommendations powered by catalog relationships and purchase patterns. "
        "These suggestions help merchants optimize their AI commerce channel."
    )

    if st.button("🔄 Refresh Insights", use_container_width=False):
        st.rerun()

    try:
        resp = httpx.get(f"{api_url}/api/v1/tools/growth/insights", timeout=10.0)
        data = resp.json()

        if not data.get("success") or not data.get("data"):
            st.info(
                "💡 No insights available yet. Insights are generated from catalog "
                "relationships and order history."
            )
            return

        insights = data["data"]

        # Summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Insights", len(insights))
        upsell = sum(1 for i in insights if i.get("type") == "upsell")
        col2.metric("Upsell", upsell)
        cross_sell = sum(1 for i in insights if i.get("type") == "cross_sell")
        col3.metric("Cross-sell", cross_sell)

        st.divider()

        # Insight type filter
        insight_type = st.selectbox(
            "Filter by type",
            ["All", "upsell", "cross_sell"],
            format_func=lambda x: {"All": "📊 All", "upsell": "⬆️ Upsell", "cross_sell": "🔗 Cross-sell"}.get(x, x),
        )

        filtered = insights
        if insight_type != "All":
            filtered = [i for i in insights if i.get("type") == insight_type]

        if not filtered:
            st.info(f"No {insight_type} insights available.")
            return

        # Render insight cards
        for idx, insight in enumerate(filtered):
            with st.container():
                icon = "⬆️" if insight.get("type") == "upsell" else "🔗"
                st.markdown(f"### {icon} {insight.get('recommended_product', 'Product')}")

                col_a, col_b, col_c = st.columns(3)
                confidence = insight.get("confidence", 0)
                col_a.metric("Confidence", f"{confidence:.0%}")
                col_b.metric("Est. Value", f"₹{insight.get('estimated_value', 0):,.0f}")
                col_c.metric("Type", insight.get("type", "").replace("_", " ").title())

                st.markdown(f"**💡 Reason:** {insight.get('reason', 'N/A')}")
                st.markdown(f"**🎯 Target Context:** {insight.get('target_context', 'N/A')}")

                if insight.get("source_product"):
                    st.markdown(f"**📦 Source Product:** {insight['source_product']}")

                # Confidence bar
                bar_color = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.4 else "🔴"
                st.progress(min(confidence, 1.0))
                st.caption(f"{bar_color} Confidence: {confidence:.1%}")

                st.divider()

    except httpx.ConnectError:
        st.error(
            "❌ Cannot connect to the API server. Make sure the FastAPI backend is running."
        )
    except Exception as e:
        st.error(f"❌ Error loading insights: {str(e)}")
