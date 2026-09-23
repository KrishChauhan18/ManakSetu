import streamlit as st
import requests
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from i18n import t

st.set_page_config(page_title="Scan Product — ComplyErg", page_icon="📷", layout="wide")

API_URL = "http://localhost:8000"

lang = st.session_state.get("ui_lang", "en")

st.markdown("""
<style>
.stage-bar { background: #1E293B; border-radius: 8px; padding: 12px 16px; margin: 6px 0; border-left: 4px solid #3B82F6; color: #E2E8F0; font-size: 14px; }
.stage-done { border-left-color: #10B981; }
.stage-active { border-left-color: #F59E0B; }
.violation-critical { background: #1F1215; border: 1px solid #EF4444; border-radius: 8px; padding: 12px; margin: 6px 0; }
.violation-high { background: #1A1409; border: 1px solid #F97316; border-radius: 8px; padding: 12px; margin: 6px 0; }
.violation-medium { background: #1A1A09; border: 1px solid #F59E0B; border-radius: 8px; padding: 12px; margin: 6px 0; }
.score-gauge { text-align: center; font-size: 3.5rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# Auth headers
headers = {}
if st.session_state.get("jwt_token"):
    token = st.session_state["jwt_token"]
    if not token.startswith("mock_"):
        headers["Authorization"] = f"Bearer {token}"

st.title(t("scan_title", lang))
st.caption(t("scan_subtitle", lang))

SAMPLE_DIR = os.path.join(os.getcwd(), "ml", "data", "samples")
SAMPLES = {
    t("grocery_good", lang): (os.path.join(SAMPLE_DIR, "grocery_compliant.jpg"), "food"),
    t("grocery_bad", lang): (os.path.join(SAMPLE_DIR, "grocery_violation.jpg"), "food"),
    t("medicine_good", lang): (os.path.join(SAMPLE_DIR, "medicine_compliant.jpg"), "medicine"),
    t("medicine_bad", lang): (os.path.join(SAMPLE_DIR, "medicine_violation.jpg"), "medicine"),
}

col1, col2 = st.columns([1, 1.1])

with col1:
    st.subheader("1. Input Product Label Photo")

    # Language toggle
    with st.expander(t("language_toggle", lang)):
        chosen_lang = st.radio("Language", ["English", "हिंदी"], index=0 if lang == "en" else 1, key="lang_radio_scan", horizontal=True)
        st.session_state["ui_lang"] = "en" if chosen_lang == "English" else "hi"
        lang = st.session_state["ui_lang"]

    # Input method
    input_method = st.radio(t("input_method", lang), [t("file_upload", lang), t("camera", lang)], horizontal=True)
    uploaded_file = None
    if input_method == t("file_upload", lang):
        uploaded_file = st.file_uploader("Upload Product Label Image (JPG/PNG)", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    else:
        uploaded_file = st.camera_input("Take a photo of the product package label")

    category = st.selectbox(
        t("product_category", lang),
        ["food", "medicine", "cosmetics", "imported", "all"],
        help="Category-specific legal rule sets will be applied (medicine = Drugs & Cosmetics Rules 1945)"
    )

    start_scan = st.button(t("start_scan", lang), type="primary", use_container_width=True, key="btn_scan")

    # ─── Demo Sample Scan ───
    st.markdown("---")
    st.subheader("🎯 " + t("load_sample", lang))
    sample_cols = st.columns(2)
    sample_keys = list(SAMPLES.keys())
    for i, (samp_label, (samp_path, samp_cat)) in enumerate(SAMPLES.items()):
        col_idx = i % 2
        with sample_cols[col_idx]:
            if st.button(samp_label, key=f"sample_{i}", use_container_width=True):
                if os.path.exists(samp_path):
                    st.session_state["demo_sample_path"] = samp_path
                    st.session_state["demo_sample_cat"] = samp_cat
                    st.session_state["trigger_demo"] = True
                    st.rerun()
                else:
                    st.warning("Sample image not found. Run: `python ml/generate_sample_dataset.py` to generate demo images.")

with col2:
    st.subheader("2. Real-time Scan Results & Verdict")

    def run_scan_and_display(file_bytes: bytes, file_name: str, cat: str):
        """Submit scan to /api/v1/scan/upload and display results."""
        STAGE_LABELS = {
            "preprocessing": t("stage_preprocessing", lang),
            "ocr": t("stage_ocr", lang),
            "extraction": t("stage_extraction", lang),
            "rule_check": t("stage_rule_check", lang),
            "done": t("stage_done", lang),
            "failed": "❌ Scan Failed"
        }
        STAGE_ORDER = ["preprocessing", "ocr", "extraction", "rule_check", "done"]
        STAGE_PCT = {"preprocessing": 20, "ocr": 45, "extraction": 70, "rule_check": 90, "done": 100}

        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        # Show a live progress simulation using WebSocket-like polling approach
        # (Streamlit's websocket-client can be used here; we simulate with a progress bar)
        try:
            ws_base = API_URL.replace("http://", "ws://").replace("https://", "wss://")

            # Attempt WebSocket live progress via websocket-client
            try:
                import websocket
                import threading

                progress_stages = []
                ws_done = threading.Event()

                def on_message(ws_obj, message):
                    try:
                        data = json.loads(message)
                        progress_stages.append(data)
                        if data.get("stage") in ["done", "failed"]:
                            ws_done.set()
                    except Exception:
                        pass

                def on_error(ws_obj, error):
                    ws_done.set()

                def on_close(ws_obj, *args):
                    ws_done.set()

                def connect_ws(scan_id_to_watch):
                    ws_obj = websocket.WebSocketApp(
                        f"{ws_base}/api/v1/scan/{scan_id_to_watch}/status-stream",
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close
                    )
                    ws_thread = threading.Thread(target=ws_obj.run_forever, kwargs={"ping_interval": 5})
                    ws_thread.daemon = True
                    ws_thread.start()
                    return ws_obj, ws_thread

                # First get a scan ID by using a quick pre-scan
                progress_placeholder.progress(0, text=STAGE_LABELS["preprocessing"])
            except ImportError:
                # websocket-client not available; will show animated progress bar
                progress_stages = None

            # Upload to API
            files = {"file": (file_name, file_bytes, "image/jpeg")}
            data = {"category": cat}

            with status_placeholder.status(f"⚙️ {t('processing', lang)}", expanded=True) as status:
                status.write(STAGE_LABELS["preprocessing"])
                progress_placeholder.progress(10, text=STAGE_LABELS["preprocessing"])
                time.sleep(0.3)

                # Animate progress while uploading
                for pct, stage_label in [(25, STAGE_LABELS["ocr"]), (55, STAGE_LABELS["extraction"]), (80, STAGE_LABELS["rule_check"])]:
                    status.write(stage_label)
                    progress_placeholder.progress(pct, text=stage_label)
                    time.sleep(0.4)

                res = requests.post(
                    f"{API_URL}/api/v1/scan/upload",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=90
                )

                progress_placeholder.progress(100, text=STAGE_LABELS["done"])
                status.write(STAGE_LABELS["done"])
                status.update(label="✅ Scan complete!", state="complete")

            if res.status_code == 200:
                rdata = res.json()
                scan_data = rdata.get("data", rdata)
                display_results(scan_data)
            else:
                err_body = res.json()
                err_msg = err_body.get("error", {}).get("message", res.text[:300])
                st.error(f"API Error ({res.status_code}): {err_msg}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to FastAPI backend. Start it with: `uvicorn app.main:app --reload --port 8000`")
        except Exception as e:
            st.error(f"Scan error: {str(e)}")

    def display_results(scan_data: dict):
        comp_score = scan_data.get("compliance_pct", 0.0)
        violations = scan_data.get("violations", [])
        label_record = scan_data.get("label_record", {}) or {}
        scan_id = scan_data.get("id")
        category_result = scan_data.get("category", "")

        # Compliance Gauge
        gauge_color = "#10B981" if comp_score == 100 else ("#F59E0B" if comp_score >= 70 else "#EF4444")
        st.markdown(
            f'<div class="score-gauge" style="color:{gauge_color};">{comp_score:.1f}%</div>'
            f'<div style="text-align:center;color:#94A3B8;font-size:14px;margin-bottom:8px;">{t("compliance_score", lang)}</div>',
            unsafe_allow_html=True
        )
        st.progress(int(comp_score) / 100)

        if comp_score == 100:
            st.success("✅ **FULLY COMPLIANT** — All mandatory statutory declarations satisfy legal specifications.")
        elif comp_score >= 70:
            st.warning(f"⚠️ **PARTIALLY COMPLIANT** ({len(violations)} violation(s) detected)")
        else:
            st.error(f"🚨 **NON-COMPLIANT** — {len(violations)} critical statutory violation(s) detected.")

        # Medicine Disclaimer
        if category_result == "medicine":
            st.warning("⚖️ **STATUTORY NOTICE**: Automated preliminary check — not a substitute for regulatory/legal review under Drugs and Cosmetics Rules, 1945.")

        # Annotated Label Image
        ann_url = scan_data.get("annotated_image_url")
        if ann_url:
            ann_full = f"{API_URL}{ann_url}"
            img_res = requests.get(ann_full, headers=headers, timeout=10)
            if img_res.status_code == 200:
                st.image(img_res.content, caption="📍 Explainability Map: Green = PASS, Red = FAIL, Amber = REVIEW", use_container_width=True)

        # PDF Download
        if scan_id:
            pdf_res = requests.get(f"{API_URL}/api/v1/reports/{scan_id}/pdf", headers=headers, timeout=15)
            if pdf_res.status_code == 200:
                st.download_button(
                    label=t("download_pdf", lang),
                    data=pdf_res.content,
                    file_name=f"ComplyErg_Inspection_Report_{scan_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            st.session_state["last_scan_id"] = scan_id

        # Extracted Declarations Table
        if label_record:
            st.markdown(f"### 📋 {t('extracted_fields', lang)}")
            rows = []
            skip_fields = {"raw_ocr_text", "quality_assessment", "language_detected", "category"}
            for fkey, fval in label_record.items():
                if fkey in skip_fields:
                    continue
                if isinstance(fval, dict):
                    val_str = fval.get("value", "MISSING") or "MISSING"
                    unit = fval.get("unit", "")
                    conf_pct = f"{fval.get('confidence', 0.0)*100:.0f}%"
                    src = (fval.get("source", "N/A") or "N/A").upper()
                    overridden = "✏️" if fval.get("overridden") else ""
                    rows.append({
                        "Declaration Field": fkey.replace("_", " ").title(),
                        "Extracted Value": f"{val_str} {unit}".strip() or "MISSING",
                        "Confidence": conf_pct,
                        "Source": src,
                        "Override": overridden
                    })
            if rows:
                st.dataframe(rows, use_container_width=True, hide_index=True)

        # Violations
        if violations:
            st.markdown(f"### 🚨 {t('violations', lang)}")
            for v in violations:
                sev = v.get("severity", "medium").lower()
                css_class = f"violation-{sev}"
                icon = "🔴" if sev in ["critical", "high"] else "🟡"
                rule_id = v.get("rule_id", "")
                field = v.get("field", "")
                msg = v.get("message", "")
                rec = v.get("recommendation", "")
                law = v.get("source_law", "")
                legal_ref = v.get("legal_rule_ref", "")
                st.markdown(
                    f'<div class="{css_class}">'
                    f'{icon} <b>[{sev.upper()}] {rule_id} — {field}</b><br/>'
                    f'<span style="color:#CBD5E1;">{msg}</span><br/>'
                    f'<span style="color:#6EE7B7;font-size:13px;">📖 {law} ({legal_ref})</span><br/>'
                    f'<span style="color:#FCD34D;font-size:13px;">👉 <b>Remedy:</b> {rec}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.success("✅ No statutory rule violations detected.")

    # ─── Trigger Demo Sample ────────────────────────────────────────────────
    if st.session_state.get("trigger_demo"):
        st.session_state["trigger_demo"] = False
        samp_path = st.session_state.get("demo_sample_path")
        samp_cat = st.session_state.get("demo_sample_cat", "food")
        if samp_path and os.path.exists(samp_path):
            with open(samp_path, "rb") as f:
                demo_bytes = f.read()
            st.info(f"📦 Running demo scan: `{os.path.basename(samp_path)}` (Category: {samp_cat.upper()})")
            run_scan_and_display(demo_bytes, os.path.basename(samp_path), samp_cat)

    # ─── Real Upload Scan ───────────────────────────────────────────────────
    elif start_scan and uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = getattr(uploaded_file, "name", "label.jpg") or "label.jpg"
        run_scan_and_display(file_bytes, file_name, category)

    elif start_scan and uploaded_file is None:
        st.warning("⚠️ Please upload or capture a label image first.")
