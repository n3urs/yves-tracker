import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
from datetime import datetime

st.set_page_config(page_title="Log Workout", page_icon="📝", layout="wide")

init_session_state()

st.title("📝 Log Workout")

# Connect to sheet
worksheet = get_google_sheet()

# Load users dynamically from Google Sheets
if worksheet:
    available_users = load_users_from_sheets(worksheet)
else:
    available_users = USER_LIST.copy()


# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    available_users,
    index=available_users.index(st.session_state.current_user),
    key="user_selector_log"
)

selected_user = st.session_state.current_user

# Bodyweight input
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Bodyweight")
current_bw = get_bodyweight(selected_user)
new_bw = st.sidebar.number_input(
    "Your bodyweight (kg)",
    min_value=40.0,
    max_value=150.0,
    value=current_bw,
    step=0.5,
    key="bodyweight_input"
)
if new_bw != current_bw:
    set_bodyweight(selected_user, new_bw)
    st.sidebar.success(f"✅ Bodyweight updated to {new_bw}kg")

# 1RM Manager in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("💾 1RM Manager")

saved_1rms = st.session_state.saved_1rms.get(selected_user, {})
base_exercises = ["20mm Edge", "Pinch", "Wrist Roller"]

for ex in base_exercises:
    col_left, col_right = st.sidebar.columns(2)
    with col_left:
        saved_1rms[f"{ex} (L)"] = st.sidebar.number_input(
            f"{ex} (L) kg",
            min_value=20,
            max_value=200,
            value=saved_1rms.get(f"{ex} (L)", 105 if "Edge" in ex else 85 if "Pinch" in ex else 75),
            step=1,
            key=f"1rm_{ex}_L_{selected_user}"
        )
    with col_right:
        saved_1rms[f"{ex} (R)"] = st.sidebar.number_input(
            f"{ex} (R) kg",
            min_value=20,
            max_value=200,
            value=saved_1rms.get(f"{ex} (R)", 105 if "Edge" in ex else 85 if "Pinch" in ex else 75),
            step=1,
            key=f"1rm_{ex}_R_{selected_user}"
        )

if st.sidebar.button("💾 Save All 1RMs", key="save_1rms_btn", use_container_width=True):
    st.session_state.saved_1rms[selected_user] = saved_1rms
    st.sidebar.success("✅ 1RMs saved!")

