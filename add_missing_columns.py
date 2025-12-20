"""
Script to add missing columns to user_profile table for Pinch and Wrist Roller exercises
"""
import streamlit as st
from supabase import create_client

def add_missing_columns():
    """Add l_pinch_current, r_pinch_current, l_wrist_roller_current, r_wrist_roller_current if they don't exist"""
    
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
            print(f"✅ Existing columns in user_profile: {existing_columns}")
            
            required_columns = [
                'l_pinch_current', 'r_pinch_current',
                'l_wrist_roller_current', 'r_wrist_roller_current'
            ]
            
            missing = [col for col in required_columns if col not in existing_columns]
            
            if missing:
                print(f"\n⚠️  Missing columns: {missing}")
                print("\nYou need to add these columns to your Supabase user_profile table.")
                print("Run this SQL in your Supabase SQL editor:\n")
                print("ALTER TABLE user_profile")
                for i, col in enumerate(missing):
                    comma = "," if i < len(missing) - 1 else ";"
                    print(f"  ADD COLUMN IF NOT EXISTS {col} NUMERIC DEFAULT 0{comma}")
            else:
                print("\n✅ All required columns exist!")
        else:
            print("⚠️  No data in user_profile table to check columns")
    except Exception as e:
        print(f"❌ Error checking table: {e}")

if __name__ == "__main__":
    add_missing_columns()
