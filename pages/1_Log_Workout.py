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
    index=available_users.index(st.session_state.current_user) if st.session_state.current_user in available_users else 0,
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

# ==================== MAIN WORKOUT FORM ====================

st.markdown("---")
st.subheader("🏋️ Log Your Session")

# Exercise selection
col1, col2 = st.columns(2)

with col1:
    exercise = st.selectbox(
        "Exercise:",
        ["20mm Edge", "Pinch", "Wrist Roller", "1RM Test - 20mm Edge", "1RM Test - Pinch", "1RM Test - Wrist Roller"],
        key="exercise_select"
    )

with col2:
    arm = st.selectbox("Arm:", ["L", "R"], key="arm_select")

# Get 1RM from sheet
if worksheet:
    base_exercise = exercise.replace("1RM Test - ", "")
    current_1rm = get_user_1rm(worksheet, selected_user, base_exercise, arm)
    
    # Show current 1RM
    st.info(f"📊 Current 1RM for {base_exercise} ({arm}): **{current_1rm} kg**")
    
    # Target percentage (only if not 1RM test)
    if "1RM Test" not in exercise:
        target_pct = st.slider(
            "Target % of 1RM:",
            min_value=50,
            max_value=100,
            value=80,
            step=5,
            key="target_pct_slider"
        )
        prescribed_load = current_1rm * (target_pct / 100)
        st.success(f"🎯 Prescribed Load: **{prescribed_load:.1f} kg** ({target_pct}% of {current_1rm}kg)")
    else:
        target_pct = 100
        prescribed_load = current_1rm
    
    # Actual weight lifted
    st.markdown("---")
    actual_load = st.number_input(
        "💪 Actual Weight Lifted (kg):",
        min_value=0.0,
        max_value=200.0,
        value=prescribed_load,
        step=0.25,
        key="actual_load_input",
        help="Enter the total weight you lifted (not split between sides)"
    )
    
    # Workout details
    st.markdown("---")
    st.subheader("📝 Workout Details")
    
    col_reps, col_sets, col_rpe = st.columns(3)
    
    with col_reps:
        reps_per_set = st.number_input("Reps per set:", min_value=1, max_value=20, value=5, step=1, key="reps_input")
    
    with col_sets:
        sets_completed = st.number_input("Sets completed:", min_value=1, max_value=10, value=3 if "1RM Test" not in exercise else 1, step=1, key="sets_input")
    
    with col_rpe:
        rpe = st.slider("RPE (Rate of Perceived Exertion):", min_value=1, max_value=10, value=7, step=1, key="rpe_slider")
    
    # Notes
    notes = st.text_area("Notes (optional):", placeholder="How did it feel? Any observations?", key="notes_input")
    
    # Quick note buttons
    st.markdown("**Quick Notes:**")
    quick_cols = st.columns(len(QUICK_NOTES))
    for idx, (emoji_label, note_text) in enumerate(QUICK_NOTES.items()):
        if quick_cols[idx].button(emoji_label, key=f"quick_{note_text}"):
            st.session_state.notes_input = notes + " " + note_text if notes else note_text
            st.rerun()
    
    # Submit button
    st.markdown("---")
    if st.button("✅ Log Workout", type="primary", use_container_width=True):
        workout_data = {
            "User": selected_user,
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Exercise": exercise,
            "Arm": arm,
            "1RM_Reference": current_1rm,
            "Target_Percentage": target_pct,
            "Prescribed_Load_kg": prescribed_load,
            "Actual_Load_kg": actual_load,
            "Reps_Per_Set": reps_per_set,
            "Sets_Completed": sets_completed,
            "RPE": rpe,
            "Notes": notes
        }
        
        if save_workout_to_sheets(worksheet, workout_data):
            # If this was a 1RM test and it's higher than current, update it
            if "1RM Test" in exercise and actual_load > current_1rm:
                update_user_1rm(worksheet, selected_user, base_exercise, arm, actual_load)
                st.success(f"🎉 Workout logged! New 1RM record: {actual_load}kg! 🏆")
            else:
                st.success("🎉 Workout logged successfully!")
            st.balloons()
        else:
            st.error("❌ Failed to save workout. Please try again.")

else:
    st.error("⚠️ Could not connect to Google Sheets. Please check your configuration.")
