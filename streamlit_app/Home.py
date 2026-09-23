import streamlit as st
import requests
import sys
import os

# Add streamlit_app to path for i18n import
sys.path.insert(0, os.path.dirname(__file__))
from i18n import t

st.set_page_config(
    page_title="ComplyErg — Legal Metrology Scanner",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 50%, #10B981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    line-height: 1.1;
}
.sub-title {
    font-size: 1.05rem;
    color: #94A3B8;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}
.hero-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08);
}
.badge-inspector { background: #1E40AF; color: #BFDBFE; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.badge-supervisor { background: #5B21B6; color: #DDD6FE; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.badge-admin { background: #065F46; color: #A7F3D0; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Session state initialization
for key, default in [
    ("jwt_token", None), ("user_role", "inspector"),
    ("user_email", None), ("last_scan_id", None), ("ui_lang", "en")
]:
    if key not in st.session_state:
        st.session_state[key] = default

API_URL = "http://localhost:8000"

# ─── Language Toggle ─────────────────────────────────────────────────────────
lang = st.session_state.get("ui_lang", "en")
toggle_label = "🌐 Language / भाषा"
with st.sidebar:
    chosen_lang = st.radio(toggle_label, ["English", "हिंदी"], index=0 if lang == "en" else 1, key="lang_radio_home")
    st.session_state["ui_lang"] = "en" if chosen_lang == "English" else "hi"
    lang = st.session_state["ui_lang"]

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f'<div class="main-title">{t("app_title", lang)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{t("app_subtitle", lang)}</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1.8, 1.2])

with col1:
    st.markdown("""
    <div class="hero-card">
        <h3 style="color:#E2E8F0; margin-top:0;">System Overview</h3>
        <p style="color:#CBD5E1;"><b>ComplyErg</b> empowers Legal Metrology officers to scan product packaging labels
        in real-time, extract mandatory legal declarations, and verify compliance deterministically
        against Indian Legal Metrology statutory rules.</p>
        <ul style="color:#94A3B8; line-height:1.9;">
            <li><b style="color:#60A5FA;">Mandatory Statutory Extraction:</b> Manufacturer/Packer, Net Quantity, MRP, Mfg &amp; Expiry Dates, Consumer Care, Batch No, FSSAI Lic.</li>
            <li><b style="color:#60A5FA;">Deterministic Rule Engine:</b> 100% explainable verdicts for Rules 6, 7, 9, 10 + Drugs &amp; Cosmetics Rules 1945 (Schedule H/H1/X).</li>
            <li><b style="color:#60A5FA;">Dual-Category Compliance:</b> Grocery/General + Prescription Medicine with Rx symbol detection.</li>
            <li><b style="color:#60A5FA;">3-Tier RBAC:</b> Inspector, Supervisor, and Administrator roles with query-level data isolation.</li>
            <li><b style="color:#60A5FA;">Explainability Visualizer:</b> Color-coded bounding boxes on label images (Green = Pass, Red = Fail, Amber = Review).</li>
            <li><b style="color:#60A5FA;">Real-time WebSocket Progress:</b> Live stage-by-stage scan pipeline progress.</li>
            <li><b style="color:#60A5FA;">Audit Trail:</b> Every override, deletion, and rule change atomically logged.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.info("💡 **Pro-Tip:** Use **1 Scan Product** to upload a grocery or medicine label. Switch to Admin to manage rules and users.")

with col2:
    st.markdown(f"### {t('login_portal', lang)}")

    if st.session_state["jwt_token"]:
        role = st.session_state['user_role']
        badge_class = f"badge-{role}"
        st.success(f"Logged in as **{st.session_state['user_email']}**")
        st.markdown(f'<span class="{badge_class}">{role.upper()}</span>', unsafe_allow_html=True)
        if st.button(t("logout", lang), key="logout_btn", use_container_width=True):
            st.session_state["jwt_token"] = None
            st.session_state["user_email"] = None
            st.session_state["user_role"] = "inspector"
            st.rerun()
    else:
        st.markdown(f"#### {t('login_quick', lang)}")
        qcol1, qcol2, qcol3 = st.columns(3)

        def attempt_login(email_val, pass_val):
            try:
                res = requests.post(
                    f"{API_URL}/api/v1/auth/login",
                    json={"email": email_val, "password": pass_val},
                    timeout=5
                )
                if res.status_code == 200:
                    rdata = res.json()
                    data = rdata.get("data", rdata)
                    st.session_state["jwt_token"] = data["access_token"]
                    st.session_state["user_role"] = data["role"]
                    st.session_state["user_email"] = data.get("email", email_val)
                    st.success(f"Logged in as {data['role'].upper()}!")
                    st.rerun()
                else:
                    st.error(f"Login failed: {res.text[:200]}")
            except Exception:
                # Offline mock login fallback
                st.session_state["jwt_token"] = f"mock_{email_val}_token"
                if "admin" in email_val:
                    st.session_state["user_role"] = "admin"
                elif "supervisor" in email_val:
                    st.session_state["user_role"] = "supervisor"
                else:
                    st.session_state["user_role"] = "inspector"
                st.session_state["user_email"] = email_val
                st.success("Logged in (offline mode)")
                st.rerun()

        with qcol1:
            if st.button(t("btn_inspector", lang), use_container_width=True, key="q_inspector"):
                attempt_login("inspector@complyerg.gov.in", "Inspector@123")
        with qcol2:
            if st.button(t("btn_supervisor", lang), use_container_width=True, key="q_supervisor"):
                attempt_login("supervisor@complyerg.gov.in", "Supervisor@123")
        with qcol3:
            if st.button(t("btn_admin", lang), use_container_width=True, key="q_admin"):
                attempt_login("admin@complyerg.gov.in", "Admin@123")

        st.markdown("---")
        tab1, tab2 = st.tabs(["Custom Login", "Register Account"])

        with tab1:
            email = st.text_input("Email Address", value="admin@complyerg.gov.in", key="login_email")
            password = st.text_input("Password", type="password", value="Admin@123", key="login_pass")
            if st.button("Login to ComplyErg", use_container_width=True, type="primary", key="login_btn"):
                attempt_login(email, password)

        with tab2:
            reg_email = st.text_input("New User Email", key="reg_email")
            reg_pass = st.text_input("New Password", type="password", key="reg_pass")
            reg_role = st.selectbox("Role", ["inspector", "supervisor", "admin"], key="reg_role")
            reg_region = st.text_input("Region", value="Delhi NCR", key="reg_region")
            if st.button("Register Account", use_container_width=True, key="reg_btn"):
                try:
                    res = requests.post(
                        f"{API_URL}/api/v1/auth/register",
                        json={"email": reg_email, "password": reg_pass, "role": reg_role, "region": reg_region},
                        timeout=5
                    )
                    if res.status_code == 200:
                        st.success("Registration successful! Please login.")
                    else:
                        err_data = res.json()
                        st.error(err_data.get("error", {}).get("message", "Registration failed"))
                except Exception as e:
                    st.error(f"Error connecting to backend API: {e}")
