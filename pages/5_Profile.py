import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

init_session_state()

st.title("👤 User Profile")

# Connect to sheet
worksheet = get_google_sheet()

# Load users dynamically from Google Sheets
if worksheet:
    available_users = load_users_from_sheets(worksheet)
else:
    available_users = USER_LIST.copy()


# User selector
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    available_users,
    index=available_users.index(st.session_state.current_user),
    key="user_selector_profile"
)

# User creation section
st.markdown("---")
st.subheader("➕ Create New User Profile")

with st.expander("Add a New User"):
    new_username = st.text_input("Enter new username:", key="new_user_input")
    
    if st.button("Create User", type="primary"):
        if new_username and new_username.strip():
            if worksheet:
                success, message = add_new_user(worksheet, new_username.strip())
                if success:
                    st.success(f"✅ {message}! User '{new_username}' has been created.")
                    # Refresh the user list
                    available_users = load_users_from_sheets(worksheet)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Could not connect to Google Sheets.")
        else:
            st.warning("Please enter a valid username.")

st.markdown("---")

# Bodyweight section
st.subheader("⚖️ Bodyweight")
st.caption("Your bodyweight is used to calculate relative strength on the leaderboard.")

current_bw = get_bodyweight(selected_user)

col1, col2 = st.columns([2, 1])

with col1:
    new_bodyweight = st.number_input(
        "Bodyweight (kg):",
        min_value=40.0,
        max_value=150.0,
        value=current_bw,
        step=0.5,
        key="bodyweight_input"
    )

with col2:
    st.metric("Current Bodyweight", f"{current_bw} kg")

if st.button("💾 Save Bodyweight", type="primary", use_container_width=True):
    if worksheet:
        # Update session state
        set_bodyweight(selected_user, new_bodyweight)
        
        # Save to Google Sheets
        if save_bodyweight_to_sheets(worksheet, selected_user, new_bodyweight):
            st.success(f"✅ Bodyweight updated to {new_bodyweight} kg and saved!")
            st.rerun()
        else:
            st.error("Failed to save to Google Sheets.")
    else:
        st.error("Could not connect to Google Sheets.")

st.markdown("---")

# Display all users' bodyweights
st.subheader("👥 All Users")

if worksheet:
    bodyweights_data = []
    for user in available_users:
        bw = get_bodyweight(user)
        bodyweights_data.append({"User": user, "Bodyweight (kg)": bw})
    
    import pandas as pd
    df_bw = pd.DataFrame(bodyweights_data)
    st.dataframe(df_bw, use_container_width=True, hide_index=True)

st.markdown("---")


selected_user = st.session_state.current_user

