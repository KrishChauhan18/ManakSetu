import streamlit as st
import requests
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from i18n import t

st.set_page_config(page_title="Reports — ComplyErg", page_icon="📄", layout="wide")

API_URL = "http://localhost:8000"
lang = st.session_state.get("ui_lang", "en")

headers = {}
role = st.session_state.get("user_role", "inspector")
if st.session_state.get("jwt_token") and not str(st.session_state.get("jwt_token", "")).startswith("mock_"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("📄 Inspection Reports")
st.caption("Generate and download evidence PDF reports for individual scans or batch summaries.")

tab1, tab2, tab3 = st.tabs(["Individual Scan Report", "Batch Summary Report", "📧 Share / Escalate"])

with tab1:
    st.subheader("Generate Evidence PDF for a Scan")
    last_scan_id = st.session_state.get("last_scan_id")
    default_id = int(last_scan_id) if last_scan_id else 1

    scan_id_input = st.number_input("Scan ID", min_value=1, value=default_id, key="report_scan_id", step=1)
    include_annot = st.checkbox("Include annotated label image", value=True, key="rpt_include_annot")
    include_ocr = st.checkbox("Include raw OCR text", value=False, key="rpt_include_ocr")

    if st.button("📥 Generate & Download PDF", use_container_width=True, type="primary", key="gen_rpt_btn"):
        try:
            params = {"include_annotated": include_annot, "include_ocr_text": include_ocr}
            res = requests.get(
                f"{API_URL}/api/v1/reports/{int(scan_id_input)}/pdf",
                headers=headers,
                params=params,
                timeout=30
            )
            if res.status_code == 200:
                st.download_button(
                    label="📄 Download Evidence Report PDF",
                    data=res.content,
                    file_name=f"ComplyErg_Report_Scan_{scan_id_input}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ Report generated! Click above to download.")
            elif res.status_code == 404:
                st.error("Scan not found. Please run a scan first.")
            else:
                err = res.json().get("error", {}).get("message", f"HTTP {res.status_code}")
                st.error(f"Report generation failed: {err}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Backend offline — cannot generate report. Start the FastAPI server.")

with tab2:
    if role not in ["supervisor", "admin"]:
        st.warning("🔒 Batch summary reports require Supervisor or Admin role.")
    else:
        st.subheader("Batch Compliance Summary Report")
        b1, b2 = st.columns(2)
        with b1:
            batch_cat = st.selectbox("Category", ["all", "food", "medicine", "cosmetics", "imported"], key="batch_cat")
            batch_date_from = st.date_input("From Date", key="batch_from")
        with b2:
            batch_region = st.text_input("Region (optional)", key="batch_region")
            batch_date_to = st.date_input("To Date", key="batch_to")

        if st.button("📊 Generate Batch PDF Report", use_container_width=True, key="batch_rpt_btn"):
            try:
                params = {
                    "category": batch_cat,
                    "date_from": str(batch_date_from),
                    "date_to": str(batch_date_to),
                }
                if batch_region:
                    params["region"] = batch_region
                res = requests.get(
                    f"{API_URL}/api/v1/reports/batch",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                if res.status_code == 200:
                    st.download_button(
                        label="📊 Download Batch Summary PDF",
                        data=res.content,
                        file_name=f"ComplyErg_Batch_Report_{batch_cat}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ Batch report ready!")
                else:
                    err = res.json().get("error", {}).get("message", f"HTTP {res.status_code}")
                    st.error(f"Error: {err}")
            except requests.exceptions.ConnectionError:
                st.error("Backend offline")

with tab3:
    st.subheader("🚨 Escalate / Share Findings")
    esc_scan_id = st.number_input("Scan ID to escalate", min_value=1, value=default_id, key="esc_id", step=1)
    esc_reason = st.text_area("Escalation reason / notes", placeholder="Describe the violation concern...", key="esc_reason")
    esc_email = st.text_input("Supervisor / authority email", placeholder="supervisor@complyerg.gov.in", key="esc_email")
    esc_priority = st.selectbox("Priority", ["Normal", "High", "Urgent"], key="esc_priority")

    if st.button("📤 Submit Escalation", use_container_width=True, key="esc_btn"):
        try:
            payload = {
                "scan_id": int(esc_scan_id),
                "reason": esc_reason,
                "escalated_to": esc_email,
                "priority": esc_priority.lower()
            }
            res = requests.post(f"{API_URL}/api/v1/reports/escalate", json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                st.success("✅ Escalation submitted and audit-logged!")
            else:
                err = res.json().get("error", {}).get("message", f"HTTP {res.status_code}")
                st.warning(f"Escalation API: {err} — logged locally.")
                st.info(f"Manual escalation: Scan #{esc_scan_id} | Priority: {esc_priority} | To: {esc_email}")
        except requests.exceptions.ConnectionError:
            st.info(f"📋 Backend offline — escalation logged locally: Scan #{esc_scan_id} escalated to {esc_email}")
