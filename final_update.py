"""
Final comprehensive update: All remaining critical database functions
"""
import re

with open('utils/helpers.py', 'r') as f:
    content = f.read()

# Update get_bodyweight_history
pattern1 = r'def get_bodyweight_history\(spreadsheet, user\):.*?return pd\.DataFrame\(\)'
replacement1 = '''def get_bodyweight_history(spreadsheet, user):
    """Get user's bodyweight history over time"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        response = supabase.table("bodyweight_history").select("date, bodyweight_kg").eq("username", user).order("date").execute()
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        if len(df) > 0:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['bodyweight_kg'] = pd.to_numeric(df['bodyweight_kg'], errors='coerce')
            df = df.rename(columns={'date': 'Date', 'bodyweight_kg': 'Bodyweight_kg'})
            return df[['Date', 'Bodyweight_kg']]
        
        return pd.DataFrame()
    except:
        return pd.DataFrame()'''
content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# Update log_activity_to_sheets
pattern2 = r'def log_activity_to_sheets\(spreadsheet, user, activity_type, duration_min=None, notes="", session_date=None\):.*?return False'
replacement2 = '''def log_activity_to_sheets(spreadsheet, user, activity_type, duration_min=None, notes="", session_date=None):
    """
    Log a simple activity (Climbing, Board, Work Pullups, or Gym) to activity_log table.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        if session_date is None:
            session_date = datetime.now().date()
        
        date_str = session_date.strftime("%Y-%m-%d")
        
        activity_data = {
            "username": user,
            "date": date_str,
            "activity_type": activity_type,
            "duration_min": duration_min,
            "notes": notes or ""
        }
        
        supabase.table("activity_log").insert(activity_data).execute()
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error logging activity: {e}")
        return False'''
content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

# Update load_activity_log
pattern3 = r'def load_activity_log\(spreadsheet, user=None\):.*?return pd\.DataFrame\(\)'
replacement3 = '''def load_activity_log(spreadsheet, user=None):
    """Load activity log from activity_log table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        query = supabase.table("activity_log").select("*")
        if user:
            query = query.eq("username", user)
        
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns={
                'username': 'User',
                'date': 'Date',
                'activity_type': 'ActivityType',
                'duration_min': 'DurationMin',
                'notes': 'Notes'
            })
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()'''
content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)

# Update get_user_setting
pattern4 = r'def get_user_setting\(spreadsheet, user, setting_key, default_value=.*?\):.*?return default_value'
replacement4 = '''def get_user_setting(spreadsheet, user, setting_key, default_value=None):
    """Get a user setting value from user_settings table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return default_value
        
        response = supabase.table("user_settings").select("setting_value").eq("username", user).eq("setting_key", setting_key).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["setting_value"]
        return default_value
    except:
        return default_value'''
content = re.sub(pattern4, replacement4, content, flags=re.DOTALL)

# Update set_user_setting
pattern5 = r'def set_user_setting\(spreadsheet, user, setting_key, setting_value\):.*?return False'
replacement5 = '''def set_user_setting(spreadsheet, user, setting_key, setting_value):
    """Set a user setting value in user_settings table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        supabase.table("user_settings").upsert({
            "username": user,
            "setting_key": setting_key,
            "setting_value": str(setting_value)
        }).execute()
        
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error setting user setting: {e}")
        return False'''
content = re.sub(pattern5, replacement5, content, flags=re.DOTALL)

with open('utils/helpers.py', 'w') as f:
    f.write(content)

print("✅ All critical functions updated!")
print("📊 Updated: bodyweight_history, activity logging, user settings")
