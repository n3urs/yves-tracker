"""
Script to check the actual columns in the user_profile table
"""
import streamlit as st
from supabase import create_client

def check_user_profile_schema():
    """Check what columns exist in user_profile table"""
    
    # Get Supabase credentials from streamlit secrets
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
    except:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in Streamlit secrets")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Try to fetch user_profile table to see what columns exist
    try:
        response = supabase.table("user_profile").select("*").limit(1).execute()
        if response.data:
            existing_columns = list(response.data[0].keys())
            print(f"✅ Existing columns in user_profile table:")
            for col in sorted(existing_columns):
                print(f"   - {col}")
            print(f"\nTotal: {len(existing_columns)} columns")
        else:
            print("⚠️  No data in user_profile table. Trying to get schema another way...")
            # Try to insert an empty record to see error
            try:
                response = supabase.table("user_profile").select("*").execute()
                print(f"Table exists but is empty. Columns: {response.data}")
            except Exception as e:
                print(f"Error: {e}")
    except Exception as e:
        print(f"❌ Error checking table: {e}")

if __name__ == "__main__":
    check_user_profile_schema()
