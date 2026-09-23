import streamlit as st
import requests
import pandas as pd
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from i18n import t

st.set_page_config(page_title="Dashboard — ComplyErg", page_icon="📊", layout="wide")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

API_URL = "http://localhost:8000"
lang = st.session_state.get("ui_lang", "en")

headers = {}
if st.session_state.get("jwt_token") and not str(st.session_state.get("jwt_token", "")).startswith("mock_"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.kpi-value { font-size: 2.4rem; font-weight: 800; margin: 4px 0; }
.kpi-label { font-size: 0.85rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Compliance Intelligence Dashboard")
st.caption("Real-time compliance analytics across all product categories and regions.")

# ─── Filters ───────────────────────────────────────────────────────────────
filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    cat_filter = st.selectbox("Category", ["all", "food", "medicine", "cosmetics", "imported"], key="dash_cat")
with filter_col2:
    date_range = st.selectbox("Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"], key="dash_period")
with filter_col3:
    st.markdown("&nbsp;")
    refresh_btn = st.button("🔄 Refresh Dashboard", use_container_width=True, key="dash_refresh")

# ─── Fetch dashboard data ────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch_dashboard(cat: str):
    try:
        params = {} if cat == "all" else {"category": cat}
        res = requests.get(f"{API_URL}/api/v1/dashboard", headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            rdata = res.json()
            return rdata.get("data", rdata), None
        return None, f"HTTP {res.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Backend offline"
    except Exception as e:
        return None, str(e)

if refresh_btn:
    st.cache_data.clear()

dash_data, dash_error = fetch_dashboard(cat_filter)

if dash_error:
    st.warning(f"⚠️ Dashboard data unavailable: {dash_error}. Running in offline demo mode.")
    # Inject demo data for offline/presentation mode
    dash_data = {
        "total_scans": 1247,
        "compliant_scans": 942,
        "non_compliant_scans": 305,
        "avg_compliance_pct": 82.4,
        "top_violations": [
            {"rule_id": "LM2011_R6_5", "field": "consumer_care", "count": 187, "severity": "critical"},
            {"rule_id": "LM2011_R6_3", "field": "net_quantity", "count": 134, "severity": "high"},
            {"rule_id": "LM2011_R6_1", "field": "manufacturer_name", "count": 98, "severity": "medium"},
            {"rule_id": "DC1945_SCH_H1", "field": "rx_symbol", "count": 76, "severity": "critical"},
            {"rule_id": "LM2011_R6_6", "field": "mfg_date", "count": 65, "severity": "medium"},
        ],
        "compliance_by_category": {"food": 86.1, "medicine": 74.3, "cosmetics": 88.9, "imported": 71.2},
        "scans_last_7_days": 48,
    }

if dash_data:
    total = dash_data.get("total_scans", 0)
    compliant = dash_data.get("compliant_scans", 0)
    non_compliant = dash_data.get("non_compliant_scans", 0)
    avg_pct = dash_data.get("avg_compliance_pct", 0.0)
    scans_7d = dash_data.get("scans_last_7_days", 0)
    compliance_pct = (compliant / total * 100) if total > 0 else avg_pct

    # ─── KPI Row ───
    kpi_cols = st.columns(5)
    kpi_defs = [
        ("total_scans", "🗂️ Total Scans", f"{total:,}", "#3B82F6"),
        ("compliant", "✅ Compliant", f"{compliant:,}", "#10B981"),
        ("non_compliant", "🚨 Violations Found", f"{non_compliant:,}", "#EF4444"),
        ("avg_score", "📊 Avg Compliance", f"{avg_pct:.1f}%", "#F59E0B"),
        ("scans_7d", "📅 Scans (7d)", f"{scans_7d:,}", "#8B5CF6"),
    ]
    for idx, (k, label, val, color) in enumerate(kpi_defs):
        with kpi_cols[idx]:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{val}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns([1.2, 1])

    with chart_col1:
        st.subheader("🔥 Top Rule Violations (Frequency)")
        top_v = dash_data.get("top_violations", [])
        if top_v and HAS_PLOTLY:
            vio_df = pd.DataFrame(top_v)
            color_map = {"critical": "#EF4444", "high": "#F97316", "medium": "#F59E0B", "low": "#22C55E"}
            fig = go.Figure(go.Bar(
                y=[f"{r.get('rule_id','')}: {r.get('field','')}" for r in top_v],
                x=[r.get("count", 0) for r in top_v],
                orientation="h",
                marker=dict(
                    color=[color_map.get(r.get("severity","medium"), "#64748B") for r in top_v],
                    line=dict(width=0)
                ),
                text=[r.get("count", 0) for r in top_v],
                textposition="outside"
            ))
            fig.update_layout(
                plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
                font=dict(color="#E2E8F0", size=12),
                xaxis=dict(gridcolor="#334155", title="Occurrence Count"),
                yaxis=dict(gridcolor="#334155"),
                margin=dict(l=10, r=10, t=10, b=10),
                height=340
            )
            st.plotly_chart(fig, use_container_width=True)
        elif top_v:
            vio_df = pd.DataFrame(top_v)
            st.dataframe(vio_df[["rule_id", "field", "severity", "count"]], use_container_width=True)

    with chart_col2:
        st.subheader("🍕 Compliance Split")
        if HAS_PLOTLY:
            labels = ["Compliant", "Non-Compliant"]
            values = [max(compliant, 1), max(non_compliant, 1)]
            fig2 = go.Figure(go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=["#10B981", "#EF4444"]),
                textfont=dict(size=13, color="#E2E8F0")
            ))
            fig2.add_annotation(
                text=f"{compliance_pct:.1f}%",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=26, color="#E2E8F0", family="Inter"),
                xanchor="center", yanchor="middle"
            )
            fig2.update_layout(
                plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
                font=dict(color="#E2E8F0"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=10, b=10),
                height=340
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    cat_chart_col, breakdown_col = st.columns([1.2, 1])

    with cat_chart_col:
        st.subheader("📂 Compliance by Product Category")
        by_cat = dash_data.get("compliance_by_category", {})
        if by_cat and HAS_PLOTLY:
            cats = list(by_cat.keys())
            vals = list(by_cat.values())
            bar_colors = [("#10B981" if v >= 85 else ("#F59E0B" if v >= 70 else "#EF4444")) for v in vals]
            fig3 = go.Figure(go.Bar(
                x=cats,
                y=vals,
                marker=dict(color=bar_colors, line=dict(width=0)),
                text=[f"{v:.1f}%" for v in vals],
                textposition="outside",
                textfont=dict(color="#E2E8F0")
            ))
            fig3.update_layout(
                plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
                font=dict(color="#E2E8F0"),
                yaxis=dict(title="Avg Compliance %", gridcolor="#334155", range=[0, 110]),
                xaxis=dict(title="Product Category"),
                margin=dict(l=10, r=10, t=10, b=10),
                height=300
            )
            st.plotly_chart(fig3, use_container_width=True)

    with breakdown_col:
        st.subheader("📋 Performance Summary")
        summary_rows = []
        for cat, pct in by_cat.items():
            status_icon = "✅" if pct >= 85 else ("⚠️" if pct >= 70 else "🚨")
            summary_rows.append({"Category": cat.title(), "Avg Score": f"{pct:.1f}%", "Status": status_icon})
        if summary_rows:
            df = pd.DataFrame(summary_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("""
        <div style="background:#1E293B;border:1px solid #334155;border-radius:10px;padding:14px;margin-top:12px;">
            <b style="color:#F1F5F9;">📊 Legend</b><br/>
            <span style="color:#10B981;">✅ ≥ 85% — Excellent</span><br/>
            <span style="color:#F59E0B;">⚠️ 70-84% — Requires Attention</span><br/>
            <span style="color:#EF4444;">🚨 &lt; 70% — Enforcement Action Recommended</span>
        </div>
        """, unsafe_allow_html=True)
