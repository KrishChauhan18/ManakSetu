import streamlit as st
import requests
import pandas as pd
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from i18n import t

st.set_page_config(page_title="Admin — ComplyErg", page_icon="⚡", layout="wide")

API_URL = "http://localhost:8000"
lang = st.session_state.get("ui_lang", "en")

headers = {}
role = st.session_state.get("user_role", "inspector")
if st.session_state.get("jwt_token") and not str(st.session_state.get("jwt_token", "")).startswith("mock_"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

if role != "admin":
    st.error("🔒 Access Denied — Admin role required.")
    st.info("Login as admin@complyerg.gov.in / Admin@123 from the Home page.")
    st.stop()

st.title("⚡ Admin Panel")
st.caption("User management, system health, and advanced configuration.")

tab1, tab2, tab3 = st.tabs(["👥 User Management", "📋 Audit Log", "⚙️ System Health"])

with tab1:
    st.subheader("Active Users")

    @st.cache_data(ttl=60, show_spinner=False)
    def fetch_users():
        try:
            res = requests.get(f"{API_URL}/api/v1/users", headers=headers, timeout=10)
            if res.status_code == 200:
                rdata = res.json()
                return rdata.get("data", {}).get("items", rdata.get("data", [])), None
            return None, f"HTTP {res.status_code}"
        except requests.exceptions.ConnectionError:
            return None, "Backend offline"
        except Exception as e:
            return None, str(e)

    if st.button("🔄 Refresh Users", key="admin_refresh_users"):
        st.cache_data.clear()

    users, usr_err = fetch_users()
    if usr_err:
        st.warning(f"⚠️ {usr_err} — demo data shown.")
        users = [
            {"id": 1, "email": "admin@complyerg.gov.in", "role": "admin", "region": "Delhi NCR", "is_active": True, "total_scans": 45},
            {"id": 2, "email": "supervisor@complyerg.gov.in", "role": "supervisor", "region": "Mumbai", "is_active": True, "total_scans": 112},
            {"id": 3, "email": "inspector@complyerg.gov.in", "role": "inspector", "region": "Bangalore", "is_active": True, "total_scans": 289},
        ]

    if users:
        rows = [{
            "ID": u.get("id"),
            "Email": u.get("email", ""),
            "Role": u.get("role", "").upper(),
            "Region": u.get("region", "N/A"),
            "Active": "✅" if u.get("is_active") else "❌",
            "Total Scans": u.get("total_scans", 0)
        } for u in users]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Create New User")
    with st.form("admin_create_user"):
        nc1, nc2 = st.columns(2)
        with nc1:
            new_email = st.text_input("Email")
            new_pass = st.text_input("Password", type="password")
        with nc2:
            new_role = st.selectbox("Role", ["inspector", "supervisor", "admin"])
            new_region = st.text_input("Region", value="Delhi NCR")
        if st.form_submit_button("Create User", use_container_width=True):
            try:
                res = requests.post(
                    f"{API_URL}/api/v1/users",
                    json={"email": new_email, "password": new_pass, "role": new_role, "region": new_region},
                    headers=headers,
                    timeout=5
                )
                if res.status_code in [200, 201]:
                    st.success(f"✅ User {new_email} created!")
                    st.cache_data.clear()
                else:
                    st.error(res.json().get("error", {}).get("message", "Failed to create user"))
            except requests.exceptions.ConnectionError:
                st.error("Backend offline")

    st.markdown("---")
    st.subheader("🔧 User Actions")
    act_uid = st.number_input("User ID", min_value=1, key="usr_act_id", step=1)
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("🔄 Toggle Active/Inactive", use_container_width=True, key="usr_toggle"):
            try:
                res = requests.patch(f"{API_URL}/api/v1/users/{int(act_uid)}/toggle-active", headers=headers, timeout=5)
                if res.status_code == 200:
                    st.success("User status toggled!")
                    st.cache_data.clear()
                else:
                    st.error(f"HTTP {res.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Backend offline")
    with act_col2:
        if st.button("🗑️ Delete User", use_container_width=True, key="usr_delete"):
            try:
                res = requests.delete(f"{API_URL}/api/v1/users/{int(act_uid)}", headers=headers, timeout=5)
                if res.status_code == 200:
                    st.success("User deleted.")
                    st.cache_data.clear()
                else:
                    st.error(f"HTTP {res.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Backend offline")

with tab2:
    st.subheader("System Audit Log")

    @st.cache_data(ttl=30, show_spinner=False)
    def fetch_audit(page):
        try:
            res = requests.get(f"{API_URL}/api/v1/audit", headers=headers, params={"page": page, "page_size": 20}, timeout=10)
            if res.status_code == 200:
                rdata = res.json()
                return rdata.get("data", rdata), None
            return None, f"HTTP {res.status_code}"
        except requests.exceptions.ConnectionError:
            return None, "Backend offline"
        except Exception as e:
            return None, str(e)

    audit_page = st.number_input("Audit Log Page", min_value=1, value=1, key="audit_page", step=1)
    if st.button("🔄 Refresh Audit Log", key="audit_refresh"):
        st.cache_data.clear()

    audit_data, audit_err = fetch_audit(audit_page)
    if audit_err:
        st.warning(f"⚠️ {audit_err} — demo data shown.")
        audit_data = {
            "items": [
                {"id": 1, "action": "scan_created", "entity_type": "scan", "entity_id": 103, "user_email": "inspector@complyerg.gov.in", "created_at": "2024-01-15 12:30:01"},
                {"id": 2, "action": "rule_toggled", "entity_type": "rule", "entity_id": 4, "user_email": "admin@complyerg.gov.in", "created_at": "2024-01-15 09:12:35"},
                {"id": 3, "action": "field_overridden", "entity_type": "scan", "entity_id": 101, "user_email": "supervisor@complyerg.gov.in", "created_at": "2024-01-14 16:44:20"},
            ]
        }

    audit_items = audit_data.get("items", []) if audit_data else []
    if audit_items:
        arows = [{
            "ID": a.get("id"),
            "Action": a.get("action", ""),
            "Entity": f"{a.get('entity_type', '')} #{a.get('entity_id', '')}",
            "User": a.get("user_email", ""),
            "Timestamp": a.get("created_at", ""),
        } for a in audit_items]
        st.dataframe(pd.DataFrame(arows), use_container_width=True, hide_index=True)
    else:
        st.info("No audit log entries found.")

with tab3:
    st.subheader("⚙️ System Health")
    try:
        res = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        if res.status_code == 200:
            health = res.json()
            data = health.get("data", health)
            hc1, hc2, hc3 = st.columns(3)
            status = data.get("status", "unknown")
            with hc1:
                color = "#10B981" if status == "healthy" else "#EF4444"
                st.markdown(f'<div style="background:#1E293B;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;"><div style="font-size:2rem;color:{color};">{"✅" if status=="healthy" else "❌"}</div><div style="color:#94A3B8;font-size:13px;">Backend Status</div><div style="color:#E2E8F0;font-size:1.1rem;font-weight:700;">{status.upper()}</div></div>', unsafe_allow_html=True)
            with hc2:
                db_ok = data.get("database", False)
                db_color = "#10B981" if db_ok else "#EF4444"
                st.markdown(f'<div style="background:#1E293B;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;"><div style="font-size:2rem;color:{db_color};">{"✅" if db_ok else "❌"}</div><div style="color:#94A3B8;font-size:13px;">Database</div><div style="color:#E2E8F0;font-size:1.1rem;font-weight:700;">{"CONNECTED" if db_ok else "OFFLINE"}</div></div>', unsafe_allow_html=True)
            with hc3:
                st.markdown(f'<div style="background:#1E293B;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;"><div style="font-size:2rem;color:#3B82F6;">⚙️</div><div style="color:#94A3B8;font-size:13px;">Version</div><div style="color:#E2E8F0;font-size:1.1rem;font-weight:700;">{data.get("version","v4.0")}</div></div>', unsafe_allow_html=True)
            st.json(data)
        else:
            st.error(f"Health check failed: HTTP {res.status_code}")
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Backend server offline. Start with: `uvicorn app.main:app --reload --port 8000`")
        st.markdown("""
        <div style="background:#1A0A0A;border:1px solid #EF4444;border-radius:10px;padding:16px;margin-top:12px;">
            <b style="color:#FCA5A5;">🚀 Quick Start Commands:</b><br/>
            <code style="color:#F1F5F9;">cd SIH_CodePulse_034</code><br/>
            <code style="color:#F1F5F9;">pip install -r requirements.txt</code><br/>
            <code style="color:#F1F5F9;">uvicorn app.main:app --reload --port 8000</code>
        </div>
        """, unsafe_allow_html=True)
