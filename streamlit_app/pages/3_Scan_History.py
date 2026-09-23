import streamlit as st
import requests
import pandas as pd
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from i18n import t

st.set_page_config(page_title="Scan History — ComplyErg", page_icon="📁", layout="wide")

API_URL = "http://localhost:8000"
lang = st.session_state.get("ui_lang", "en")

headers = {}
if st.session_state.get("jwt_token") and not str(st.session_state.get("jwt_token", "")).startswith("mock_"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("📁 Scan History & Audit Log")
st.caption("View, filter, and export all historical label compliance scan records.")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    cat_f = st.selectbox("Category", ["all", "food", "medicine", "cosmetics", "imported"], key="hist_cat")
with filter_col2:
    verdict_f = st.selectbox("Verdict", ["all", "COMPLIANT", "PARTIALLY_COMPLIANT", "NON_COMPLIANT"], key="hist_verdict")
with filter_col3:
    page_size = st.selectbox("Per Page", [10, 25, 50], key="hist_ps")
with filter_col4:
    page_num = st.number_input("Page", min_value=1, value=1, key="hist_page")

@st.cache_data(ttl=30, show_spinner=False)
def fetch_scans(cat, verdict, page, size):
    try:
        params = {"page": page, "page_size": size}
        if cat != "all":
            params["category"] = cat
        if verdict != "all":
            params["verdict"] = verdict
        res = requests.get(f"{API_URL}/api/v1/scan/history", headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            rdata = res.json()
            return rdata.get("data", rdata), None
        return None, f"HTTP {res.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Backend offline"
    except Exception as e:
        return None, str(e)

refresh_col, export_col = st.columns([1, 5])
with refresh_col:
    if st.button("🔄 Refresh", key="hist_refresh"):
        st.cache_data.clear()

scan_data, err = fetch_scans(cat_f, verdict_f, page_num, page_size)

if err:
    st.warning(f"⚠️ {err} — showing offline demo data.")
    scan_data = {
        "total": 3,
        "items": [
            {"id": 101, "filename": "biscuit_pack.jpg", "category": "food", "verdict": "NON_COMPLIANT", "compliance_pct": 62.5, "violation_count": 3, "risk_score": 0.78, "created_at": "2024-01-15 10:32"},
            {"id": 102, "filename": "paracetamol_strip.jpg", "category": "medicine", "verdict": "PARTIALLY_COMPLIANT", "compliance_pct": 85.0, "violation_count": 1, "risk_score": 0.44, "created_at": "2024-01-15 11:05"},
            {"id": 103, "filename": "mango_juice.jpg", "category": "food", "verdict": "COMPLIANT", "compliance_pct": 100.0, "violation_count": 0, "risk_score": 0.12, "created_at": "2024-01-15 12:30"},
        ]
    }

if scan_data:
    items = scan_data.get("items", [])
    total = scan_data.get("total", len(items))
    st.caption(f"Showing {len(items)} of {total} records")

    if items:
        rows = []
        for scan in items:
            verdict = scan.get("verdict", "")
            v_icon = "✅" if verdict == "COMPLIANT" else ("⚠️" if verdict == "PARTIALLY_COMPLIANT" else "🚨")
            risk = scan.get("risk_score", 0.0)
            risk_icon = "🔴" if risk >= 0.7 else ("🟡" if risk >= 0.4 else "🟢")
            rows.append({
                "ID": scan.get("id", ""),
                "File": scan.get("filename", ""),
                "Category": (scan.get("category") or "").title(),
                "Verdict": f"{v_icon} {verdict}",
                "Compliance %": f"{scan.get('compliance_pct', 0):.1f}%",
                "Violations": scan.get("violation_count", 0),
                "Risk": f"{risk_icon} {risk:.2f}",
                "Date": scan.get("created_at", ""),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Scan Detail Drill-down
        selected_id = st.number_input("View scan ID details:", min_value=1, key="hist_detail_id", step=1)
        if st.button("🔍 Load Scan Detail", key="hist_detail_btn"):
            try:
                res = requests.get(f"{API_URL}/api/v1/scan/{int(selected_id)}", headers=headers, timeout=10)
                if res.status_code == 200:
                    rdata = res.json()
                    detail = rdata.get("data", rdata)
                    viols = detail.get("violations", [])
                    st.subheader(f"Scan #{selected_id} — Detail")
                    if viols:
                        st.markdown("**Violations:**")
                        for v in viols:
                            sev = v.get("severity", "medium")
                            color = {"critical": "#EF4444", "high": "#F97316", "medium": "#F59E0B"}.get(sev, "#94A3B8")
                            st.markdown(
                                f'<div style="border:1px solid {color};border-radius:8px;padding:10px;margin:4px 0;">'
                                f'<b style="color:{color};">[{sev.upper()}] {v.get("rule_id","")}</b> — {v.get("field","")}<br/>'
                                f'<span style="color:#CBD5E1;">{v.get("message","")}</span><br/>'
                                f'<span style="color:#6EE7B7;font-size:12px;">{v.get("source_law","")}: {v.get("legal_rule_ref","")}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.success("No violations — fully compliant!")
                else:
                    st.error(f"Not found: HTTP {res.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Backend offline")

        # Export CSV
        csv_data = df.to_csv(index=False)
        st.download_button(
            "⬇️ Export to CSV",
            data=csv_data,
            file_name="complyerg_scan_history.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No scans found matching current filters.")
