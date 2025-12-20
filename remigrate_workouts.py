"""
Re-migrate workout data with proper column mapping
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from supabase import create_client
import toml

# Load secrets
secrets = toml.load('.streamlit/secrets.toml')

# Parse Google credentials from TOML
import json
google_creds = json.loads(secrets['GOOGLE_SHEETS_CREDENTIALS'])

# Connect to Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

# Extract spreadsheet ID from URL
sheet_url = secrets['SHEET_URL']
spreadsheet_id = sheet_url.split('/d/')[1].split('/')[0]
spreadsheet = client.open_by_key(spreadsheet_id)

# Connect to Supabase
supabase = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_KEY'])

def clean_value(val):
    """Clean and convert values - keep 0 as valid"""
    if val is None or val == '' or val == 'None' or val == 'nan':
        return None
    try:
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val.lower() == 'none':
                return None
        return float(val)  # Keep 0 as valid
    except:
        return None

def clean_int_value(val):
    """Clean and convert to integer - keep 0 as valid"""
    if val is None or val == '' or val == 'None' or val == 'nan':
        return None
    try:
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val.lower() == 'none':
                return None
        return int(float(val))  # Keep 0 as valid
    except:
        return None

print("🔍 Checking Google Sheets columns...")
try:
    workout_sheet = spreadsheet.worksheet("Sheet1")
    headers = workout_sheet.row_values(1)
    print(f"✓ Found columns in Sheet1: {headers}")
    
    # Get first data row to see what values look like
    first_row = workout_sheet.get_all_records()[0]
    print(f"\n📝 Sample row:")
    for key, val in first_row.items():
        print(f"  {key}: {val}")
    
    print("\n🗑️  Clearing existing workout data in Supabase...")
    # Delete all workouts
    result = supabase.table("workouts").delete().neq('id', 0).execute()
    print(f"✓ Cleared workouts table")
    
    print("\n🏋️  Re-migrating workouts...")
    workout_data = workout_sheet.get_all_records()
    print(f"Found {len(workout_data)} workout records in Google Sheets")
    
    batch_size = 100
    total_inserted = 0
    
    for i in range(0, len(workout_data), batch_size):
        batch = workout_data[i:i+batch_size]
        records_to_insert = []
        
        for record in batch:
            try:
                # Try different possible column names for each field
                username = record.get("User") or record.get("Username") or record.get("username")
                date = record.get("Date") or record.get("date")
                exercise = record.get("Exercise") or record.get("exercise")
                arm = record.get("Arm") or record.get("arm")
                
                # These are the tricky ones - use clean_int_value for integer columns
                sets_val = clean_int_value(
                    record.get("Sets_Completed") or 
                    record.get("Sets") or 
                    record.get("sets")
                )
                reps_val = clean_int_value(
                    record.get("Reps_Per_Set") or 
                    record.get("Reps") or 
                    record.get("reps")
                )
                weight_val = clean_value(
                    record.get("Actual_Load_kg") or 
                    record.get("Weight") or 
                    record.get("Weight_kg") or
                    record.get("weight")
                )
                rpe_val = clean_int_value(
                    record.get("RPE") or 
                    record.get("rpe")
                )
                
                notes = record.get("Notes") or record.get("notes") or ""
                
                if username and date and exercise and arm:
                    records_to_insert.append({
                        "username": username,
                        "date": date,
                        "exercise": exercise,
                        "arm": arm,
                        "sets": sets_val,
                        "reps": reps_val,
                        "weight": weight_val,
                        "rpe": rpe_val,
                        "notes": notes
                    })
            except Exception as e:
                print(f"  ✗ Error preparing record: {e}")
        
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
        print(f"  {w['username']}: {w['exercise']} (Arm: {w['arm']}) - sets:{w['sets']}, reps:{w['reps']}, weight:{w['weight']}kg")
    
    # Count records with data
    all_workouts = supabase.table("workouts").select("*").execute()
    with_weight = sum(1 for w in all_workouts.data if w['weight'] is not None)
    print(f"\n📈 Total: {len(all_workouts.data)} workouts, {with_weight} with weight data")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
