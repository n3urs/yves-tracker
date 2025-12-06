import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
from datetime import datetime

st.set_page_config(page_title="Log Workout", page_icon="📝", layout="wide")

init_session_state()

st.title("📝 Log Workout")

# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    USER_LIST,
    index=USER_LIST.index(st.session_state.current_user),
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

# Connect to sheet
worksheet = get_google_sheet()

exercise_list = [
    "20mm Edge", 
    "Pinch", 
    "Wrist Roller",
    "─────────────────",
    "1RM Test: 20mm Edge",
    "1RM Test: Pinch",
    "1RM Test: Wrist Roller"
]

# ==================== CALCULATOR ====================
st.subheader("⚙️ Workout Calculator")

selected_exercise = st.selectbox("Exercise", exercise_list, key="exercise_select")

if selected_exercise != "─────────────────" and not selected_exercise.startswith("1RM Test:"):
    current_1rm_L = saved_1rms.get(f"{selected_exercise} (L)", 105)
    current_1rm_R = saved_1rms.get(f"{selected_exercise} (R)", 105)

    intensity_options = {"50% Warm-up": 0.50, "60% Warm-up": 0.60, "70% Warm-up": 0.70, "80% Work": 0.80, "Custom": None}
    intensity_label = st.selectbox("Intensity", list(intensity_options.keys()), key="intensity_select")

    if intensity_label == "Custom":
        target_pct = st.slider("Custom %", min_value=0.3, max_value=1.0, step=0.05, value=0.8)
    else:
        target_pct = intensity_options[intensity_label]

    prescribed_load_L = current_1rm_L * target_pct
    prescribed_load_R = current_1rm_R * target_pct

    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        st.metric("Left Arm Target", f"{prescribed_load_L:.1f} kg")
        plates_str_L, actual_load_L = calculate_plates(prescribed_load_L)
        st.caption(f"**Plates:** {plates_str_L}")
    
    with col_calc2:
        st.metric("Right Arm Target", f"{prescribed_load_R:.1f} kg")
        plates_str_R, actual_load_R = calculate_plates(prescribed_load_R)
        st.caption(f"**Plates:** {plates_str_R}")
else:
    if selected_exercise.startswith("1RM Test:"):
        st.info("💡 For 1RM tests, enter the maximum weight you can lift for 1 rep.")
    prescribed_load_L = 100.0
    prescribed_load_R = 100.0
    current_1rm_L = 100.0
    current_1rm_R = 100.0
    target_pct = 1.0

st.markdown("---")

# ==================== LOG FORM ====================
st.subheader("📋 Log Today's Session")

same_weight = st.checkbox("✅ Same weight both arms", value=True, key="same_weight_check")

if same_weight:
    st.subheader("Both Arms")
    actual_load = st.number_input("Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load_L, step=0.5, key="load_both")
    reps = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1, key="reps_both")
    sets = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1, key="sets_both")
    rpe = st.slider("RPE (Rate of Perceived Exertion)", min_value=1, max_value=10, value=7, key="rpe_both")
    
    actual_load_L = actual_load_R = actual_load
    reps_L = reps_R = reps
    sets_L = sets_R = sets
    rpe_L = rpe_R = rpe
else:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("👈 Left Arm")
        actual_load_L = st.number_input("Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load_L, step=0.5, key="load_L")
        reps_L = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1, key="reps_L")
        sets_L = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1, key="sets_L")
        rpe_L = st.slider("RPE", min_value=1, max_value=10, value=7, key="rpe_L")
    
    with col_right:
        st.subheader("👉 Right Arm")
        actual_load_R = st.number_input("Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load_R, step=0.5, key="load_R")
        reps_R = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1, key="reps_R")
        sets_R = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1, key="sets_R")
        rpe_R = st.slider("RPE", min_value=1, max_value=10, value=7, key="rpe_R")

quick_note = st.selectbox("Quick note:", ["None"] + list(QUICK_NOTES.keys()), key="quick_note_select")
quick_note_text = QUICK_NOTES.get(quick_note, "") if quick_note != "None" else ""
notes = st.text_input("Custom notes (optional)", placeholder="e.g., felt strong, hand pain, etc.")
full_notes = f"{quick_note_text} {notes}".strip()

# ==================== SAVE BUTTON ====================
if st.button("✅ Save Workout (Both Arms)", key="save_btn", use_container_width=True):
    if worksheet and selected_exercise != "─────────────────":
        new_row_L = {
            "User": selected_user,
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Exercise": selected_exercise,
            "Arm": "L",
            "1RM_Reference": current_1rm_L,
            "Target_Percentage": target_pct,
            "Prescribed_Load_kg": prescribed_load_L,
            "Actual_Load_kg": actual_load_L,
            "Reps_Per_Set": reps_L,
            "Sets_Completed": sets_L,
            "RPE": rpe_L,
            "Notes": full_notes
        }
        
        new_row_R = {
            "User": selected_user,
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Exercise": selected_exercise,
            "Arm": "R",
            "1RM_Reference": current_1rm_R,
            "Target_Percentage": target_pct,
            "Prescribed_Load_kg": prescribed_load_R,
            "Actual_Load_kg": actual_load_R,
            "Reps_Per_Set": reps_R,
            "Sets_Completed": sets_R,
            "RPE": rpe_R,
            "Notes": full_notes
        }
        
        if save_workout_to_sheets(worksheet, new_row_L) and save_workout_to_sheets(worksheet, new_row_R):
            st.success(f"✅ Logged {selected_exercise}: L: {actual_load_L}kg x{reps_L} x{sets_L} | R: {actual_load_R}kg x{reps_R} x{sets_R}")
            st.balloons()
            st.cache_resource.clear()
    else:
        st.error("Could not connect to Google Sheets. Check your secrets configuration.")

# Quick navigation
st.markdown("---")
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    st.page_link("pages/2_Progress.py", label="📊 View My Progress →", use_container_width=True)
with col_nav2:
    st.page_link("pages/4_Leaderboard.py", label="🏆 Check Leaderboard →", use_container_width=True)
