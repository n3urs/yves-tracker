
import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io

# ==================== CONFIG ====================
PLATE_SIZES = [20, 15, 10, 5, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.25]
QUICK_NOTES = {"💪 Strong": "Strong", "😴 Tired": "Tired", "🤕 Hand pain": "Hand pain", "😤 Hard": "Hard", "✨ Great": "Great"}
USER_LIST = ["Oscar", "Yves", "Isaac", "Ian", "Guest"]

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

# ==================== GOOGLE SHEETS ====================
@st.cache_resource
def get_google_sheet():
    """Connect to Google Sheets"""
    try:
        credentials_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        sheet_url = st.secrets["SHEET_URL"]
        sheet = client.open_by_url(sheet_url)
        return sheet.worksheet("Sheet1")
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def load_data_from_sheets(worksheet, user=None):
    """Load all data from Google Sheet, optionally filtered by user"""
    try:
        data = worksheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            return df
        else:
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

# ==================== HELPER FUNCTIONS ====================
def calculate_plates(target_kg, pin_kg=1):
    """Find nearest achievable load with exact plate breakdown."""
    load_per_side = (target_kg - pin_kg) / 2
    best_diff = float('inf')
    best_load = target_kg
    best_plates = []
    
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
        
        if remaining < 0.001:
            diff = abs(test_total - target_kg)
            if diff < best_diff:
                best_diff = diff
                best_load = test_total
                best_plates = sorted(plates, reverse=True)
    
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

def get_bodyweight(user):
    """Get user's bodyweight from session state"""
    if "bodyweights" not in st.session_state:
        st.session_state.bodyweights = {
            "Oscar": 70.0,
            "Yves": 75.0,
            "Isaac": 68.0,
            "Ian": 80.0,
            "Guest": 70.0
        }
    return st.session_state.bodyweights.get(user, 70.0)

def set_bodyweight(user, weight):
    """Set user's bodyweight"""
    if "bodyweights" not in st.session_state:
        st.session_state.bodyweights = {}
    st.session_state.bodyweights[user] = weight

def calculate_relative_strength(absolute_kg, bodyweight_kg):
    """Calculate strength relative to bodyweight"""
    return absolute_kg / bodyweight_kg

def init_session_state():
    """Initialize all session state variables"""
    if "current_user" not in st.session_state:
        st.session_state.current_user = "Oscar"
    
    if "saved_1rms" not in st.session_state:
        st.session_state.saved_1rms = {}
    
    if "goals" not in st.session_state:
        st.session_state.goals = {}
    
    # Initialize defaults for current user
    if st.session_state.current_user not in st.session_state.saved_1rms:
        st.session_state.saved_1rms[st.session_state.current_user] = {
            "20mm Edge (L)": 105,
            "20mm Edge (R)": 105,
            "Pinch (L)": 85,
            "Pinch (R)": 85,
            "Wrist Roller (L)": 75,
            "Wrist Roller (R)": 75
        }
    
    if st.session_state.current_user not in st.session_state.goals:
        st.session_state.goals[st.session_state.current_user] = []

def generate_workout_summary_image(df_data, username, days_back):
    """Generate a beautiful social media-ready workout summary"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    df_data["Date"] = pd.to_datetime(df_data["Date"])
    df_period = df_data[df_data["Date"] >= cutoff_date].copy()
    
    if len(df_period) == 0:
        return None
    
    numeric_cols = ["Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE"]
    for col in numeric_cols:
        df_period[col] = pd.to_numeric(df_period[col], errors='coerce')
    
    total_sessions = df_period["Date"].nunique()
    total_volume = (df_period["Actual_Load_kg"] * df_period["Reps_Per_Set"] * df_period["Sets_Completed"]).sum()
    avg_rpe = df_period["RPE"].mean()
    
    prs = {}
    for exercise in df_period["Exercise"].unique():
        if not exercise.startswith("1RM Test"):
            df_ex = df_period[df_period["Exercise"] == exercise]
            max_load = df_ex["Actual_Load_kg"].max()
            prs[exercise] = max_load
    
    fig = plt.figure(figsize=(10, 12), facecolor='#1a1a2e')
    
    fig.text(0.5, 0.95, f"{username}'s Training Summary", 
             ha='center', va='top', fontsize=32, fontweight='bold', color='white')
    
    period_text = f"Last {days_back} Days" if days_back < 30 else f"Last {days_back//30} Month{'s' if days_back >= 60 else ''}"
    fig.text(0.5, 0.91, period_text, 
             ha='center', va='top', fontsize=18, color='#00d4ff', style='italic')
    
    stats_y = 0.82
    box_width = 0.25
    box_height = 0.12
    
    rect1 = mpatches.FancyBboxPatch((0.08, stats_y-box_height), box_width, box_height,
                                     boxstyle="round,pad=0.01", 
                                     facecolor='#16213e', edgecolor='#00d4ff', linewidth=2,
                                     transform=fig.transFigure)
    fig.patches.append(rect1)
    fig.text(0.08 + box_width/2, stats_y - 0.03, f"{total_sessions}", 
             ha='center', va='center', fontsize=36, fontweight='bold', color='#00d4ff')
    fig.text(0.08 + box_width/2, stats_y - 0.08, "Sessions", 
             ha='center', va='center', fontsize=14, color='white')
    
    rect2 = mpatches.FancyBboxPatch((0.375, stats_y-box_height), box_width, box_height,
                                     boxstyle="round,pad=0.01", 
                                     facecolor='#16213e', edgecolor='#00ff88', linewidth=2,
                                     transform=fig.transFigure)
    fig.patches.append(rect2)
    fig.text(0.375 + box_width/2, stats_y - 0.03, f"{total_volume:.0f}", 
             ha='center', va='center', fontsize=36, fontweight='bold', color='#00ff88')
    fig.text(0.375 + box_width/2, stats_y - 0.08, "Total Volume (kg)", 
             ha='center', va='center', fontsize=14, color='white')
    
    rect3 = mpatches.FancyBboxPatch((0.67, stats_y-box_height), box_width, box_height,
                                     boxstyle="round,pad=0.01", 
                                     facecolor='#16213e', edgecolor='#ff6b6b', linewidth=2,
                                     transform=fig.transFigure)
    fig.patches.append(rect3)
    fig.text(0.67 + box_width/2, stats_y - 0.03, f"{avg_rpe:.1f}", 
             ha='center', va='center', fontsize=36, fontweight='bold', color='#ff6b6b')
    fig.text(0.67 + box_width/2, stats_y - 0.08, "Avg RPE", 
             ha='center', va='center', fontsize=14, color='white')
    
    prs_y = 0.62
    fig.text(0.5, prs_y, "🏆 Personal Records", 
             ha='center', va='center', fontsize=24, fontweight='bold', color='#ffd700')
    
    pr_start_y = prs_y - 0.06
    for i, (exercise, weight) in enumerate(prs.items()):
        y_pos = pr_start_y - (i * 0.05)
        fig.text(0.2, y_pos, f"• {exercise}:", 
                 ha='left', va='center', fontsize=16, color='white')
        fig.text(0.8, y_pos, f"{weight:.1f} kg", 
                 ha='right', va='center', fontsize=18, fontweight='bold', color='#00ff88')
    
    chart_y = 0.35
    ax = fig.add_axes([0.1, chart_y - 0.25, 0.8, 0.2])
    
    df_period_sorted = df_period.sort_values("Date")
    df_period_sorted["Volume"] = df_period_sorted["Actual_Load_kg"] * df_period_sorted["Reps_Per_Set"] * df_period_sorted["Sets_Completed"]
    daily_volume = df_period_sorted.groupby("Date")["Volume"].sum()
    
    ax.fill_between(daily_volume.index, daily_volume.values, alpha=0.3, color='#00d4ff')
    ax.plot(daily_volume.index, daily_volume.values, linewidth=3, color='#00d4ff', marker='o', markersize=6)
    
    ax.set_facecolor('#16213e')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.tick_params(colors='white', labelsize=10)
    ax.set_xlabel('Date', color='white', fontsize=12)
    ax.set_ylabel('Daily Volume (kg)', color='white', fontsize=12)
    ax.grid(True, alpha=0.2, color='white')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    fig.text(0.5, 0.05, "💪 Keep Crushing It! 🧗", 
             ha='center', va='center', fontsize=20, color='white', style='italic')
    fig.text(0.5, 0.02, "Generated by Yves Tracker", 
             ha='center', va='center', fontsize=10, color='#666666')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor='#1a1a2e', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return buf
