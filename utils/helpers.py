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
USER_LIST = ["Oscar", "Ian"]  # Initial users - more can be added via Profile page

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

# ==================== SESSION STATE ====================
def init_session_state():
    """Initialize session state variables if they don't exist"""
    if "current_user" not in st.session_state:
        st.session_state.current_user = USER_LIST[0]
    
    if "bodyweights" not in st.session_state:
        st.session_state.bodyweights = {user: 78.0 for user in USER_LIST}
    
    if "saved_1rms" not in st.session_state:
        st.session_state.saved_1rms = {}
    
    if "goals" not in st.session_state:
        st.session_state.goals = {}

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

def load_users_from_sheets(worksheet):
    """Load unique users from Google Sheets"""
    try:
        data = worksheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            if "User" in df.columns:
                users = sorted(df["User"].unique().tolist())
                return users if users else USER_LIST.copy()
        return USER_LIST.copy()
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return USER_LIST.copy()

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

def calculate_relative_strength(avg_load, bodyweight):
    """Calculate relative strength: load / bodyweight"""
    if bodyweight is not None and bodyweight > 0:
        return avg_load / bodyweight
    return 0

def get_bodyweight(user):
    """Get user's bodyweight from session state"""
    if "bodyweights" not in st.session_state:
        st.session_state.bodyweights = {user: 78.0 for user in USER_LIST}
    
    return st.session_state.bodyweights.get(user, 78.0)

def set_bodyweight(user, bodyweight):
    """Set user's bodyweight in session state"""
    if "bodyweights" not in st.session_state:
        st.session_state.bodyweights = {}
    
    st.session_state.bodyweights[user] = bodyweight

def save_bodyweight_to_sheets(worksheet, user, bodyweight):
    """Save bodyweight to Google Sheets"""
    try:
        # This is a placeholder - implement based on your sheet structure
        # You may want to create a separate sheet for user profiles
        return True
    except Exception as e:
        st.error(f"Error saving bodyweight: {e}")
        return False

def add_new_user(worksheet, username):
    """Add a new user to the system"""
    try:
        # Add user to session state
        if username not in USER_LIST:
            USER_LIST.append(username)
        
        if "bodyweights" not in st.session_state:
            st.session_state.bodyweights = {}
        
        st.session_state.bodyweights[username] = 78.0
        
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {e}"

def load_goals_from_sheets(worksheet, user):
    """Load user's goals from Google Sheets"""
    try:
        # Placeholder - implement based on your sheet structure
        # You may want to create a separate sheet for goals
        return []
    except Exception as e:
        st.error(f"Error loading goals: {e}")
        return []

def save_goals_to_sheets(worksheet, user, goals):
    """Save user's goals to Google Sheets"""
    try:
        # Placeholder - implement based on your sheet structure
        return True
    except Exception as e:
        st.error(f"Error saving goals: {e}")
        return False

def create_heatmap(df):
    """Create training consistency heatmap data"""
    try:
        if len(df) == 0:
            return None
        
        # Create 12-week heatmap data
        df_copy = df.copy()
        df_copy['Date'] = pd.to_datetime(df_copy['Date'])
        
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=12)
        
        df_filtered = df_copy[(df_copy['Date'] >= start_date) & (df_copy['Date'] <= end_date)]
        
        if len(df_filtered) == 0:
            return None
        
        # Create heatmap grid (7 days x 12 weeks)
        heatmap_data = np.zeros((7, 12))
        
        for _, row in df_filtered.iterrows():
            date = row['Date']
            week = min((end_date - date).days // 7, 11)
            day_of_week = date.weekday()
            if week < 12 and day_of_week < 7:
                heatmap_data[day_of_week, 11 - week] += 1
        
        return heatmap_data, (start_date, end_date)
    except Exception as e:
        st.error(f"Error creating heatmap: {e}")
        return None

def generate_workout_summary_image(df, user, time_period):
    """Generate social media summary image"""
    try:
        if len(df) == 0:
            return None
        
        # Filter data by time period
        df_copy = df.copy()
        df_copy['Date'] = pd.to_datetime(df_copy['Date'])
        cutoff_date = datetime.now() - timedelta(days=time_period)
        df_filtered = df_copy[df_copy['Date'] >= cutoff_date]
        
        if len(df_filtered) == 0:
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10.8, 19.2), facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        ax.axis('off')
        
        # Add title
        ax.text(0.5, 0.95, f"🏆 {user}'s Training Summary", 
                ha='center', va='top', fontsize=32, color='white', weight='bold')
        
        ax.text(0.5, 0.90, f"Last {time_period} Days", 
                ha='center', va='top', fontsize=20, color='#888')
        
        # Calculate stats
        total_sessions = len(df_filtered['Date'].unique())
        total_volume = (df_filtered['Actual_Load_kg'] * 
                       pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') * 
                       pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce')).sum()
        
        # Add stats
        y_pos = 0.75
        stats = [
            (f"💪 {total_sessions}", "Training Sessions"),
            (f"🏋️ {total_volume:.0f}kg", "Total Volume"),
        ]
        
        for value, label in stats:
            ax.text(0.5, y_pos, value, ha='center', va='center', 
                   fontsize=36, color='white', weight='bold')
            ax.text(0.5, y_pos - 0.05, label, ha='center', va='center', 
                   fontsize=18, color='#888')
            y_pos -= 0.15
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, facecolor='#1a1a2e', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None
