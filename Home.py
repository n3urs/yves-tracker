import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import *
import pandas as pd

st.set_page_config(page_title="Yves Climbing Tracker", page_icon="🧗", layout="wide")

init_session_state()

st.title("🧗 Yves Climbing Tracker")
st.markdown("### Finger Strength Training Dashboard")

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
    key="user_selector_home"
)

selected_user = st.session_state.current_user

st.markdown("---")
st.markdown(f"## Welcome, {selected_user}! 👋")

# Quick Stats
if workout_sheet:
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    if len(df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_workouts = len(df)
            st.metric("Total Workouts", total_workouts)
        
        with col2:
            df['Date'] = pd.to_datetime(df['Date'])
            last_workout = df['Date'].max()
            days_since = (pd.Timestamp.now() - last_workout).days
            st.metric("Last Workout", f"{days_since} days ago")
        
        with col3:
            total_volume = (pd.to_numeric(df['Actual_Load_kg'], errors='coerce') * 
                           pd.to_numeric(df['Reps_Per_Set'], errors='coerce') * 
                           pd.to_numeric(df['Sets_Completed'], errors='coerce')).sum()
            st.metric("Total Volume", f"{total_volume:,.0f} kg")
        
        with col4:
            avg_rpe = df['RPE'].mean() if 'RPE' in df.columns else 0
            st.metric("Avg RPE", f"{avg_rpe:.1f}")
    else:
        st.info("📝 No workout data yet. Head to **Log Workout** to get started!")
else:
    st.error("⚠️ Could not connect to Google Sheets. Please check your configuration.")

# Quick Links
st.markdown("---")
st.subheader("🚀 Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/1_Log_Workout.py", label="📝 Log Workout", icon="📝")

with col2:
    st.page_link("pages/2_Progress.py", label="📈 View Progress", icon="📈")

with col3:
    st.page_link("pages/3_Goals.py", label="🎯 Training Plan", icon="🎯")
