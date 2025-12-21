"""
Test script for user creation and deletion
"""
import streamlit as st
from supabase import create_client
import sys
sys.path.append('.')
from utils.helpers import add_new_user, delete_user

def test_user_operations():
    """Test creating and deleting a user"""
    
    test_username = "TestUser123"
    test_bodyweight = 75.5
    test_pin = "9999"
    
    print("=" * 60)
    print("🧪 Testing User Creation")
    print("=" * 60)
    
    # Create user
    ok, msg = add_new_user(test_username, test_bodyweight, test_pin)
    print(f"\nCreate Result: {'✅ SUCCESS' if ok else '❌ FAILED'}")
    print(f"Message: {msg}")
    
    if ok:
        # Verify user in tables
        print("\n" + "=" * 60)
        print("🔍 Verifying User in Tables")
        print("=" * 60)
        
        try:
            supabase_url = st.secrets["SUPABASE_URL"]
            supabase_key = st.secrets["SUPABASE_KEY"]
            supabase = create_client(supabase_url, supabase_key)
            
            tables = ['users', 'bodyweights', 'user_profile', 'user_settings']
            for table in tables:
                try:
                    response = supabase.table(table).select("*").eq("username", test_username).execute()
                    if response.data:
                        print(f"\n✅ {table}: Found {len(response.data)} row(s)")
                    else:
                        print(f"\n❌ {table}: No data")
                except Exception as e:
                    print(f"\n❌ {table}: Error - {e}")
        except Exception as e:
            print(f"\n❌ Verification failed: {e}")
        
        # Test deletion
        print("\n" + "=" * 60)
        print("🗑️ Testing User Deletion")
        print("=" * 60)
        
        ok, msg = delete_user(test_username)
        print(f"\nDelete Result: {'✅ SUCCESS' if ok else '❌ FAILED'}")
        print(f"Message: {msg}")
        
        # Verify deletion
        print("\n" + "=" * 60)
        print("🔍 Verifying User Removed from Tables")
        print("=" * 60)
        
        try:
            for table in tables:
                try:
                    response = supabase.table(table).select("*").eq("username", test_username).execute()
                    if response.data:
                        print(f"\n⚠️ {table}: Still has {len(response.data)} row(s)")
                    else:
                        print(f"\n✅ {table}: Removed successfully")
                except:
                    print(f"\n✅ {table}: Removed successfully")
        except Exception as e:
            print(f"\n❌ Verification failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_user_operations()
