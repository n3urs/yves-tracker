import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os

# ==================== USER LIST ====================
USER_LIST = ["Oscar", "Ian", "Ali"]

# ==================== LOAD USERS FROM SHEETS ====================
# NO DECORATOR - this is the fix!
def load_users_from_sheets(spreadsheet):
    """Load users from both Bodyweights and Users sheets and merge them."""
    users = []
    
    # Try to load from Bodyweights sheet first (primary source)
    try:
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        bw_data = bw_sheet.get_all_records()
        if bw_data:
            users.extend([row["User"] for row in bw_data if row.get("User")])
    except:
        pass
    
    # Also check Users sheet for any users not in Bodyweights
    try:
        users_sheet = spreadsheet.worksheet("Users")
        users_data = users_sheet.get_all_records()
        if users_data:
            for row in users_data:
                user = row.get("User") or row.get("Username")
                if user and user not in users:
                    users.append(user)
    except:
        pass
    
    # Remove duplicates and empty entries, return sorted list
    users = sorted(list(set([u for u in users if u and u.strip() != ""])))
    
    # Fallback to default list if no users found
    return users if users else USER_LIST.copy()


# ==================== GOOGLE SHEETS CONNECTION ====================
@st.cache_resource
def get_google_sheet():
    """Connect to Google Sheets using service account credentials."""
    try:
        # Define scope
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Load credentials from Streamlit secrets
        creds_dict = dict(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        
        # Authorize and open spreadsheet
        client = gspread.authorize(creds)
        spreadsheet = client.open("Yves Climbing Tracker")
        
        return spreadsheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None


# ==================== SESSION STATE ====================
def init_session_state():
    """Initialize session state variables."""
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "Oscar"


# ==================== LOAD DATA FROM SHEETS ====================
def load_data_from_sheets(worksheet, user=None):
    """Load workout data from Google Sheets."""
    try:
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if user:
            df = df[df['User'] == user]
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


# ==================== BODYWEIGHT FUNCTIONS ====================
def get_bodyweight(spreadsheet, user):
    """Get bodyweight for a specific user."""
    try:
        # Try Bodyweights sheet first
        try:
            bw_sheet = spreadsheet.worksheet("Bodyweights")
            bw_data = bw_sheet.get_all_records()
            for row in bw_data:
                if row.get("User") == user:
                    return float(row.get("Bodyweight_kg", 78.0))
        except:
            pass
        
        # Fallback to Users sheet
        try:
            users_sheet = spreadsheet.worksheet("Users")
            users_data = users_sheet.get_all_records()
            for row in users_data:
                if row.get("User") == user:
                    return float(row.get("Bodyweight_kg", 78.0))
        except:
            pass
        
        return 78.0  # Default
    except:
        return 78.0


def set_bodyweight(spreadsheet, user, bodyweight):
    """Set bodyweight for a specific user."""
    try:
        # Update in Bodyweights sheet
        try:
            bw_sheet = spreadsheet.worksheet("Bodyweights")
            bw_data = bw_sheet.get_all_records()
            
            for idx, row in enumerate(bw_data):
                if row.get("User") == user:
                    bw_sheet.update_cell(idx + 2, 2, bodyweight)  # +2 for header and 0-indexing
                    break
        except:
            pass
        
        # Also update in Users sheet if it exists
        try:
            users_sheet = spreadsheet.worksheet("Users")
            users_data = users_sheet.get_all_records()
            
            for idx, row in enumerate(users_data):
                if row.get("User") == user:
                    users_sheet.update_cell(idx + 2, 2, bodyweight)
                    break
        except:
            pass
            
    except Exception as e:
        st.error(f"Error updating bodyweight: {e}")


# ==================== 1RM FUNCTIONS ====================
def get_user_1rm(spreadsheet, user, exercise, arm):
    """Get 1RM for a specific user, exercise, and arm."""
    try:
        users_sheet = spreadsheet.worksheet("Users")
        users_data = users_sheet.get_all_records()
        
        # Column mapping
        col_map = {
            "20mm Edge_L": "20mm_Edge_L",
            "20mm Edge_R": "20mm_Edge_R",
            "Pinch_L": "Pinch_L",
            "Pinch_R": "Pinch_R",
            "Wrist Roller_L": "Wrist_Roller_L",
            "Wrist Roller_R": "Wrist_Roller_R"
        }
        
        col_key = f"{exercise}_{arm}"
        col_name = col_map.get(col_key, col_key)
        
        for row in users_data:
            if row.get("User") == user:
                return float(row.get(col_name, 0))
        
        return 0.0
    except:
        return 0.0


def update_user_1rm(spreadsheet, user, exercise, arm, value):
    """Update 1RM for a specific user."""
    try:
        users_sheet = spreadsheet.worksheet("Users")
        users_data = users_sheet.get_all_records()
        
        # Column mapping
        col_map = {
            "20mm Edge": {"L": 3, "R": 4},
            "Pinch": {"L": 5, "R": 6},
            "Wrist Roller": {"L": 7, "R": 8}
        }
        
        col_num = col_map.get(exercise, {}).get(arm)
        
        if col_num:
            for idx, row in enumerate(users_data):
                if row.get("User") == user:
                    users_sheet.update_cell(idx + 2, col_num, value)
                    break
    except Exception as e:
        st.error(f"Error updating 1RM: {e}")


# ==================== WORKOUT LOGGING ====================
def log_workout_to_sheets(worksheet, workout_data):
    """Log a workout to Google Sheets."""
    try:
        worksheet.append_row(workout_data)
        return True
    except Exception as e:
        st.error(f"Error logging workout: {e}")
        return False


# ==================== CALCULATE 1RM ====================
def calculate_1rm(weight, reps):
    """Calculate 1RM using Brzycki formula."""
    if reps == 1:
        return weight
    return weight * (36 / (37 - reps))


# ==================== DATA PROCESSING ====================
def process_workout_data(df):
    """Process and clean workout data."""
    if len(df) == 0:
        return df
    
    # Convert date column
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Convert numeric columns
    numeric_cols = ['Actual_Load_kg', 'Reps_Per_Set', 'Sets_Completed']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


# ==================== STATISTICS ====================
def get_user_stats(df, user):
    """Calculate statistics for a user."""
    user_df = df[df['User'] == user] if 'User' in df.columns else df
    
    if len(user_df) == 0:
        return {
            'total_sessions': 0,
            'total_volume': 0,
            'avg_weight': 0,
            'max_weight': 0
        }
    
    stats = {
        'total_sessions': len(user_df['Date'].dt.date.unique()) if 'Date' in user_df.columns else 0,
        'total_volume': (user_df['Actual_Load_kg'] * user_df['Reps_Per_Set'] * user_df['Sets_Completed']).sum() if all(col in user_df.columns for col in ['Actual_Load_kg', 'Reps_Per_Set', 'Sets_Completed']) else 0,
        'avg_weight': user_df['Actual_Load_kg'].mean() if 'Actual_Load_kg' in user_df.columns else 0,
        'max_weight': user_df['Actual_Load_kg'].max() if 'Actual_Load_kg' in user_df.columns else 0
    }
    
    return stats
