import streamlit as st
from supabase import create_client

# Test Supabase connection
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    print(f"URL: {url}")
    print(f"Key: {key[:20]}...")
    
    supabase = create_client(url, key)
    print("✅ Supabase client created successfully!")
    
    # Test query - get users
    users = supabase.table("users").select("*").execute()
    print(f"\n📊 Users table: {len(users.data)} records")
    print(users.data)
    
    # Test query - get workouts
    workouts = supabase.table("workouts").select("*").limit(5).execute()
    print(f"\n🏋️ Workouts table: {len(workouts.data)} recent records")
    print(workouts.data)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
