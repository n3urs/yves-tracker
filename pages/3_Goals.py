import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Goals", page_icon="🎯", layout="wide")

init_session_state()

st.title("🎯 Goals & Training Plan")

# Connect to Google Sheets
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

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
    key="user_selector_goals"
)

selected_user = st.session_state.current_user

# Training Plan Section
st.markdown("---")
st.header("📅 Weekly Training Plan")

for exercise, details in EXERCISE_PLAN.items():
    with st.expander(f"🏋️ {exercise}", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Schedule:** {details['Schedule']}")
            st.markdown(f"**Frequency:** {details['Frequency']}")
            st.markdown(f"**Sets:** {details['Sets']}")
            st.markdown(f"**Reps:** {details['Reps']}")
        
        with col2:
            st.markdown(f"**Rest:** {details['Rest']}")
            st.markdown(f"**Intensity:** {details['Intensity']}")
        
        st.markdown("**Technique Tips:**")
        for tip in details['Technique']:
            st.markdown(tip)

# Goals Section
st.markdown("---")
st.header("🎯 Set Your Goals")

# Get current 1RMs
if spreadsheet:
    st.subheader("Current 1RMs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**20mm Edge**")
        edge_L = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "L")
        edge_R = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "R")
        st.write(f"Left: {edge_L} kg")
        st.write(f"Right: {edge_R} kg")
    
    with col2:
        st.markdown("**Pinch**")
        pinch_L = get_user_1rm(spreadsheet, selected_user, "Pinch", "L")
        pinch_R = get_user_1rm(spreadsheet, selected_user, "Pinch", "R")
        st.write(f"Left: {pinch_L} kg")
        st.write(f"Right: {pinch_R} kg")
    
    with col3:
        st.markdown("**Wrist Roller**")
        wrist_L = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "L")
        wrist_R = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "R")
        st.write(f"Left: {wrist_L} kg")
        st.write(f"Right: {wrist_R} kg")

# Training Consistency
st.markdown("---")
st.subheader("📆 Training Consistency (Last 12 Weeks)")

if workout_sheet:
    df_fresh = load_data_from_sheets(workout_sheet, user=selected_user)
    
    if len(df_fresh) > 0:
        df_fresh['Date'] = pd.to_datetime(df_fresh['Date'])
        
        # Get unique training days
        training_days = df_fresh['Date'].dt.date.unique()
        
        # Calculate weekly frequency
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=12)
        
        recent_days = [d for d in training_days if start_date.date() <= d <= end_date.date()]
        
        weeks_trained = len(recent_days) / 7 if len(recent_days) > 0 else 1
        sessions_per_week = len(recent_days) / weeks_trained if weeks_trained > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Training Days (12 weeks)", len(recent_days))
        
        with col2:
            st.metric("Average Sessions/Week", f"{sessions_per_week:.1f}")
    else:
        st.info("No training data available yet.")
