"""
Script to verify user creation in all Supabase tables
"""
import streamlit as st
from supabase import create_client

def verify_user_in_tables(username):
    """Check if user exists in all relevant tables"""
    
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
    except:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in Streamlit secrets")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    tables = ['users', 'bodyweights', 'user_profile', 'user_settings']
    
    print(f"\n🔍 Checking for user: '{username}'")
    print("=" * 50)
    
    for table in tables:
        try:
            response = supabase.table(table).select("*").eq("username", username).execute()
            if response.data:
                print(f"\n✅ {table}:")
                for row in response.data:
                    print(f"   {row}")
            else:
                print(f"\n❌ {table}: No data found")
        except Exception as e:
            print(f"\n❌ {table}: Error - {e}")

if __name__ == "__main__":
    # Check for the most recently created user
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "test2"  # Default to test2
    
    verify_user_in_tables(username)
