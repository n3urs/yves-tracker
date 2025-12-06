import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import json
import gspread
from google.oauth2.service_account import Credentials

# ==================== CONFIG ====================
PLATE_SIZES = [20, 15, 10, 5, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.25]  # kg per side
QUICK_NOTES = {"💪 Strong": "Strong", "😴 Tired": "Tired", "🤕 Hand pain": "Hand pain", "😤 Hard": "Hard", "✨ Great": "Great"}

# List of users - ADD YOUR GYM STAFF NAMES HERE
USER_LIST = ["Oscar", "Yves", "Isaac", "Ian", "Guest"]  # Customize this list!

# Exercise plan data
EXERCISE_PLAN = {
    "20mm Edge": {
        "Schedule": "Monday & Thursday",
        "Frequency": "2x per week",
        "Sets": "3-4 sets",
        "Reps": "3-5 reps per set",
        "Rest": "3-5 min between sets",
        "Intensity": "80-85% 1RM",
        "Technique": [
            "• Grip: Thumb over, fingers on edge (crimp grip)",
            "• Dead hang first 2-3 seconds before pulling",
            "• Keep shoulders packed (avoid shrugging)",
            "• Pull elbows down and back (don't just hang)",
            "• Focus on controlled descent (eccentric)",
            "• Avoid twisting or swinging the body"
        ]
    },
    "Pinch": {
        "Schedule": "Tuesday & Saturday",
        "Frequency": "2x per week",
        "Sets": "3-4 sets",
        "Reps": "5-8 reps per set",
        "Rest": "2-3 min between sets",
        "Intensity": "75-80% 1RM",
        "Technique": [
            "• Grip: Thumb against fingers (pinch hold)",
            "• Hold weight plate between thumb and fingers",
            "• Keep arm straight (don't bend elbow)",
            "• Squeeze hard at the top for 2-3 seconds",
            "• Lower slowly and controlled",
            "• Start with lighter weight to build grip endurance"
        ]
    },
    "Wrist Roller": {
        "Schedule": "Wednesday & Sunday",
        "Frequency": "2x per week",
        "Sets": "2-3 sets",
        "Reps": "Full ROM (up and down)",
        "Rest": "2 min between sets",
        "Intensity": "50-60% 1RM",
        "Technique": [
            "• Hold roller with arms extended at shoulder height",
            "• Roll wrist forward to wrap rope around roller",
            "• Then roll backward to unwrap",
            "• Keep movement slow and controlled",
            "• Full range of motion (flex to extension)",
            "• Can be used for warm-up or conditioning"
        ]
    }
}

# ==================== INIT ====================
st.set_page_config(page_title="Yves Tracker", layout="wide", initial_sidebar_state="collapsed")

# ==================== USER SELECTION ====================
st.title("🧗 Yves Arm-Lifting Tracker")

# User selector at the top
selected_user = st.selectbox("👤 Select User:", USER_LIST, key="user_selector")
st.markdown("---")

# ==================== Google Sheets Connection ====================
@st.cache_resource
def get_google_sheet():
    """Connect to Google Sheets"""
    try:
        # Get credentials from Streamlit secrets
        credentials_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        # Connect to Google Sheets
        client = gspread.authorize(credentials)
        sheet_url = st.secrets["SHEET_URL"]
        sheet = client.open_by_url(sheet_url)
        return sheet.worksheet("Sheet1")  # Use first worksheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def load_data_from_sheets(worksheet, user=None):
    """Load all data from Google Sheet, optionally filtered by user"""
    try:
        data = worksheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            # Filter by user if specified
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            return df
        else:
            # Return empty dataframe with correct columns
            return pd.DataFrame(columns=[
                "User", "Date", "Exercise", "Arm", "1RM_Reference", "Target_Percentage",
                "Prescribed_Load_kg", "Actual_Load_kg", "Reps_Per_Set",
                "Sets_Completed", "RPE", "Notes"
            ])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def save_workout_to_sheets(worksheet, row_data):
    """Append a new workout to the sheet"""
    try:
        worksheet.append_row(list(row_data.values()))
        return True
    except Exception as e:
        st.error(f"Error saving workout: {e}")
        return False

# Connect to sheet
worksheet = get_google_sheet()

# Load 1RMs from session state - now per user
if "saved_1rms" not in st.session_state:
    st.session_state.saved_1rms = {}

# Initialize default 1RMs for current user if not exists
if selected_user not in st.session_state.saved_1rms:
    st.session_state.saved_1rms[selected_user] = {
        "20mm Edge (L)": 105,
        "20mm Edge (R)": 105,
        "Pinch (L)": 85,
        "Pinch (R)": 85,
        "Wrist Roller (L)": 75,
        "Wrist Roller (R)": 75
    }

saved_1rms = st.session_state.saved_1rms[selected_user]

# Initialize goals in session state
if "goals" not in st.session_state:
    st.session_state.goals = {}

if selected_user not in st.session_state.goals:
    st.session_state.goals[selected_user] = []

# ==================== HELPER FUNCTIONS ====================
def calculate_plates(target_kg, pin_kg=1):
    """Find nearest achievable load with exact plate breakdown."""
    load_per_side = (target_kg - pin_kg) / 2
    
    # Try to find exact or very close match
    best_diff = float('inf')
    best_load = target_kg
    best_plates = []
    best_per_side = load_per_side
    
    # Test all possible combinations by trying different target values
    for multiplier in range(int(load_per_side * 4) - 5, int(load_per_side * 4) + 10):
        test_per_side = multiplier / 4
        test_total = test_per_side * 2 + pin_kg
        
        if test_total > target_kg + 3 or test_total < target_kg - 3:
            continue
        
        plates = []
        remaining = test_per_side
        
        for plate in PLATE_SIZES:
            while remaining >= plate - 0.001:
                plates.append(plate)
                remaining -= plate
        
        # Valid combination if remaining is negligible
        if remaining < 0.001:
            diff = abs(test_total - target_kg)
            if diff < best_diff:
                best_diff = diff
                best_load = test_total
                best_plates = sorted(plates, reverse=True)
                best_per_side = test_per_side
    
    if best_plates:
        plates_str = f"{' + '.join(map(str, best_plates))} kg per side"
        if abs(best_load - target_kg) < 0.1:
            return plates_str, best_load
        else:
            return f"{plates_str} (actual: {best_load}kg)", best_load
    
    return "No exact combo found", target_kg

def estimate_1rm_epley(load_kg, reps):
    """Epley formula: 1RM = weight * (1 + reps/30)"""
    if reps == 1:
        return load_kg
    return load_kg * (1 + reps / 30)

def analyze_progression(df_filtered, exercise_name):
    """Analyze recent sessions and suggest progression"""
    suggestions = []
    
    if len(df_filtered) < 3:
        return suggestions
    
    # Get last 3 sessions
    recent = df_filtered.tail(3).copy()
    
    # Check for both arms
    for arm in ["L", "R"]:
        arm_data = recent[recent["Arm"] == arm]
        
        if len(arm_data) < 3:
            continue
        
        # Average RPE of last 3 sessions
        avg_rpe = arm_data["RPE"].mean()
        current_load = arm_data["Actual_Load_kg"].iloc[-1]
        
        # Progression logic
        if avg_rpe <= 6.0:
            # Too easy - suggest increase
            increase = 2.5 if current_load < 60 else 5.0
            new_load = current_load + increase
            suggestions.append({
                "type": "increase",
                "arm": arm,
                "message": f"💪 **{arm} Arm**: RPE averaging {avg_rpe:.1f} (too easy!) → Increase from {current_load:.1f}kg to {new_load:.1f}kg",
                "color": "success"
            })
        elif avg_rpe >= 8.5:
            # Too hard - suggest decrease or same
            suggestions.append({
                "type": "caution",
                "arm": arm,
                "message": f"⚠️ **{arm} Arm**: RPE averaging {avg_rpe:.1f} (very hard) → Stay at {current_load:.1f}kg or reduce slightly",
                "color": "warning"
            })
        else:
            # Just right
            suggestions.append({
                "type": "maintain",
                "arm": arm,
                "message": f"✅ **{arm} Arm**: RPE {avg_rpe:.1f} is perfect! Keep training at {current_load:.1f}kg",
                "color": "info"
            })
    
    return suggestions

def check_deload_needed(df_all):
    """Check if user needs a deload week"""
    if len(df_all) == 0:
        return None
    
    # Get date range
    df_all["Date"] = pd.to_datetime(df_all["Date"])
    df_all = df_all.sort_values("Date")
    
    # Look at last 6 weeks
    six_weeks_ago = datetime.now() - timedelta(weeks=6)
    recent_data = df_all[df_all["Date"] >= six_weeks_ago]
    
    if len(recent_data) == 0:
        return None
    
    # Count weeks with sessions
    recent_data["Week"] = recent_data["Date"].dt.isocalendar().week
    weeks_trained = recent_data["Week"].nunique()
    
    # Check average RPE
    recent_data["RPE"] = pd.to_numeric(recent_data["RPE"], errors='coerce')
    avg_rpe = recent_data["RPE"].mean()
    
    # Deload recommendation logic
    if weeks_trained >= 4:
        if avg_rpe >= 8.0:
            return {
                "needed": True,
                "reason": f"You've trained hard for {weeks_trained} weeks with avg RPE {avg_rpe:.1f}",
                "recommendation": "Consider a deload week: 60-70% intensity, same reps/sets, focus on form"
            }
        elif weeks_trained >= 6:
            return {
                "needed": True,
                "reason": f"You've been training consistently for {weeks_trained} weeks",
                "recommendation": "Time for a planned deload: 60-70% intensity to allow recovery and adaptation"
            }
    
    return {
        "needed": False,
        "message": f"Training load looks good! {weeks_trained} weeks of training, avg RPE {avg_rpe:.1f}"
    }

def create_heatmap(df_all):
    """Create training consistency heatmap (last 12 weeks)"""
    if len(df_all) == 0:
        return None
    
    # Get last 12 weeks
    df_all["Date"] = pd.to_datetime(df_all["Date"])
    twelve_weeks_ago = datetime.now() - timedelta(weeks=12)
    df_recent = df_all[df_all["Date"] >= twelve_weeks_ago]
    
    if len(df_recent) == 0:
        return None
    
    # Count sessions per day
    session_counts = df_recent.groupby("Date").size().reset_index(name="Sessions")
    
    # Create date range for last 12 weeks
    date_range = pd.date_range(end=datetime.now(), periods=84, freq='D')  # 12 weeks = 84 days
    
    # Create heatmap data (7 rows x 12 columns = 84 days)
    heatmap_data = np.zeros((7, 12))  # 7 days, 12 weeks
    
    for i, date in enumerate(date_range):
        week_idx = i // 7
        day_idx = i % 7
        
        # Check if there's a session on this date
        sessions = session_counts[session_counts["Date"] == date.date()]
        if len(sessions) > 0:
            heatmap_data[day_idx, week_idx] = sessions["Sessions"].values[0]
    
    return heatmap_data, date_range

# ==================== SIDEBAR: 1RM MANAGER ====================
st.sidebar.header(f"💾 {selected_user}'s 1RM Manager")
st.sidebar.subheader("Save your max lifts:")

exercise_list = [
    "20mm Edge", 
    "Pinch", 
    "Wrist Roller",
    "─────────────────",  # Separator
    "1RM Test: 20mm Edge",
    "1RM Test: Pinch",
    "1RM Test: Wrist Roller"
]

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

st.sidebar.markdown("---")

# ==================== SIDEBAR: GOAL TRACKER ====================
st.sidebar.header("🎯 Goal Tracker")

# Add new goal form
with st.sidebar.expander("➕ Add New Goal"):
    goal_exercise = st.selectbox("Exercise", base_exercises, key="goal_exercise")
    goal_arm = st.selectbox("Arm", ["Left", "Right", "Both"], key="goal_arm")
    goal_weight = st.number_input("Target Weight (kg)", min_value=20, max_value=200, value=60, step=5, key="goal_weight")
    goal_date = st.date_input("Target Date", value=datetime.now() + timedelta(weeks=8), key="goal_date")
    
    if st.button("Add Goal", key="add_goal_btn"):
        new_goal = {
            "exercise": goal_exercise,
            "arm": goal_arm,
            "target_weight": goal_weight,
            "target_date": goal_date.strftime("%Y-%m-%d"),
            "created_date": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state.goals[selected_user].append(new_goal)
        st.sidebar.success("🎉 Goal added!")

# Display active goals
if len(st.session_state.goals[selected_user]) > 0:
    st.sidebar.subheader("Active Goals:")
    for idx, goal in enumerate(st.session_state.goals[selected_user]):
        with st.sidebar.container():
            st.write(f"**{goal['exercise']} ({goal['arm']})**")
            st.write(f"🎯 Target: {goal['target_weight']}kg by {goal['target_date']}")
            
            # Calculate progress
            if worksheet:
                df_user = load_data_from_sheets(worksheet, user=selected_user)
                if len(df_user) > 0:
                    df_user["Date"] = pd.to_datetime(df_user["Date"])
                    df_user["Actual_Load_kg"] = pd.to_numeric(df_user["Actual_Load_kg"], errors='coerce')
                    
                    # Filter for this exercise
                    df_exercise = df_user[df_user["Exercise"] == goal['exercise']]
                    
                    if len(df_exercise) > 0:
                        # Get current max for the arm
                        if goal['arm'] == "Both":
                            current_max = df_exercise['Actual_Load_kg'].max()
                        else:
                            arm_letter = "L" if goal['arm'] == "Left" else "R"
                            df_arm = df_exercise[df_exercise["Arm"] == arm_letter]
                            current_max = df_arm['Actual_Load_kg'].max() if len(df_arm) > 0 else 0
                        
                        # Calculate progress percentage
                        progress = (current_max / goal['target_weight']) * 100
                        progress = min(progress, 100)  # Cap at 100%
                        
                        st.progress(progress / 100, text=f"{progress:.0f}% complete ({current_max:.1f}kg / {goal['target_weight']}kg)")
                        
                        # Days remaining
                        days_left = (datetime.strptime(goal['target_date'], "%Y-%m-%d") - datetime.now()).days
                        if days_left > 0:
                            st.caption(f"⏰ {days_left} days remaining")
                        else:
                            st.caption("🏁 Goal date passed")
            
            # Delete goal button
            if st.button(f"🗑️ Delete", key=f"delete_goal_{idx}"):
                st.session_state.goals[selected_user].pop(idx)
                st.rerun()
            
            st.markdown("---")
else:
    st.sidebar.info("No goals set yet. Add one above!")

st.sidebar.markdown("---")

# ==================== SIDEBAR: EXERCISE PLAN ====================
st.sidebar.header("📋 Exercise Plan")

if st.sidebar.button("📖 View Plan", key="view_plan_btn", use_container_width=True):
    st.session_state.show_plan = not st.session_state.get("show_plan", False)

if st.session_state.get("show_plan", False):
    st.sidebar.markdown("---")
    selected_plan_exercise = st.sidebar.selectbox("Choose exercise:", base_exercises, key="plan_select")
    plan = EXERCISE_PLAN[selected_plan_exercise]
    
    st.sidebar.subheader(f"📅 {selected_plan_exercise}")
    st.sidebar.write(f"**Schedule:** {plan['Schedule']}")
    st.sidebar.write(f"**Frequency:** {plan['Frequency']}")
    st.sidebar.write(f"**Sets:** {plan['Sets']}")
    st.sidebar.write(f"**Reps:** {plan['Reps']}")
    st.sidebar.write(f"**Rest:** {plan['Rest']}")
    st.sidebar.write(f"**Intensity:** {plan['Intensity']}")
    
    st.sidebar.subheader("🎯 Technique Tips:")
    for tip in plan['Technique']:
        st.sidebar.write(tip)
    
    st.sidebar.markdown("---")

# ==================== SIDEBAR: CALCULATOR ====================
st.sidebar.header("⚙️ Calculator")

selected_exercise = st.sidebar.selectbox("Exercise", exercise_list, key="exercise_select")

# Only show calculator for non-separator and non-1RM test exercises
if selected_exercise != "─────────────────" and not selected_exercise.startswith("1RM Test:"):
    current_1rm_L = saved_1rms.get(f"{selected_exercise} (L)", 105)
    current_1rm_R = saved_1rms.get(f"{selected_exercise} (R)", 105)

    intensity_options = {"50% Warm-up": 0.50, "60% Warm-up": 0.60, "70% Warm-up": 0.70, "80% Work": 0.80, "Custom": None}
    intensity_label = st.sidebar.selectbox("Intensity", list(intensity_options.keys()), key="intensity_select")

    if intensity_label == "Custom":
        target_pct = st.sidebar.slider("Custom %", min_value=0.3, max_value=1.0, step=0.05, value=0.8)
    else:
        target_pct = intensity_options[intensity_label]

    prescribed_load_L = current_1rm_L * target_pct
    prescribed_load_R = current_1rm_R * target_pct

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📊 Left Arm: **{prescribed_load_L:.1f} kg**")
    plates_str_L, actual_load_L = calculate_plates(prescribed_load_L)
    st.sidebar.write(f"**Plates:** {plates_str_L}")
    
    st.sidebar.subheader(f"📊 Right Arm: **{prescribed_load_R:.1f} kg**")
    plates_str_R, actual_load_R = calculate_plates(prescribed_load_R)
    st.sidebar.write(f"**Plates:** {plates_str_R}")
else:
    if selected_exercise.startswith("1RM Test:"):
        st.sidebar.info("💡 For 1RM tests, enter the maximum weight you can lift for 1 rep.")
    prescribed_load_L = 100.0  # Default for 1RM tests
    prescribed_load_R = 100.0
    current_1rm_L = 100.0
    current_1rm_R = 100.0
    target_pct = 1.0

# ==================== DELOAD CHECK (SIDEBAR) ====================
st.sidebar.markdown("---")
st.sidebar.header("🔋 Recovery Status")

if worksheet:
    df_all_user = load_data_from_sheets(worksheet, user=selected_user)
    deload_status = check_deload_needed(df_all_user)
    
    if deload_status:
        if deload_status.get("needed"):
            st.sidebar.warning(f"⚠️ **Deload Recommended**")
            st.sidebar.write(deload_status["reason"])
            st.sidebar.info(f"💡 {deload_status['recommendation']}")
        else:
            st.sidebar.success("✅ Recovery looks good!")
            st.sidebar.write(deload_status.get("message", "Keep training!"))

# ==================== MAIN: LOG FORM ====================
st.header("📝 Log Today's Session")

# Checkbox for same weight both arms
same_weight = st.checkbox("✅ Same weight both arms", value=True, key="same_weight_check")

if same_weight:
    # Single column layout when same weight
    st.subheader("Both Arms")
    actual_load = st.number_input("Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load_L, step=0.5, key="load_both")
    reps = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1, key="reps_both")
    sets = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1, key="sets_both")
    rpe = st.slider("RPE (Rate of Perceived Exertion)", min_value=1, max_value=10, value=7, key="rpe_both")
    
    # Use same values for both arms
    actual_load_L = actual_load_R = actual_load
    reps_L = reps_R = reps
    sets_L = sets_R = sets
    rpe_L = rpe_R = rpe
else:
    # Two columns for Left and Right
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

# Shared notes at bottom
quick_note = st.selectbox("Quick note:", ["None"] + list(QUICK_NOTES.keys()), key="quick_note_select")
quick_note_text = QUICK_NOTES.get(quick_note, "") if quick_note != "None" else ""
notes = st.text_input("Custom notes (optional)", placeholder="e.g., felt strong, hand pain, etc.")
full_notes = f"{quick_note_text} {notes}".strip()

# ==================== SAVE BUTTON ====================
if st.button("✅ Save Workout (Both Arms)", key="save_btn", use_container_width=True):
    if worksheet and selected_exercise != "─────────────────":
        # Save Left Arm
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
        
        # Save Right Arm
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
            # Clear cache to reload fresh data
            st.cache_resource.clear()
    else:
        st.error("Could not connect to Google Sheets. Check your secrets configuration.")

# ==================== ANALYTICS ====================
st.markdown("---")
st.header(f"📈 {selected_user}'s Progress")

# Load fresh data from sheets - filtered by current user
if worksheet:
    df_fresh = load_data_from_sheets(worksheet, user=selected_user)
    
    if len(df_fresh) > 0:
        # Filter exercise options - ONLY show base exercises (not 1RM tests) in dropdown
        exercise_options = [ex for ex in df_fresh["Exercise"].unique().tolist() if not ex.startswith("1RM Test:")]
        
        if len(exercise_options) > 0:
            selected_analysis_exercise = st.selectbox("View progress for:", exercise_options, key="analysis_exercise")
            
            df_filtered = df_fresh[df_fresh["Exercise"] == selected_analysis_exercise].copy()
            
            # Convert date and numeric columns BEFORE separating arms
            df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
            df_filtered = df_filtered.sort_values("Date").reset_index(drop=True)
            
            # Convert numeric columns
            numeric_cols = ["1RM_Reference", "Target_Percentage", "Prescribed_Load_kg", 
                           "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE"]
            for col in numeric_cols:
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
            
            # Estimate 1RM from rep data - FIX: Don't inflate 1-rep sets
            df_filtered["Estimated_1RM"] = df_filtered.apply(
                lambda row: row["Actual_Load_kg"] if row["Reps_Per_Set"] == 1 
                else estimate_1rm_epley(row["Actual_Load_kg"], row["Reps_Per_Set"]),
                axis=1
            )
            
            # NOW separate Left and Right (after all conversions)
            df_left = df_filtered[df_filtered["Arm"] == "L"].copy()
            df_right = df_filtered[df_filtered["Arm"] == "R"].copy()
            
            # ==================== PROGRESSION SUGGESTIONS ====================
            if len(df_filtered) >= 3:
                st.markdown("---")
                st.subheader("🎯 Training Recommendations")
                
                suggestions = analyze_progression(df_filtered, selected_analysis_exercise)
                
                if suggestions:
                    for suggestion in suggestions:
                        if suggestion["type"] == "increase":
                            st.success(suggestion["message"])
                        elif suggestion["type"] == "caution":
                            st.warning(suggestion["message"])
                        else:
                            st.info(suggestion["message"])
                else:
                    st.info("Keep training! Need at least 3 sessions for recommendations.")
                
                st.markdown("---")
            
            # Get 1RM test data for reference table
            test_exercise_name = f"1RM Test: {selected_analysis_exercise}"
            df_tests = df_fresh[df_fresh["Exercise"] == test_exercise_name].copy()
            
            # Layout: Metrics on top, then 1RM reference table on the side
            col_metrics, col_1rm_ref = st.columns([3, 1])
            
            with col_metrics:
                # Metrics - Show both arms
                if len(df_left) > 0 or len(df_right) > 0:
                    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                    with col_metric1:
                        best_L = df_left['Actual_Load_kg'].max() if len(df_left) > 0 else 0
                        st.metric("Best Load (L)", f"{best_L:.1f} kg")
                    with col_metric2:
                        best_R = df_right['Actual_Load_kg'].max() if len(df_right) > 0 else 0
                        st.metric("Best Load (R)", f"{best_R:.1f} kg")
                    with col_metric3:
                        vol_L = (df_left["Actual_Load_kg"] * df_left["Reps_Per_Set"] * df_left["Sets_Completed"]).sum() if len(df_left) > 0 else 0
                        vol_R = (df_right["Actual_Load_kg"] * df_right["Reps_Per_Set"] * df_right["Sets_Completed"]).sum() if len(df_right) > 0 else 0
                        st.metric("Volume (L)", f"{vol_L:.0f} kg")
                        st.caption(f"R: {vol_R:.0f} kg")
                    with col_metric4:
                        # Count unique dates (sessions) instead of rows
                        unique_sessions = df_filtered["Date"].nunique()
                        st.metric("Sessions", f"{unique_sessions}")
            
            with col_1rm_ref:
                # 1RM Test Reference Table
                st.markdown("#### 🎯 Latest 1RM Tests")
                if len(df_tests) > 0:
                    df_tests["Date"] = pd.to_datetime(df_tests["Date"])
                    df_tests["Actual_Load_kg"] = pd.to_numeric(df_tests["Actual_Load_kg"], errors='coerce')
                    
                    # Get most recent test for each arm
                    df_tests_sorted = df_tests.sort_values("Date", ascending=False)
                    latest_L = df_tests_sorted[df_tests_sorted["Arm"] == "L"].head(1)
                    latest_R = df_tests_sorted[df_tests_sorted["Arm"] == "R"].head(1)
                    
                    if len(latest_L) > 0:
                        st.write(f"**L:** {latest_L.iloc[0]['Actual_Load_kg']:.1f} kg")
                        st.caption(f"{latest_L.iloc[0]['Date'].strftime('%Y-%m-%d')}")
                    else:
                        st.write("**L:** No test yet")
                    
                    if len(latest_R) > 0:
                        st.write(f"**R:** {latest_R.iloc[0]['Actual_Load_kg']:.1f} kg")
                        st.caption(f"{latest_R.iloc[0]['Date'].strftime('%Y-%m-%d')}")
                    else:
                        st.write("**R:** No test yet")
                else:
                    st.caption("No 1RM tests logged yet")
            
            # Charts - Both arms on same graph with different markers to avoid overlap
            st.subheader("Load Over Time (Both Arms)")
            fig, ax = plt.subplots(figsize=(12, 4))
            
            # Plot Left Arm - CIRCLES
            if len(df_left) > 0:
                ax.plot(df_left["Date"], df_left["Actual_Load_kg"], 
                        marker="o", label="Left - Actual Load", linewidth=2, markersize=10, 
                        color="blue", alpha=0.8, markeredgewidth=2, markeredgecolor='darkblue')
                ax.plot(df_left["Date"], df_left["Estimated_1RM"], 
                        marker="s", label="Left - Estimated 1RM", linewidth=2, markersize=7, 
                        linestyle="--", color="lightblue", alpha=0.7)
            
            # Plot Right Arm - TRIANGLES
            if len(df_right) > 0:
                ax.plot(df_right["Date"], df_right["Actual_Load_kg"], 
                        marker="^", label="Right - Actual Load", linewidth=2, markersize=10, 
                        color="green", alpha=0.8, markeredgewidth=2, markeredgecolor='darkgreen')
                ax.plot(df_right["Date"], df_right["Estimated_1RM"], 
                        marker="s", label="Right - Estimated 1RM", linewidth=2, markersize=7, 
                        linestyle="--", color="lightgreen", alpha=0.7)
            
            ax.set_xlabel("Date")
            ax.set_ylabel("Load (kg)")
            ax.set_title(f"{selected_analysis_exercise} Progress (L vs R)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
            # RPE Trend - Both arms
            st.subheader("RPE Trend (Both Arms)")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            if len(df_left) > 0:
                ax2.plot(df_left["Date"], df_left["RPE"], marker="o", color="blue", linewidth=2, markersize=8, label="Left Arm", alpha=0.8)
            if len(df_right) > 0:
                ax2.plot(df_right["Date"], df_right["RPE"], marker="^", color="green", linewidth=2, markersize=8, label="Right Arm", alpha=0.8)
            ax2.set_xlabel("Date")
            ax2.set_ylabel("RPE")
            ax2.set_ylim([0, 10])
            ax2.set_title(f"Perceived Effort Over Time")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
            
            # Data table - Both arms combined
            st.subheader("Workout Log")
            display_cols = ["Date", "Arm", "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE", "Notes"]
            st.dataframe(df_filtered[display_cols].sort_values(["Date", "Arm"], ascending=[False, True]), use_container_width=True, hide_index=True)
        else:
            st.info(f"No training workouts logged yet for {selected_user}. Only 1RM tests found.")
    
    else:
        st.info(f"No workouts logged yet for {selected_user}. Start by logging your first session above!")
    
    # ==================== TRAINING CONSISTENCY HEATMAP ====================
    st.markdown("---")
    st.subheader("📅 Training Consistency (Last 12 Weeks)")
    
    heatmap_result = create_heatmap(df_fresh)
    if heatmap_result:
        heatmap_data, date_range = heatmap_result
        
        fig3, ax3 = plt.subplots(figsize=(14, 3))
        
        # Create heatmap
        im = ax3.imshow(heatmap_data, cmap='Greens', aspect='auto', vmin=0, vmax=3)
        
        # Set ticks
        ax3.set_yticks(np.arange(7))
        ax3.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        ax3.set_xticks(np.arange(12))
        ax3.set_xticklabels([f'W{i+1}' for i in range(12)])
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax3, orientation='horizontal', pad=0.1)
        cbar.set_label('Sessions per day', rotation=0)
        
        ax3.set_title("Training Frequency Heatmap (Green = More Sessions)")
        plt.tight_layout()
        st.pyplot(fig3)
        
        # Training streak
        df_fresh_sorted = df_fresh.sort_values("Date")
        df_fresh_sorted["Date"] = pd.to_datetime(df_fresh_sorted["Date"])
        unique_dates = df_fresh_sorted["Date"].dt.date.unique()
        
        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        
        if len(unique_dates) > 0 and unique_dates[-1] == today:
            current_streak = 1
            for i in range(len(unique_dates) - 2, -1, -1):
                if (unique_dates[i+1] - unique_dates[i]).days == 1:
                    current_streak += 1
                else:
                    break
        
        if current_streak > 0:
            st.success(f"🔥 **Current Streak: {current_streak} days!** Keep it up!")
        else:
            st.info("💪 Start a new training streak today!")
    else:
        st.info("Not enough data yet for heatmap. Keep logging workouts!")
    
else:
    st.error("Could not connect to Google Sheets. Check your configuration.")
