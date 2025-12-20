"""
Migration script to copy data from Google Sheets to Supabase
Run this once to migrate all your existing data
"""
from supabase import create_client
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import toml

# Load secrets from .streamlit/secrets.toml
secrets = toml.load('.streamlit/secrets.toml')
SUPABASE_URL = secrets["SUPABASE_URL"]
SUPABASE_KEY = secrets["SUPABASE_KEY"]
GOOGLE_CREDS = secrets["GOOGLE_SHEETS_CREDENTIALS"]
SHEET_URL = secrets["SHEET_URL"]

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Connect to Google Sheets
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = eval(GOOGLE_CREDS)
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_url(SHEET_URL)

print("🚀 Starting migration from Google Sheets to Supabase...")
print("=" * 60)

# Helper function to clean data
def clean_value(val):
    """Clean empty strings and convert to None"""
    if val == "" or val is None:
        return None
    return val

# 1. Migrate Users
print("\n📋 Migrating Users...")
try:
    users_sheet = spreadsheet.worksheet("Users")
    users_data = users_sheet.get_all_records()
    
    print(f"  Debug: First record keys: {users_data[0].keys() if users_data else 'No records'}")
    
    for record in users_data:
        try:
            # Handle both "User" and "Username" column names
            username = record.get("User") or record.get("Username")
            pin = str(record.get("PIN") or record.get("Pin") or "0000")
            
            if not username:
                print(f"  ⚠️  Skipping record with no username: {record}")
                continue
                
            supabase.table("users").upsert({
                "username": username,
                "pin": pin
            }).execute()
            print(f"  ✓ Migrated user: {username}")
        except Exception as e:
            print(f"  ✗ Error migrating user {record}: {e}")
    print(f"✅ Users migration complete: {len(users_data)} users")
except Exception as e:
    print(f"❌ Error with Users sheet: {e}")

# 2. Migrate Bodyweights
print("\n⚖️  Migrating Bodyweights...")
try:
    bw_sheet = spreadsheet.worksheet("Bodyweights")
    bw_data = bw_sheet.get_all_records()
    
    for record in bw_data:
        try:
            supabase.table("bodyweights").upsert({
                "username": record["User"],
                "bodyweight_kg": float(record["Bodyweight_kg"])
            }).execute()
            print(f"  ✓ Migrated bodyweight for: {record['User']}")
        except Exception as e:
            print(f"  ✗ Error migrating bodyweight for {record.get('User')}: {e}")
    print(f"✅ Bodyweights migration complete: {len(bw_data)} records")
except Exception as e:
    print(f"❌ Error with Bodyweights sheet: {e}")

# 3. Migrate Bodyweight History
print("\n📊 Migrating Bodyweight History...")
try:
    bw_history_sheet = spreadsheet.worksheet("BodyweightHistory")
    bw_history_data = bw_history_sheet.get_all_records()
    
    for record in bw_history_data:
        try:
            supabase.table("bodyweight_history").insert({
                "username": record["User"],
                "date": record["Date"],
                "bodyweight_kg": float(record["Bodyweight_kg"])
            }).execute()
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print(f"✅ Bodyweight History migration complete: {len(bw_history_data)} records")
except Exception as e:
    print(f"❌ Error with BodyweightHistory sheet: {e}")

# 4. Migrate User Profile
print("\n👤 Migrating User Profiles...")
try:
    profile_sheet = spreadsheet.worksheet("UserProfile")
    profile_data = profile_sheet.get_all_records()
    
    for record in profile_data:
        try:
            supabase.table("user_profile").upsert({
                "username": record["User"],
                "bodyweight_kg": float(record["Bodyweight_kg"]),
                "left_20mm_goal": clean_value(record.get("Left_20mm_Goal")),
                "left_20mm_current": clean_value(record.get("Left_20mm_Current")),
                "right_20mm_goal": clean_value(record.get("Right_20mm_Goal")),
                "right_20mm_current": clean_value(record.get("Right_20mm_Current")),
                "left_14mm_goal": clean_value(record.get("Left_14mm_Goal")),
                "left_14mm_current": clean_value(record.get("Left_14mm_Current")),
                "right_14mm_goal": clean_value(record.get("Right_14mm_Goal")),
                "right_14mm_current": clean_value(record.get("Right_14mm_Current"))
            }).execute()
            print(f"  ✓ Migrated profile for: {record['User']}")
        except Exception as e:
            print(f"  ✗ Error migrating profile for {record.get('User')}: {e}")
    print(f"✅ User Profiles migration complete: {len(profile_data)} records")
except Exception as e:
    print(f"❌ Error with UserProfile sheet: {e}")

# 5. Migrate Workouts (Sheet1)
print("\n🏋️  Migrating Workouts...")
try:
    workout_sheet = spreadsheet.worksheet("Sheet1")
    workout_data = workout_sheet.get_all_records()
    
    batch_size = 100
    for i in range(0, len(workout_data), batch_size):
        batch = workout_data[i:i+batch_size]
        records_to_insert = []
        
        for record in batch:
            try:
                records_to_insert.append({
                    "username": record["User"],
                    "date": record["Date"],
                    "exercise": record["Exercise"],
                    "arm": record["Arm"],
                    "sets": clean_value(record.get("Sets")),
                    "reps": clean_value(record.get("Reps")),
                    "weight": clean_value(record.get("Weight")),
                    "notes": clean_value(record.get("Notes"))
                })
            except Exception as e:
                print(f"  ✗ Error preparing workout record: {e}")
        
        if records_to_insert:
            supabase.table("workouts").insert(records_to_insert).execute()
            print(f"  ✓ Migrated batch {i//batch_size + 1}: {len(records_to_insert)} workouts")
    
    print(f"✅ Workouts migration complete: {len(workout_data)} records")
except Exception as e:
    print(f"❌ Error with Workouts sheet: {e}")

# 6. Migrate Activity Log
print("\n🧗 Migrating Activity Log...")
try:
    activity_sheet = spreadsheet.worksheet("ActivityLog")
    activity_data = activity_sheet.get_all_records()
    
    for record in activity_data:
        try:
            supabase.table("activity_log").insert({
                "username": record["User"],
                "date": record["Date"],
                "activity_type": record["ActivityType"],
                "duration_min": clean_value(record.get("DurationMin")),
                "notes": clean_value(record.get("Notes"))
            }).execute()
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print(f"✅ Activity Log migration complete: {len(activity_data)} records")
except Exception as e:
    print(f"❌ Error with ActivityLog sheet: {e}")

# 7. Migrate Custom Workout Templates
print("\n💪 Migrating Custom Workout Templates...")
try:
    template_sheet = spreadsheet.worksheet("CustomWorkoutTemplates")
    template_data = template_sheet.get_all_records()
    
    for record in template_data:
        try:
            supabase.table("custom_workout_templates").upsert({
                "username": record["User"],
                "template_name": record["TemplateName"],
                "category": record["Category"],
                "exercise_1": clean_value(record.get("Exercise1")),
                "exercise_2": clean_value(record.get("Exercise2")),
                "exercise_3": clean_value(record.get("Exercise3")),
                "exercise_4": clean_value(record.get("Exercise4")),
                "exercise_5": clean_value(record.get("Exercise5"))
            }).execute()
            print(f"  ✓ Migrated template: {record['TemplateName']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print(f"✅ Custom Workout Templates migration complete: {len(template_data)} records")
except Exception as e:
    print(f"❌ Error with CustomWorkoutTemplates sheet: {e}")

# 8. Migrate Custom Workout Logs
print("\n📝 Migrating Custom Workout Logs...")
try:
    log_sheet = spreadsheet.worksheet("CustomWorkoutLogs")
    log_data = log_sheet.get_all_records()
    
    for record in log_data:
        try:
            supabase.table("custom_workout_logs").insert({
                "username": record["User"],
                "date": record["Date"],
                "template_name": record["TemplateName"],
                "category": record["Category"],
                "exercise_1": clean_value(record.get("Exercise1")),
                "exercise_2": clean_value(record.get("Exercise2")),
                "exercise_3": clean_value(record.get("Exercise3")),
                "exercise_4": clean_value(record.get("Exercise4")),
                "exercise_5": clean_value(record.get("Exercise5")),
                "notes": clean_value(record.get("Notes"))
            }).execute()
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print(f"✅ Custom Workout Logs migration complete: {len(log_data)} records")
except Exception as e:
    print(f"❌ Error with CustomWorkoutLogs sheet: {e}")

# 9. Migrate User Settings
print("\n⚙️  Migrating User Settings...")
try:
    settings_sheet = spreadsheet.worksheet("UserSettings")
    settings_data = settings_sheet.get_all_records()
    
    for record in settings_data:
        try:
            supabase.table("user_settings").upsert({
                "username": record["User"],
                "setting_key": record["SettingKey"],
                "setting_value": str(record["SettingValue"])
            }).execute()
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print(f"✅ User Settings migration complete: {len(settings_data)} records")
except Exception as e:
    print(f"❌ Error with UserSettings sheet: {e}")

# 10. Migrate Goals
print("\n🎯 Migrating Goals...")
try:
    goals_sheet = spreadsheet.worksheet("Goals")
    goals_data = goals_sheet.get_all_records()
    
    for record in goals_data:
        try:
            supabase.table("goals").insert({
                "username": record["User"],
                "exercise": record["Exercise"],
                "arm": record["Arm"],
                "target_weight": float(record["Target_Weight"]),
                "completed": bool(record.get("Completed", False)),
                "date_set": record["Date_Set"],
                "date_completed": clean_value(record.get("Date_Completed"))
            }).execute()
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print(f"✅ Goals migration complete: {len(goals_data)} records")
except Exception as e:
    print(f"❌ Error with Goals sheet: {e}")

print("\n" + "=" * 60)
print("🎉 Migration complete!")
print("=" * 60)
print("\n✨ Next steps:")
print("1. Verify your data in Supabase dashboard (Table Editor)")
print("2. The app will now use Supabase instead of Google Sheets")
print("3. Your Google Sheets data is still safe as a backup\n")
