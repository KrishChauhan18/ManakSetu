import streamlit as st
import requests

st.set_page_config(page_title="User Management — ComplyErg", page_icon="👥", layout="wide")

API_URL = "http://localhost:8000"

# Role Guard (Admin Only)
user_role = st.session_state.get("user_role", "inspector")
if user_role != "admin":
    st.error("⛔ Access Denied. User Management is restricted to Administrators only.")
    st.stop()

headers = {}
if st.session_state.get("jwt_token"):
    headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

st.title("👥 User Management & Role Authorization")
st.caption("Admin portal to manage system users, roles (Inspector, Supervisor, Admin), and regional assignments.")

st.markdown("---")

tab_list, tab_create = st.tabs(["Active Users Directory", "Create New System User"])

with tab_list:
    st.subheader("System Users")
    try:
        res = requests.get(f"{API_URL}/users/", headers=headers)
        if res.status_code == 200:
            users = res.json()
            if users:
                user_table = []
                for u in users:
                    user_table.append({
                        "ID": u["id"],
                        "Email": u["email"],
                        "Role": u["role"].upper(),
                        "Region": u.get("region") or "N/A",
                        "Supervisor ID": u.get("supervisor_id") or "None",
                        "Active Status": "Active" if u["is_active"] else "Inactive"
                    })
                st.dataframe(user_table, use_container_width=True)

                st.markdown("### Update User Role / Status")
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    selected_user_id = st.selectbox("Select User ID", [u["id"] for u in users], key="edit_u_id")
                with col2:
                    new_role = st.selectbox("New Role", ["inspector", "supervisor", "admin"], key="edit_u_role")
                with col3:
                    new_active = st.selectbox("Active Status", [True, False], key="edit_u_active")

                if st.button("Update User Profile"):
                    up_res = requests.put(
                        f"{API_URL}/users/{selected_user_id}",
                        json={"role": new_role, "is_active": new_active},
                        headers=headers
                    )
                    if up_res.status_code == 200:
                        st.success(f"User {selected_user_id} updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update user: {up_res.text}")
            else:
                st.info("No users found in database.")
        else:
            st.error(f"Error fetching users ({res.status_code}): {res.text}")
    except Exception as e:
        st.error(f"Unable to connect to backend: {e}")

with tab_create:
    st.subheader("Register New Inspector or Supervisor Account")
    with st.form("create_user_form"):
        new_email = st.text_input("User Email")
        new_pass = st.text_input("Temporary Password", type="password")
        c_role = st.selectbox("Assign Role", ["inspector", "supervisor", "admin"])
        c_region = st.text_input("Assigned Region", value="Delhi NCR")
        submit_btn = st.form_submit_button("Create User & Audit Record")

        if submit_btn:
            if not new_email or not new_pass:
                st.warning("Email and Password are required.")
            else:
                try:
                    res = requests.post(
                        f"{API_URL}/users/",
                        json={
                            "email": new_email,
                            "password": new_pass,
                            "role": c_role,
                            "region": c_region
                        },
                        headers=headers
                    )
                    if res.status_code in [200, 201]:
                        st.success(f"User '{new_email}' created successfully as {c_role.upper()}!")
                    else:
                        st.error(f"Failed to create user: {res.text}")
                except Exception as e:
                    st.error(f"Error creating user: {e}")
