#!/usr/bin/env python3
"""
Comprehensive script to convert helpers.py from Google Sheets to Supabase
"""

# Read the backup file
with open('utils/helpers_backup_sheets.py', 'r') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    'import gspread\nfrom google.oauth2.service_account import Credentials',
    'from supabase import create_client'
)

# 2. Replace connection function
old_connection = '''@st.cache_resource(ttl=600)
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
        return None'''

new_connection = '''@st.cache_resource
def get_supabase_client():
    """Connect to Supabase - returns the client object"""
    try:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

# Legacy alias for compatibility
def get_google_sheet():
    return get_supabase_client()'''

content = content.replace(old_connection, new_connection)

# 3. Replace cache function
old_cache = '''@st.cache_data(ttl=120)  # Cache for 2 minutes
def _load_sheet_data(sheet_name):
    """Internal cached function to load data from a specific sheet"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return []
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()
    except:
        return []'''

new_cache = '''@st.cache_data(ttl=120)  # Cache for 2 minutes
def _load_table_data(table_name):
    """Internal cached function to load data from a specific table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        return []

# Alias for backwards compatibility
_load_sheet_data = _load_table_data'''

content = content.replace(old_cache, new_cache)

# 4. Update load_data_from_sheets
old_load = '''def load_data_from_sheets(worksheet, user=None):
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
        return pd.DataFrame()'''

new_load = '''def load_data_from_sheets(worksheet, user=None):
    """Load all data from workouts table, optionally filtered by user"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        query = supabase.table("workouts").select("*")
        if user:
            query = query.eq("username", user)
        
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename columns to match old format
            column_map = {
                'username': 'User',
                'date': 'Date',
                'exercise': 'Exercise',
                'arm': 'Arm',
                'weight': 'Weight',
                'sets': 'Sets',
                'reps': 'Reps',
                'notes': 'Notes'
            }
            df = df.rename(columns=column_map)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()'''

content = content.replace(old_load, new_load)

# 5. Update save_workout_to_sheets
old_save = '''def save_workout_to_sheets(worksheet, row_data):
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
        return False'''

new_save = '''def save_workout_to_sheets(worksheet, row_data):
    """Save a new workout to the workouts table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Map old column names to new schema
        workout_data = {
            "username": row_data.get("User"),
            "date": row_data.get("Date"),
            "exercise": row_data.get("Exercise"),
            "arm": row_data.get("Arm"),
            "sets": row_data.get("Sets"),
            "reps": row_data.get("Reps"),
            "weight": row_data.get("Weight"),
            "notes": row_data.get("Notes", "")
        }
        
        supabase.table("workouts").insert(workout_data).execute()
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving workout: {e}")
        return False'''

content = content.replace(old_save, new_save)

# Write the new file
with open('utils/helpers.py', 'w') as f:
    f.write(content)

print("✅ Core functions converted!")
print("📝 Created new utils/helpers.py with Supabase support")
print("⚠️  Some functions still need manual updates - running phase 2...")
