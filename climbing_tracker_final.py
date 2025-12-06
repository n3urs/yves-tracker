import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
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
    "20mm Edge (L)": {
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
    "20mm Edge (R)": {
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
    "Pinch (L)": {
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
    "Pinch (R)": {
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
    "Wrist Roller (L)": {
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
    },
    "Wrist Roller (R)": {
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
                "User", "Date", "Exercise", "1RM_Reference", "Target_Percentage",
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

# ==================== SIDEBAR: 1RM MANAGER ====================
st.sidebar.header(f"💾 {selected_user}'s 1RM Manager")
st.sidebar.subheader("Save your max lifts:")

exercise_list = [
    "20mm Edge (L)", 
    "20mm Edge (R)", 
    "Pinch (L)", 
    "Pinch (R)", 
    "Wrist Roller (L)", 
    "Wrist Roller (R)",
    "─────────────────",  # Separator
    "1RM Test: 20mm Edge (L)",
    "1RM Test: 20mm Edge (R)",
    "1RM Test: Pinch (L)",
    "1RM Test: Pinch (R)",
    "1RM Test: Wrist Roller (L)",
    "1RM Test: Wrist Roller (R)"
]

for ex in ["20mm Edge (L)", "20mm Edge (R)", "Pinch (L)", "Pinch (R)", "Wrist Roller (L)", "Wrist Roller (R)"]:
    saved_1rms[ex] = st.sidebar.number_input(
        f"{ex} MVC-7 (kg)",
        min_value=20,
        max_value=200,
        value=saved_1rms.get(ex, 105),
        step=1,
        key=f"1rm_{ex}_{selected_user}"
    )

if st.sidebar.button("💾 Save All 1RMs", key="save_1rms_btn", use_container_width=True):
    st.session_state.saved_1rms[selected_user] = saved_1rms
    st.sidebar.success("✅ 1RMs saved!")

st.sidebar.markdown("---")

# ==================== SIDEBAR: EXERCISE PLAN ====================
st.sidebar.header("📋 Exercise Plan")

if st.sidebar.button("📖 View Plan", key="view_plan_btn", use_container_width=True):
    st.session_state.show_plan = not st.session_state.get("show_plan", False)

if st.session_state.get("show_plan", False):
    st.sidebar.markdown("---")
    base_exercises = ["20mm Edge (L)", "20mm Edge (R)", "Pinch (L)", "Pinch (R)", "Wrist Roller (L)", "Wrist Roller (R)"]
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
    current_1rm = saved_1rms.get(selected_exercise, 105)

    intensity_options = {"50% Warm-up": 0.50, "60% Warm-up": 0.60, "70% Warm-up": 0.70, "80% Work": 0.80, "Custom": None}
    intensity_label = st.sidebar.selectbox("Intensity", list(intensity_options.keys()), key="intensity_select")

    if intensity_label == "Custom":
        target_pct = st.sidebar.slider("Custom %", min_value=0.3, max_value=1.0, step=0.05, value=0.8)
    else:
        target_pct = intensity_options[intensity_label]

    prescribed_load = current_1rm * target_pct

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📊 Target Load: **{prescribed_load:.1f} kg**")

    plates_str, actual_load = calculate_plates(prescribed_load)
    st.sidebar.write(f"**Plates:** {plates_str}")
    st.sidebar.write(f"**Total weight: {actual_load:.1f} kg**")
else:
    if selected_exercise.startswith("1RM Test:"):
        st.sidebar.info("💡 For 1RM tests, enter the maximum weight you can lift for 1 rep.")
    prescribed_load = 100.0  # Default for 1RM tests
    current_1rm = 100.0
    target_pct = 1.0

# ==================== MAIN: LOG FORM ====================
st.header("📝 Log Today's Session")

# Desktop layout (3 columns per row)
col1, col2, col3 = st.columns(3)
with col1:
    actual_load_input = st.number_input("Actual Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load, step=0.5)
with col2:
    reps = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1)
with col3:
    sets = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1)

col4, col5, col6 = st.columns(3)
with col4:
    rpe = st.slider("RPE (Rate of Perceived Exertion)", min_value=1, max_value=10, value=7)
with col5:
    quick_note = st.selectbox("Quick note:", ["None"] + list(QUICK_NOTES.keys()), key="quick_note_select")
    quick_note_text = QUICK_NOTES.get(quick_note, "") if quick_note != "None" else ""
with col6:
    notes = st.text_input("Custom notes (optional)", placeholder="e.g., felt strong, hand pain, etc.")

full_notes = f"{quick_note_text} {notes}".strip()

# ==================== SAVE BUTTON ====================
if st.button("✅ Save Workout", key="save_btn", use_container_width=True):
    if worksheet and selected_exercise != "─────────────────":
        new_row = {
            "User": selected_user,  # Add user to the data
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Exercise": selected_exercise,
            "1RM_Reference": current_1rm,
            "Target_Percentage": target_pct,
            "Prescribed_Load_kg": prescribed_load,
            "Actual_Load_kg": actual_load_input,
            "Reps_Per_Set": reps,
            "Sets_Completed": sets,
            "RPE": rpe,
            "Notes": full_notes
        }
        
        if save_workout_to_sheets(worksheet, new_row):
            st.success(f"✅ Logged {selected_exercise}: {actual_load_input} kg x {reps} x {sets} @ RPE {rpe}")
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
        # Filter by exercise
        exercise_options = df_fresh["Exercise"].unique().tolist()
        selected_analysis_exercise = st.selectbox("View progress for:", exercise_options, key="analysis_exercise")
        
        df_filtered = df_fresh[df_fresh["Exercise"] == selected_analysis_exercise].copy()
        df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
        df_filtered = df_filtered.sort_values("Date").reset_index(drop=True)
        
        # Convert numeric columns
        numeric_cols = ["1RM_Reference", "Target_Percentage", "Prescribed_Load_kg", 
                       "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE"]
        for col in numeric_cols:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
        
        # Estimate 1RM from rep data
        df_filtered["Estimated_1RM"] = df_filtered.apply(
            lambda row: estimate_1rm_epley(row["Actual_Load_kg"], row["Reps_Per_Set"]),
            axis=1
        )
        
        # Metrics
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        with col_metric1:
            st.metric("Best Actual Load", f"{df_filtered['Actual_Load_kg'].max():.1f} kg")
        with col_metric2:
            st.metric("Avg RPE (Recent 5)", f"{df_filtered.tail(5)['RPE'].mean():.1f} / 10")
        with col_metric3:
            total_volume = (df_filtered["Actual_Load_kg"] * df_filtered["Reps_Per_Set"] * df_filtered["Sets_Completed"]).sum()
            st.metric("Total Volume", f"{total_volume:.0f} kg")
        with col_metric4:
            sessions_count = len(df_filtered)
            st.metric("Sessions Logged", sessions_count)
        
        # Charts
        st.subheader("Load Over Time")
        fig, ax = plt.subplots(figsize=(12, 4))
        
        # Plot actual working loads
        ax.plot(df_filtered["Date"], df_filtered["Actual_Load_kg"], 
                marker="o", label="Actual Load", linewidth=2, markersize=6, color="blue")
        
        # Plot estimated 1RM
        ax.plot(df_filtered["Date"], df_filtered["Estimated_1RM"], 
                marker="s", label="Estimated 1RM (Epley)", linewidth=2, markersize=6, 
                linestyle="--", color="orange")
        
        # Get actual 1RM tests for this exercise (if any exist)
        base_exercise = selected_analysis_exercise.replace("1RM Test: ", "")
        test_exercise_name = f"1RM Test: {base_exercise}"
        
        # Load ALL data to find 1RM tests
        df_all = load_data_from_sheets(worksheet, user=selected_user)
        if len(df_all) > 0:
            df_tests = df_all[df_all["Exercise"] == test_exercise_name].copy()
            if len(df_tests) > 0:
                df_tests["Date"] = pd.to_datetime(df_tests["Date"])
                df_tests["Actual_Load_kg"] = pd.to_numeric(df_tests["Actual_Load_kg"], errors='coerce')
                df_tests = df_tests.sort_values("Date")
                
                # Plot 1RM test results as stars
                ax.scatter(df_tests["Date"], df_tests["Actual_Load_kg"], 
                          marker="*", s=300, label="Actual 1RM Test", 
                          color="red", zorder=5, edgecolors='black', linewidths=1)
        
        ax.set_xlabel("Date")
        ax.set_ylabel("Load (kg)")
        ax.set_title(f"{selected_analysis_exercise} Progress")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        
        st.subheader("RPE Trend")
        fig2, ax2 = plt.subplots(figsize=(12, 4))
        ax2.plot(df_filtered["Date"], df_filtered["RPE"], marker="o", color="orange", linewidth=2, markersize=6)
        ax2.set_xlabel("Date")
        ax2.set_ylabel("RPE")
        ax2.set_ylim([0, 10])
        ax2.set_title(f"Perceived Effort Over Time")
        ax2.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
        
        # Data table (view only)
        st.subheader("Workout Log")
        display_cols = ["Date", "Exercise", "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE", "Notes"]
        st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)
    
    else:
        st.info(f"No workouts logged yet for {selected_user}. Start by logging your first session above!")
else:
    st.error("Could not connect to Google Sheets. Check your configuration.")
