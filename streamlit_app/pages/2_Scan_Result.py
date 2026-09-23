import streamlit as st
import requests
import os

st.set_page_config(page_title="Scan Result Detail — ComplyErg", page_icon="🔍", layout="wide")

API_URL = "http://localhost:8000"

user_role = st.session_state.get("user_role", "inspector")
headers = {}
if st.session_state.get("jwt_token"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("🔍 Scan Result Deep-Dive & Field Override")
st.caption("Inspect spatial bounding box localizations, download evidence PDF reports, and submit supervisor field corrections.")

scan_id = st.number_input("Enter Scan ID", min_value=1, value=st.session_state.get("last_scan_id", 1), step=1)

def draw_bounding_boxes(image_path: str, label_record: dict):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        from PIL import Image, ImageDraw
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        field_colors = {
            "manufacturer": "#3B82F6",
            "mrp": "#10B981",
            "net_quantity": "#F59E0B",
            "mfg_date": "#8B5CF6",
            "expiry_date": "#EC4899",
            "consumer_care": "#06B6D4",
            "batch_number": "#64748B"
        }

        if label_record:
            for fkey, fval in label_record.items():
                if isinstance(fval, dict) and fval.get("bbox"):
                    bbox = fval["bbox"]
                    if len(bbox) == 4 and sum(bbox) > 0:
                        color = field_colors.get(fkey, "#EF4444")
                        draw.rectangle(bbox, outline=color, width=3)
                        draw.text((bbox[0], max(0, bbox[1] - 12)), fkey.replace("_", " "), fill=color)
        return img
    except Exception:
        return None

try:
    res = requests.get(f"{API_URL}/scan/{scan_id}", headers=headers)
    if res.status_code == 200:
        scan = res.json()
        
        st.subheader(f"Scan #{scan['id']} Details (Category: {scan['category'].upper()})")
        
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("### 🖼️ Label Image & Visual Localization")
            img_with_boxes = draw_bounding_boxes(scan["image_path"], scan.get("label_record"))
            if img_with_boxes:
                st.image(img_with_boxes, caption=f"Bounding Box Localization — Scan #{scan['id']}", use_container_width=True)
            elif scan.get("image_path") and os.path.exists(scan["image_path"]):
                st.image(scan["image_path"], caption=f"Scan #{scan['id']}", use_container_width=True)
            else:
                st.warning("Label image snapshot unavailable.")

        with col2:
            comp_pct = scan["compliance_pct"]
            st.metric("Overall Compliance Score", f"{comp_pct:.1f}%")
            st.progress(int(comp_pct) / 100)

            # PDF Download Button
            pdf_url = f"{API_URL}/reports/{scan['id']}/pdf"
            try:
                pdf_res = requests.get(pdf_url, headers=headers)
                if pdf_res.status_code == 200:
                    st.download_button(
                        label="📄 Download Statutory PDF Evidence Report",
                        data=pdf_res.content,
                        file_name=f"ComplyErg_Inspection_Report_Scan_{scan['id']}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
            except Exception:
                st.info("PDF report download pending.")

            st.markdown("### 🚨 Identified Rule Violations")
            violations = scan.get("violations", [])
            if violations:
                for v in violations:
                    st.error(f"**[{v['severity'].upper()}] {v['rule_id']} — {v['field']}**\n\n{v['message']}\n\n*Statutory Ref:* {v.get('legal_rule_ref', 'Rule 6')} | *Rec:* {v.get('recommendation', 'N/A')}")
            else:
                st.success("No violations found. Package satisfies Rule 6 mandatory requirements.")

            st.markdown("### 📋 Extracted Label Declarations")
            st.json(scan.get("label_record", {}))

            # Supervisor Field Override Form
            if user_role in ["supervisor", "admin"]:
                st.markdown("---")
                st.markdown("### ✍️ Supervisor Field Correction & Audit Override")
                st.caption("Supervisors and Admins can override mis-extracted fields. Overrides re-evaluate legal rules and log to AuditLog.")
                
                label_rec = scan.get("label_record", {})
                field_options = list(label_rec.keys()) if label_rec else [
                    "commodity_name", "net_quantity", "manufacturer", "packer", "importer",
                    "mrp", "mfg_date", "expiry_date", "fssai_license", "consumer_care", "batch_number"
                ]

                with st.form("supervisor_override_form"):
                    target_field = st.selectbox("Select Declaration Field to Correct", field_options)
                    current_val = label_rec.get(target_field, {})
                    curr_str = current_val.get("value", "") if isinstance(current_val, dict) else str(current_val)
                    st.text(f"Current Value: {curr_str}")

                    new_val_input = st.text_input("Corrected Field Value")
                    override_reason = st.text_input("Mandatory Reason for Override (Logged to Audit Trail)")
                    
                    submit_override = st.form_submit_button("Submit Field Correction & Re-evaluate")

                    if submit_override:
                        if not override_reason or len(override_reason.strip()) == 0:
                            st.error("A mandatory reason must be provided for audit compliance.")
                        elif not new_val_input:
                            st.error("New field value cannot be empty.")
                        else:
                            try:
                                o_res = requests.patch(
                                    f"{API_URL}/scan/{scan_id}/override",
                                    json={
                                        "field": target_field,
                                        "new_value": new_val_input,
                                        "reason": override_reason
                                    },
                                    headers=headers
                                )
                                if o_res.status_code == 200:
                                    st.success(f"Field '{target_field}' corrected successfully! Audit log entry generated.")
                                    st.rerun()
                                else:
                                    st.error(f"Override failed ({o_res.status_code}): {o_res.text}")
                            except Exception as e:
                                st.error(f"Error connecting to backend API: {e}")
            else:
                st.info("ℹ️ Login as Supervisor or Admin to perform field corrections and audit overrides.")

    elif res.status_code == 403:
        st.error("⛔ Access Denied. Inspectors can only view their own scan results.")
    else:
        st.error(f"Scan #{scan_id} not found.")
except Exception as e:
    st.error(f"Could not connect to FastAPI server: {e}")
