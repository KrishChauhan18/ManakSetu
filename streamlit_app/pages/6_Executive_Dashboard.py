import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Analytics Dashboard — ComplyErg", page_icon="📊", layout="wide")

API_URL = "http://localhost:8000"

# Role Guard (Supervisor & Admin Only)
user_role = st.session_state.get("user_role", "inspector")
if user_role not in ["supervisor", "admin"]:
    st.error("⛔ Access Denied. Executive Dashboard analytics are restricted to Supervisors and Admins.")
    st.stop()

headers = {}
if st.session_state.get("jwt_token"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("📊 Executive Analytics & Officer Risk Dashboard")
st.caption("Real-time compliance analytics, historical violation trends, and ML Model 3 inspection risk rankings.")

try:
    # 1. Fetch Stats
    stats_res = requests.get(f"{API_URL}/dashboard/stats", headers=headers)
    if stats_res.status_code == 200:
        stats = stats_res.json()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Scans", stats.get("total_scans", 0))
        col2.metric("Overall Compliance %", f"{stats.get('overall_compliance_pct', 100.0):.1f}%")
        sev = stats.get("severity_breakdown", {})
        col3.metric("Critical Violations", sev.get("critical", 0))
        col4.metric("High/Med Violations", sev.get("high", 0) + sev.get("medium", 0))

    st.divider()

    col_left, col_right = st.columns([1.2, 1])

    # 2. Compliance Trend Line Chart
    with col_left:
        st.subheader("📈 Compliance Trend Over Time")
        trend_res = requests.get(f"{API_URL}/dashboard/trend?days=30", headers=headers)
        if trend_res.status_code == 200:
            t_data = trend_res.json().get("trend", [])
            if t_data:
                df_trend = pd.DataFrame(t_data)
                fig_trend = px.line(
                    df_trend, x="date", y="avg_compliance_pct",
                    title="Daily Average Compliance Score (%)",
                    markers=True, line_shape="spline",
                    labels={"avg_compliance_pct": "Compliance %", "date": "Date"}
                )
                fig_trend.update_traces(line_color="#3B82F6", line_width=3)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No trend data logged yet.")

    # 3. Top Violations Bar Chart
    with col_right:
        st.subheader("📊 Most Frequent Rule Violations")
        top_res = requests.get(f"{API_URL}/dashboard/top-violations?limit=5", headers=headers)
        if top_res.status_code == 200:
            v_data = top_res.json()
            if v_data:
                df_top = pd.DataFrame(v_data)
                fig_top = px.bar(
                    df_top, x="rule_id", y="count", color="severity",
                    title="Top Rule Violation Frequency by Severity",
                    color_discrete_map={"critical": "#EF4444", "high": "#F97316", "medium": "#F59E0B", "low": "#3B82F6"},
                    labels={"count": "Occurrences", "rule_id": "Rule ID"}
                )
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("No violations logged yet.")

    st.divider()

    col_mfr, col_risk = st.columns([1, 1.2])

    # 4. Manufacturer Ranking Table
    with col_mfr:
        st.subheader("🏢 Manufacturer Compliance Ranking")
        mfr_res = requests.get(f"{API_URL}/dashboard/manufacturer-ranking", headers=headers)
        if mfr_res.status_code == 200:
            mfr_data = mfr_res.json()
            if mfr_data:
                df_mfr = pd.DataFrame(mfr_data)
                st.dataframe(df_mfr, use_container_width=True)
            else:
                st.info("No manufacturer records available.")

    # 5. Officer Priority Risk Matrix (Model 3)
    with col_risk:
        st.subheader("🚨 Inspection Priority Matrix (Model 3 Risk Scorer)")
        risk_res = requests.get(f"{API_URL}/dashboard/risk-priority", headers=headers)
        if risk_res.status_code == 200:
            risk_data = risk_res.json()
            if risk_data:
                df_risk = pd.DataFrame(risk_data)
                st.dataframe(df_risk, use_container_width=True)
            else:
                st.info("No risk records calculated yet.")

except Exception as e:
    st.error(f"Could not connect to Analytics API: {e}")
