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
exercise = st.selectbox(
    "Exercise:",
    ["20mm Edge", "Pinch", "Wrist Roller", "1RM Test - 20mm Edge", "1RM Test - Pinch", "1RM Test - Wrist Roller"],
    key="exercise_select"
)

# Get 1RMs from sheet
if worksheet:
    base_exercise = exercise.replace("1RM Test - ", "")
    current_1rm_L = get_user_1rm(worksheet, selected_user, base_exercise, "L")
    current_1rm_R = get_user_1rm(worksheet, selected_user, base_exercise, "R")
    
    # Show current 1RMs
    col_info_L, col_info_R = st.columns(2)
    with col_info_L:
        st.info(f"📊 Left 1RM: **{current_1rm_L} kg**")
    with col_info_R:
        st.info(f"📊 Right 1RM: **{current_1rm_R} kg**")
    
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
        prescribed_load_L = current_1rm_L * (target_pct / 100)
        prescribed_load_R = current_1rm_R * (target_pct / 100)
        
        col_prescribed_L, col_prescribed_R = st.columns(2)
        with col_prescribed_L:
            st.success(f"🎯 Left Prescribed: **{prescribed_load_L:.1f} kg**")
        with col_prescribed_R:
            st.success(f"🎯 Right Prescribed: **{prescribed_load_R:.1f} kg**")
    else:
        target_pct = 100
        prescribed_load_L = current_1rm_L
        prescribed_load_R = current_1rm_R
    
    # Option to use same weight or different weights
    st.markdown("---")
    use_same_weight = st.checkbox("✅ Use same weight for both arms", value=True, key="same_weight_toggle")
    
    if use_same_weight:
        # Single input for both arms
        actual_load = st.number_input(
            "💪 Weight Lifted (kg) - Both Arms:",
            min_value=0.0,
            max_value=200.0,
            value=(prescribed_load_L + prescribed_load_R) / 2,
            step=0.25,
            key="actual_load_both",
            help="Enter the total weight you lifted (same for both arms)"
        )
        actual_load_L = actual_load
        actual_load_R = actual_load
    else:
        # Separate inputs for each arm
        col_L, col_R = st.columns(2)
        
        with col_L:
            actual_load_L = st.number_input(
                "💪 Left Arm Weight (kg):",
                min_value=0.0,
                max_value=200.0,
                value=prescribed_load_L,
                step=0.25,
                key="actual_load_L",
                help="Weight lifted with left arm"
            )
        
        with col_R:
            actual_load_R = st.number_input(
                "💪 Right Arm Weight (kg):",
                min_value=0.0,
                max_value=200.0,
                value=prescribed_load_R,
                step=0.25,
                key="actual_load_R",
                help="Weight lifted with right arm"
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
    
    # Initialize quick notes in session state
    if "quick_note_append" not in st.session_state:
        st.session_state.quick_note_append = ""
    
    quick_cols = st.columns(len(QUICK_NOTES))
    for idx, (emoji_label, note_text) in enumerate(QUICK_NOTES.items()):
        if quick_cols[idx].button(emoji_label, key=f"quick_{note_text}"):
            # Append to quick_note_append instead
            if st.session_state.quick_note_append:
                st.session_state.quick_note_append += " " + note_text
            else:
                st.session_state.quick_note_append = note_text
            st.rerun()
    
    # Combine manual notes with quick notes
    if st.session_state.quick_note_append:
        final_notes = (notes + " " + st.session_state.quick_note_append).strip()
        st.info(f"📝 Notes to save: {final_notes}")
    else:
        final_notes = notes
    
    # Clear quick notes button
    if st.session_state.quick_note_append:
        if st.button("🗑️ Clear quick notes"):
            st.session_state.quick_note_append = ""
            st.rerun()
    
    # Submit button
    st.markdown("---")
    if st.button("✅ Log Workout", type="primary", use_container_width=True):
        # Log LEFT arm
        workout_data_L = {
            "User": selected_user,
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Exercise": exercise,
            "Arm": "L",
            "1RM_Reference": current_1rm_L,
            "Target_Percentage": target_pct,
            "Prescribed_Load_kg": prescribed_load_L,
            "Actual_Load_kg": actual_load_L,
            "Reps_Per_Set": reps_per_set,
            "Sets_Completed": sets_completed,
            "RPE": rpe,
            "Notes": final_notes
        }
        
        # Log RIGHT arm
        workout_data_R = {
            "User": selected_user,
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Exercise": exercise,
            "Arm": "R",
            "1RM_Reference": current_1rm_R,
            "Target_Percentage": target_pct,
            "Prescribed_Load_kg": prescribed_load_R,
            "Actual_Load_kg": actual_load_R,
            "Reps_Per_Set": reps_per_set,
            "Sets_Completed": sets_completed,
            "RPE": rpe,
            "Notes": final_notes
        }
        
        # Save both workouts
        success_L = save_workout_to_sheets(worksheet, workout_data_L)
        success_R = save_workout_to_sheets(worksheet, workout_data_R)
        
        if success_L and success_R:
            # Clear quick notes after successful save
            st.session_state.quick_note_append = ""
            
            # If this was a 1RM test, check for new records
            if "1RM Test" in exercise:
                new_records = []
                if actual_load_L > current_1rm_L:
                    update_user_1rm(worksheet, selected_user, base_exercise, "L", actual_load_L)
                    new_records.append(f"Left: {actual_load_L}kg")
                if actual_load_R > current_1rm_R:
                    update_user_1rm(worksheet, selected_user, base_exercise, "R", actual_load_R)
                    new_records.append(f"Right: {actual_load_R}kg")
                
                if new_records:
                    st.success(f"🎉 Workout logged! New 1RM records: {', '.join(new_records)}! 🏆")
                else:
                    st.success("🎉 Workout logged successfully!")
            else:
                st.success("🎉 Workout logged successfully for both arms!")
            st.balloons()
        else:
            st.error("❌ Failed to save workout. Please try again.")

else:
    st.error("⚠️ Could not connect to Google Sheets. Please check your configuration.")
