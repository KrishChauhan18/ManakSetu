import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Audit Log — ComplyErg", page_icon="📜", layout="wide")

API_URL = "http://localhost:8000"

# Role Guard (Supervisor & Admin Only)
user_role = st.session_state.get("user_role", "inspector")
if user_role not in ["supervisor", "admin"]:
    st.error("⛔ Access Denied. Audit Log viewer is restricted to Supervisors and Admins.")
    st.stop()

headers = {}
if st.session_state.get("jwt_token"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("📜 System Audit Trail & Override Log")
st.caption("Immutable append-only record of all supervisor field overrides, rule edits, scan deletions, and role modifications.")

st.markdown("---")

col1, col2 = st.columns([1, 1])
with col1:
    target_filter = st.selectbox("Filter Target Type", ["All", "scan", "rule", "user"])
with col2:
    action_filter = st.selectbox("Filter Action", ["All", "override", "delete", "rule_change", "role_change", "user_create", "user_edit"])

params = {}
if target_filter != "All":
    params["target_type"] = target_filter
if action_filter != "All":
    params["action"] = action_filter

try:
    res = requests.get(f"{API_URL}/audit/", params=params, headers=headers)
    if res.status_code == 200:
        logs = res.json()
        if logs:
            log_table = []
            for log in logs:
                log_table.append({
                    "Log ID": log["id"],
                    "Timestamp": log["timestamp"],
                    "User ID": log["user_id"],
                    "Action": log["action"].upper(),
                    "Target Type": log["target_type"].upper(),
                    "Target ID": log["target_id"],
                    "Reason": log.get("reason") or "N/A",
                    "Old Value": str(log.get("old_value")) if log.get("old_value") else "N/A",
                    "New Value": str(log.get("new_value")) if log.get("new_value") else "N/A"
                })
            df = pd.DataFrame(log_table)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No audit log entries found matching selected filters.")
    else:
        st.error(f"Error fetching audit log ({res.status_code}): {res.text}")
except Exception as e:
    st.error(f"Could not connect to Audit Log API: {e}")
