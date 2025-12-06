import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

init_session_state()

st.title("👤 User Profile")

# Connect to Google Sheets
spreadsheet = get_google_sheet()

# Load users
if spreadsheet:
    available_users = load_users_from_sheets(spreadsheet)
else:
    available_users = USER_LIST.copy()

# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    available_users,
    index=available_users.index(st.session_state.current_user) if st.session_state.current_user in available_users else 0,
    key="user_selector_profile"
)

selected_user = st.session_state.current_user

# User Info Section
st.markdown("---")
st.header(f"Profile: {selected_user}")

if spreadsheet:
    # Bodyweight section
    st.subheader("⚖️ Bodyweight")
    st.caption("Your bodyweight is used to calculate relative strength metrics.")
    
    current_bw = get_bodyweight(spreadsheet, selected_user)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_bw = st.number_input(
            "Bodyweight (kg):",
            min_value=40.0,
            max_value=150.0,
            value=current_bw,
            step=0.5,
            key="profile_bw_input"
        )
    
    with col2:
        if st.button("💾 Update Bodyweight", use_container_width=True):
            if set_bodyweight(spreadsheet, selected_user, new_bw):
                st.success("✅ Bodyweight updated!")
                st.rerun()
    
    # Current 1RMs
    st.markdown("---")
    st.subheader("💪 Current 1RMs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**20mm Edge**")
        edge_L = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "L")
        edge_R = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "R")
        st.metric("Left", f"{edge_L} kg")
        st.metric("Right", f"{edge_R} kg")
    
    with col2:
        st.markdown("**Pinch**")
        pinch_L = get_user_1rm(spreadsheet, selected_user, "Pinch", "L")
        pinch_R = get_user_1rm(spreadsheet, selected_user, "Pinch", "R")
        st.metric("Left", f"{pinch_L} kg")
        st.metric("Right", f"{pinch_R} kg")
    
    with col3:
        st.markdown("**Wrist Roller**")
        wrist_L = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "L")
        wrist_R = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "R")
        st.metric("Left", f"{wrist_L} kg")
        st.metric("Right", f"{wrist_R} kg")
    
    st.caption("💡 1RMs are automatically updated when you log 1RM tests")

# Create New User Section
st.markdown("---")
st.header("➕ Create New User")

with st.form("new_user_form"):
    new_username = st.text_input("Username:", placeholder="Enter new username")
    new_user_bw = st.number_input("Initial Bodyweight (kg):", min_value=40.0, max_value=150.0, value=78.0, step=0.5)
    
    submitted = st.form_submit_button("Create User", use_container_width=True)
    
    if submitted:
        if not new_username:
            st.error("❌ Please enter a username")
        elif new_username in available_users:
            st.error(f"❌ User '{new_username}' already exists")
        else:
            if spreadsheet:
                success, message = add_new_user(spreadsheet, new_username, new_user_bw)
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    st.info("🔄 Please refresh the page to see the new user")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Could not connect to Google Sheets")
