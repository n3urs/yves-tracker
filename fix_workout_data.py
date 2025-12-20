"""
Fix workout data migration - properly map Google Sheets columns
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from supabase import create_client
import toml

# Load secrets
secrets = toml.load('.streamlit/secrets.toml')

# Connect to Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('.streamlit/service_account.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(secrets['SPREADSHEET_ID'])

# Connect to Supabase
supabase = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_KEY'])

def clean_value(val):
    """Clean and convert values"""
    if val is None or val == '' or val == 'None':
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val) if val != 0 else None
        return None
    except:
        return None

print("🔍 Checking Google Sheets columns...")
workout_sheet = spreadsheet.worksheet("Sheet1")
headers = workout_sheet.row_values(1)
print(f"Columns in Sheet1: {headers}")

print("\n🗑️  Clearing existing workout data...")
try:
    # Delete all workouts
    supabase.table("workouts").delete().neq('id', 0).execute()
    print("✓ Cleared workouts table")
except Exception as e:
    print(f"✗ Error clearing: {e}")

print("\n🏋️  Re-migrating workouts with correct column mapping...")
workout_data = workout_sheet.get_all_records()
print(f"Found {len(workout_data)} workout records")

# Show first record to understand structure
if workout_data:
    print(f"\nFirst record keys: {list(workout_data[0].keys())}")
    print(f"First record: {workout_data[0]}")

batch_size = 100
total_inserted = 0

for i in range(0, len(workout_data), batch_size):
    batch = workout_data[i:i+batch_size]
    records_to_insert = []
    
    for record in batch:
        try:
            # Try different possible column names
            sets_val = clean_value(record.get("Sets_Completed") or record.get("Sets"))
            reps_val = clean_value(record.get("Reps_Per_Set") or record.get("Reps"))
            weight_val = clean_value(record.get("Actual_Load_kg") or record.get("Weight") or record.get("Weight_kg"))
            
            records_to_insert.append({
                "username": record["User"],
                "date": record["Date"],
                "exercise": record["Exercise"],
                "arm": record["Arm"],
                "sets": sets_val,
                "reps": reps_val,
                "weight": weight_val,
                "notes": record.get("Notes", "")
            })
        except Exception as e:
            print(f"  ✗ Error preparing record: {e}")
            print(f"    Record: {record}")
    
    if records_to_insert:
        try:
            supabase.table("workouts").insert(records_to_insert).execute()
            total_inserted += len(records_to_insert)
            print(f"  ✓ Batch {i//batch_size + 1}: {len(records_to_insert)} workouts")
        except Exception as e:
            print(f"  ✗ Error inserting batch: {e}")

print(f"\n✅ Re-migration complete: {total_inserted} workout records")

# Show sample of migrated data
print("\n📊 Sample migrated data:")
response = supabase.table("workouts").select("*").limit(5).execute()
for w in response.data:
    print(f"  {w['username']}: {w['exercise']} - sets:{w['sets']}, reps:{w['reps']}, weight:{w['weight']}")
