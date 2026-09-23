import streamlit as st
import requests

st.set_page_config(page_title="Rules Admin — ComplyErg", page_icon="⚙️", layout="wide")

API_URL = "http://localhost:8000"

user_role = st.session_state.get("user_role", "inspector")
if user_role != "admin":
    st.error("⛔ Access Denied. Rules Administration is restricted to Administrators only.")
    st.stop()

headers = {}
if st.session_state.get("jwt_token"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("⚙️ Legal Metrology Rules Administration")
st.caption("Versioned Rule Engine Management (Rules 6, 7, 9, 10 of Legal Metrology Packaged Commodities Rules 2011).")

tab1, tab2 = st.tabs(["📋 Active Rules Registry", "➕ Add New Legal Rule"])

with tab1:
    st.subheader("Configured Legal Metrology Rules")
    try:
        res = requests.get(f"{API_URL}/rules/", headers=headers)
        if res.status_code == 200:
            rules = res.json()
            if rules:
                for r in rules:
                    col1, col2, col3, col4 = st.columns([1.5, 3, 1, 1])
                    with col1:
                        st.markdown(f"**{r['rule_id_str']}** ({r.get('legal_rule_ref', 'Rule 6')})\n\n*(Severity: {r['severity'].upper()})*")
                    with col2:
                        st.markdown(f"Field: `{r['field']}` | Check: `{r['check_type']}` | Pattern: `{r.get('pattern')}`")
                    with col3:
                        st.markdown(f"Category: `{r.get('category', ['all'])}` | Ver: `{r['version']}`")
                    with col4:
                        is_enabled = r.get("enabled", True)
                        btn_label = "Disable" if is_enabled else "Enable"
                        if st.button(f"{btn_label} {r['rule_id_str']}", key=f"toggle_{r['id']}"):
                            toggle_res = requests.put(
                                f"{API_URL}/rules/{r['rule_id_str']}",
                                json={"enabled": not is_enabled},
                                headers=headers
                            )
                            if toggle_res.status_code == 200:
                                st.success(f"Rule {r['rule_id_str']} updated.")
                                st.rerun()
                            else:
                                st.error(f"Failed to update rule: {toggle_res.text}")
                    st.divider()
            else:
                st.info("No rules found in registry.")
        else:
            st.error(f"Failed to load rules from API ({res.status_code}): {res.text}")
    except Exception as e:
        st.error(f"Error connecting to backend API: {e}")

with tab2:
    st.subheader("Define & Seed New Compliance Rule")
    with st.form("add_rule_form"):
        rule_id_input = st.text_input("Rule ID String (e.g., LM2011-R6-BARCODE)", value="LM2011-R6-BARCODE")
        legal_ref_input = st.text_input("Statutory Reference", value="Rule 6(1)(a)")
        field_input = st.text_input("Target Field Name", value="barcode")
        check_type_input = st.selectbox(
            "Evaluation Check Type",
            [
                "presence", "presence_and_unit", "regex", "date_format",
                "date_order", "keyword_nearby", "script_check", "spatial_prominence",
                "conditional_entity", "min_confidence", "external_verification"
            ]
        )
        pattern_input = st.text_input("Pattern / Regex / Target Keyword", value="^\\d{12,13}$")
        severity_input = st.selectbox("Severity Level", ["critical", "high", "medium", "low", "manual_review"])
        category_input = st.multiselect("Applicable Categories", ["all", "food", "cosmetics", "imported"], default=["all"])
        version_input = st.text_input("Rule Set Version", value="2011")

        submit_rule = st.form_submit_button("Save Rule to Database", type="primary")

        if submit_rule:
            try:
                payload = {
                    "rule_id_str": rule_id_input,
                    "legal_rule_ref": legal_ref_input,
                    "field": field_input,
                    "check_type": check_type_input,
                    "pattern": pattern_input if pattern_input else None,
                    "severity": severity_input,
                    "category": category_input,
                    "version": version_input,
                    "enabled": True
                }
                add_res = requests.post(f"{API_URL}/rules/", json=payload, headers=headers)
                if add_res.status_code in [200, 201]:
                    st.success(f"Successfully added rule '{rule_id_input}'!")
                    st.rerun()
                else:
                    st.error(f"Error ({add_res.status_code}): {add_res.text}")
            except Exception as e:
                st.error(f"Failed to post new rule: {e}")
