import streamlit as st
import requests
import pandas as pd
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from i18n import t

st.set_page_config(page_title="Rules Engine — ComplyErg", page_icon="⚖️", layout="wide")

API_URL = "http://localhost:8000"
lang = st.session_state.get("ui_lang", "en")

headers = {}
role = st.session_state.get("user_role", "inspector")
if st.session_state.get("jwt_token") and not str(st.session_state.get("jwt_token", "")).startswith("mock_"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("⚖️ Compliance Rules Engine")
st.caption("View and manage the deterministic legal rule sets (Legal Metrology 2011 + Drugs & Cosmetics 1945).")

if role not in ["supervisor", "admin"]:
    st.warning("🔒 You are in read-only view. Only Supervisors and Admins can modify rules.")

tab1, tab2 = st.tabs(["📋 View Rules", "✏️ Edit / Add Rule"])

with tab1:
    f1, f2, f3 = st.columns(3)
    with f1:
        cat_flt = st.selectbox("Category Filter", ["all", "food", "medicine", "cosmetics", "all"], key="rules_cat")
    with f2:
        src_flt = st.selectbox("Source Law", ["All", "Legal Metrology 2011", "Drugs & Cosmetics 1945"], key="rules_src")
    with f3:
        page_n = st.number_input("Page", min_value=1, value=1, key="rules_page")

    @st.cache_data(ttl=120, show_spinner=False)
    def fetch_rules(cat, page):
        try:
            params = {"page": page, "page_size": 25}
            if cat != "all":
                params["category"] = cat
            res = requests.get(f"{API_URL}/api/v1/rules", headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                rdata = res.json()
                return rdata.get("data", rdata), None
            return None, f"HTTP {res.status_code}"
        except requests.exceptions.ConnectionError:
            return None, "Backend offline"
        except Exception as e:
            return None, str(e)

    if st.button("🔄 Refresh Rules", key="rules_refresh"):
        st.cache_data.clear()

    rules_data, rules_err = fetch_rules(cat_flt, page_n)

    if rules_err:
        st.warning(f"⚠️ {rules_err} — showing offline demo rules.")
        rules_data = {
            "items": [
                {"id": 1, "rule_id_str": "LM2011_R6_1", "field": "manufacturer_name", "check_type": "exists", "severity": "critical", "source_law": "Legal Metrology 2011", "legal_rule_ref": "Rule 6(1)(a)", "category": ["all"], "enabled": True},
                {"id": 2, "rule_id_str": "LM2011_R6_2", "field": "net_quantity", "check_type": "exists_and_unit", "severity": "critical", "source_law": "Legal Metrology 2011", "legal_rule_ref": "Rule 6(1)(b)", "category": ["all"], "enabled": True},
                {"id": 3, "rule_id_str": "LM2011_R6_3", "field": "mrp", "check_type": "mrp_format", "severity": "critical", "source_law": "Legal Metrology 2011", "legal_rule_ref": "Rule 6(1)(f)", "category": ["all"], "enabled": True},
                {"id": 4, "rule_id_str": "DC1945_SCH_H", "field": "rx_symbol", "check_type": "rx_check", "severity": "critical", "source_law": "Drugs & Cosmetics 1945", "legal_rule_ref": "Schedule H", "category": ["medicine"], "enabled": True},
                {"id": 5, "rule_id_str": "DC1945_SCH_H1", "field": "warning_box", "check_type": "exists", "severity": "critical", "source_law": "Drugs & Cosmetics 1945", "legal_rule_ref": "Schedule H1", "category": ["medicine"], "enabled": True},
            ]
        }

    items = rules_data.get("items", []) if rules_data else []
    if src_flt != "All":
        items = [r for r in items if r.get("source_law", "") == src_flt]

    if items:
        rows = [{
            "ID": r.get("id"),
            "Rule ID": r.get("rule_id_str", ""),
            "Field": r.get("field", ""),
            "Check Type": r.get("check_type", ""),
            "Severity": r.get("severity", ""),
            "Source Law": r.get("source_law", ""),
            "Legal Ref": r.get("legal_rule_ref", ""),
            "Category": ", ".join(r.get("category", ["all"])),
            "Active": "✅" if r.get("enabled", True) else "❌"
        } for r in items]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No rules found.")

with tab2:
    if role not in ["supervisor", "admin"]:
        st.error("❌ Insufficient permissions. Supervisor or Admin role required to modify rules.")
    else:
        st.subheader("Add / Edit Compliance Rule")

        op_col, _ = st.columns([1, 2])
        with op_col:
            operation = st.radio("Operation", ["Add New Rule", "Toggle Enable/Disable", "Delete Rule"], horizontal=True, key="rules_op")

        if operation == "Add New Rule":
            with st.form("add_rule_form"):
                r1, r2 = st.columns(2)
                with r1:
                    rid = st.text_input("Rule ID String", placeholder="LM2011_R6_X")
                    field = st.text_input("Field Name", placeholder="net_quantity")
                    check = st.selectbox("Check Type", ["exists", "exists_and_unit", "mrp_format", "date_format", "min_size", "rx_check", "warning_text_exists", "bilingual_check"])
                    sev = st.selectbox("Severity", ["critical", "high", "medium", "low"])
                with r2:
                    src_law = st.selectbox("Source Law", ["Legal Metrology 2011", "Drugs & Cosmetics 1945"])
                    legal_ref = st.text_input("Legal Rule Reference", placeholder="Rule 6(1)(b)")
                    cat_opts = st.multiselect("Applicable Categories", ["all", "food", "medicine", "cosmetics", "imported"], default=["all"])
                    pattern = st.text_input("Pattern (optional)", placeholder="Regex or threshold value")
                submitted = st.form_submit_button("➕ Add Rule", use_container_width=True)
                if submitted:
                    payload = {
                        "rule_id_str": rid,
                        "field": field,
                        "check_type": check,
                        "severity": sev,
                        "source_law": src_law,
                        "legal_rule_ref": legal_ref,
                        "category": cat_opts or ["all"],
                        "enabled": True,
                        "pattern": pattern or None,
                        "version": "2011" if "Metrology" in src_law else "1945"
                    }
                    try:
                        res = requests.post(f"{API_URL}/api/v1/rules", json=payload, headers=headers, timeout=10)
                        if res.status_code in [200, 201]:
                            st.success("✅ Rule added successfully!")
                            st.cache_data.clear()
                        else:
                            err_body = res.json()
                            st.error(err_body.get("error", {}).get("message", "Failed to add rule"))
                    except requests.exceptions.ConnectionError:
                        st.error("Backend offline")

        elif operation == "Toggle Enable/Disable":
            rule_id_input = st.number_input("Rule DB ID to toggle:", min_value=1, key="toggle_rule_id", step=1)
            if st.button("🔄 Toggle", key="toggle_btn", use_container_width=True):
                try:
                    res = requests.get(f"{API_URL}/api/v1/rules/{int(rule_id_input)}", headers=headers, timeout=5)
                    if res.status_code == 200:
                        curr = res.json().get("data", {})
                        new_enabled = not curr.get("enabled", True)
                        patch_res = requests.patch(
                            f"{API_URL}/api/v1/rules/{int(rule_id_input)}",
                            json={"enabled": new_enabled},
                            headers=headers,
                            timeout=5
                        )
                        if patch_res.status_code == 200:
                            st.success(f"Rule {'enabled' if new_enabled else 'disabled'}!")
                            st.cache_data.clear()
                        else:
                            st.error(f"Toggle failed: {patch_res.status_code}")
                    else:
                        st.error(f"Rule not found: HTTP {res.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend offline")

        elif operation == "Delete Rule":
            if role != "admin":
                st.error("❌ Only Admin can delete rules.")
            else:
                del_id = st.number_input("Rule DB ID to delete:", min_value=1, key="del_rule_id", step=1)
                st.warning("⚠️ This action is permanent and will be audit-logged.")
                confirm = st.checkbox("I confirm deletion of this rule", key="del_confirm")
                if st.button("🗑️ Delete Rule", key="del_btn", use_container_width=True) and confirm:
                    try:
                        res = requests.delete(f"{API_URL}/api/v1/rules/{int(del_id)}", headers=headers, timeout=5)
                        if res.status_code == 200:
                            st.success("Rule deleted.")
                            st.cache_data.clear()
                        else:
                            st.error(f"Delete failed: {res.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend offline")
