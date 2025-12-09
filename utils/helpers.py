import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import io

PLATE_SIZES = [20, 15, 10, 5, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.25]

QUICK_NOTES = {"💪 Strong": "Strong", "😴 Tired": "Tired", "🤕 Hand pain": "Hand pain", "😤 Hard": "Hard", "✨ Great": "Great"}
USER_LIST = ["Oscar", "Ian"]

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
@st.cache_resource(ttl=600)
def get_google_sheet():
    """Connect to Google Sheets - returns the spreadsheet object"""
    try:
        credentials_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        sheet_url = st.secrets["SHEET_URL"]
        return client.open_by_url(sheet_url)
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

@st.cache_data(ttl=120)  # Cache for 2 minutes
def _load_sheet_data(sheet_name):
    """Internal cached function to load data from a specific sheet"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return []
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()
    except:
        return []

def load_data_from_sheets(worksheet, user=None):
    """Load all data from workout log sheet (Sheet1), optionally filtered by user"""
    try:
        data = _load_sheet_data("Sheet1")
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
    """Append a new workout to the Sheet1"""
    try:
        clean_data = {}
        for key, value in row_data.items():
            if isinstance(value, (np.integer, np.int64)):
                clean_data[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                clean_data[key] = float(value)
            else:
                clean_data[key] = value
        worksheet.append_row(list(clean_data.values()))
        
        # Clear the cache after saving
        _load_sheet_data.clear()
        
        return True
    except Exception as e:
        st.error(f"Error saving workout: {e}")
        return False

def load_users_from_sheets(spreadsheet):
    """Load unique users from Users sheet"""
    try:
        data = _load_sheet_data("Users")
        if data:
            df = pd.DataFrame(data)
            if "Username" in df.columns:
                users = df["Username"].tolist()
                return users if users else USER_LIST.copy()
        return USER_LIST.copy()
    except Exception as e:
        return USER_LIST.copy()

def get_bodyweight(spreadsheet, user):
    """Get user's bodyweight from Bodyweights sheet"""
    try:
        records = _load_sheet_data("Bodyweights")
        for record in records:
            if record.get("User") == user:
                return float(record.get("Bodyweight_kg", 78.0))
        return 78.0
    except:
        return 78.0

def set_bodyweight(spreadsheet, user, bodyweight):
    """Update user's bodyweight in Bodyweights sheet"""
    try:
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        records = bw_sheet.get_all_records()
        for idx, record in enumerate(records):
            if record.get("User") == user:
                bw_sheet.update_cell(idx + 2, 2, float(bodyweight))
                _load_sheet_data.clear()
                return True
        bw_sheet.append_row([user, float(bodyweight)])
        _load_sheet_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating bodyweight: {e}")
        return False

def get_user_1rms(spreadsheet, user, exercise, arm):
    """Get user's 1RM from UserProfile sheet"""
    try:
        records = _load_sheet_data("UserProfile")
        for record in records:
            if record.get("User") == user:
                key = f"{exercise}_{arm}_1RM"
                value = record.get(key, None)
                if value and value > 0:
                    return float(value)
    except:
        pass
    return float(105 if "Edge" in exercise else 85 if "Pinch" in exercise else 75)

def get_user_1rm(spreadsheet, user, exercise, arm):
    """Get user's 1RM - first try UserProfile sheet, then fall back to workout history"""
    try:
        records = _load_sheet_data("UserProfile")
        for record in records:
            if record.get("User") == user:
                key = f"{exercise}_{arm}_1RM"
                value = record.get(key, None)
                if value and value > 0:
                    return float(value)
    except:
        pass
    
    try:
        data = _load_sheet_data("Sheet1")
        if data:
            df = pd.DataFrame(data)
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            
            if len(df) > 0:
                df_filtered = df[
                    (df['Exercise'].str.contains(exercise, na=False)) &
                    (df['Arm'] == arm)
                ]
                if len(df_filtered) > 0:
                    df_filtered['Actual_Load_kg'] = pd.to_numeric(df_filtered['Actual_Load_kg'], errors='coerce')
                    max_weight = df_filtered['Actual_Load_kg'].max()
                    if pd.notna(max_weight) and max_weight > 0:
                        return float(max_weight)
    except:
        pass
    
    return float(105 if "Edge" in exercise else 85 if "Pinch" in exercise else 75)

def update_user_1rm(spreadsheet, user, exercise, arm, new_1rm):
    """Update user's 1RM in UserProfile sheet"""
    try:
        profile_sheet = spreadsheet.worksheet("UserProfile")
        records = profile_sheet.get_all_records()
        for idx, record in enumerate(records):
            if record.get("User") == user:
                key = f"{exercise}_{arm}_1RM"
                headers = list(record.keys())
                if key in headers:
                    col_idx = headers.index(key) + 1
                    profile_sheet.update_cell(idx + 2, col_idx, float(new_1rm))
                    _load_sheet_data.clear()
                    return True
        
        headers = profile_sheet.row_values(1)
        new_row = [user, 78.0, 105, 105, 85, 85, 75, 75]
        key = f"{exercise}_{arm}_1RM"
        if key in headers:
            col_idx = headers.index(key)
            new_row[col_idx] = float(new_1rm)
        profile_sheet.append_row(new_row)
        _load_sheet_data.clear()
        return True
    except Exception as e:
        return False

def add_new_user(spreadsheet, username, bodyweight=78.0):
    """Add a new user to all necessary sheets"""
    try:
        users_sheet = spreadsheet.worksheet("Users")
        users_sheet.append_row([username])
        
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        bw_sheet.append_row([username, float(bodyweight)])
        
        profile_sheet = spreadsheet.worksheet("UserProfile")
        profile_sheet.append_row([username, float(bodyweight), 105, 105, 85, 85, 75, 75])
        
        _load_sheet_data.clear()
        
        return True, "User created successfully!"
    except Exception as e:
        return False, f"Error creating user: {e}"

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

def create_heatmap(df):
    """Create training consistency heatmap data"""
    try:
        if len(df) == 0:
            return None
        
        df_copy = df.copy()
        df_copy['Date'] = pd.to_datetime(df_copy['Date'])
        
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=12)
        df_filtered = df_copy[(df_copy['Date'] >= start_date) & (df_copy['Date'] <= end_date)]
        
        if len(df_filtered) == 0:
            return None
        
        heatmap_data = np.zeros((7, 12))
        for _, row in df_filtered.iterrows():
            date = row['Date']
            week = min((end_date - date).days // 7, 11)
            day_of_week = date.weekday()
            if week < 12 and day_of_week < 7:
                heatmap_data[day_of_week, 11 - week] += 1
        
        return heatmap_data, (start_date, end_date)
    except Exception as e:
        return None

def delete_user(spreadsheet, username):
    """Delete a user from all sheets"""
    try:
        # Delete from Users sheet
        users_sheet = spreadsheet.worksheet("Users")
        users_data = users_sheet.get_all_values()
        for idx, row in enumerate(users_data):
            if len(row) > 0 and row[0] == username:
                users_sheet.delete_rows(idx + 1)
                break
        
        # Delete from Bodyweights sheet
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        bw_data = bw_sheet.get_all_values()
        for idx, row in enumerate(bw_data):
            if len(row) > 0 and row[0] == username:
                bw_sheet.delete_rows(idx + 1)
                break
        
        # Delete from UserProfile sheet
        profile_sheet = spreadsheet.worksheet("UserProfile")
        profile_data = profile_sheet.get_all_values()
        for idx, row in enumerate(profile_data):
            if len(row) > 0 and row[0] == username:
                profile_sheet.delete_rows(idx + 1)
                break
        
        # Delete workout data from Sheet1
        workout_sheet = spreadsheet.worksheet("Sheet1")
        workout_data = workout_sheet.get_all_values()
        rows_to_delete = []
        for idx, row in enumerate(workout_data):
            if len(row) > 0 and row[0] == username:  # Assuming User is first column
                rows_to_delete.append(idx + 1)
        
        # Delete rows in reverse order to avoid index shifting
        for row_idx in sorted(rows_to_delete, reverse=True):
            workout_sheet.delete_rows(row_idx)
        
        _load_sheet_data.clear()
        
        return True, f"User '{username}' deleted successfully!"
    except Exception as e:
        return False, f"Error deleting user: {e}"

# ==================== ACTIVITY LOGGING ====================
def log_activity_to_sheets(spreadsheet, user, activity_type, duration_min=None, notes=""):
    """
    Log a simple activity (Climbing, Work Pullups, or Gym) to ActivityLog sheet.
    activity_type: "Gym", "Climbing", "Work"
    """
    try:
        # Get or create ActivityLog sheet
        all_sheets = [ws.title for ws in spreadsheet.worksheets()]
        if "ActivityLog" in all_sheets:
            activity_sheet = spreadsheet.worksheet("ActivityLog")
        else:
            activity_sheet = spreadsheet.add_worksheet(title="ActivityLog", rows=1000, cols=6)
            activity_sheet.append_row(["User", "Date", "ActivityType", "DurationMin", "Notes", "Timestamp"])
        
        # Prepare row
        row_data = [
            user,
            datetime.now().strftime("%Y-%m-%d"),
            activity_type,
            duration_min if duration_min else "",
            notes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        activity_sheet.append_row(row_data)
        _load_sheet_data.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Error logging activity: {e}")
        return False


def load_activity_log(spreadsheet, user=None):
    """Load activity log from ActivityLog sheet, optionally filtered by user."""
    try:
        data = _load_sheet_data("ActivityLog")
        if data:
            df = pd.DataFrame(data)
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            return df
        else:
            return pd.DataFrame(columns=["User", "Date", "ActivityType", "DurationMin", "Notes", "Timestamp"])
    except Exception as e:
        return pd.DataFrame(columns=["User", "Date", "ActivityType", "DurationMin", "Notes", "Timestamp"])
