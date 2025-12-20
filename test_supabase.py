"""
Quick test to verify Supabase connection and data
"""
import streamlit as st
from utils.helpers import get_supabase_client

st.set_page_config(page_title="Supabase Test", page_icon="🧪")

st.title("🧪 Supabase Connection Test")

supabase = get_supabase_client()

if supabase:
    st.success("✅ Connected to Supabase!")
    
    st.subheader("Users Table")
    try:
        users = supabase.table("users").select("*").execute()
        st.write(f"Found {len(users.data)} users")
        st.json(users.data)
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.subheader("Workouts Table")
    try:
        workouts = supabase.table("workouts").select("*").limit(5).execute()
        st.write(f"Showing 5 of your workouts:")
        st.json(workouts.data)
    except Exception as e:
        st.error(f"Error: {e}")
        
    st.subheader("Bodyweights Table")
    try:
        bodyweights = supabase.table("bodyweights").select("*").execute()
        st.write(f"Found {len(bodyweights.data)} bodyweight records")
        st.json(bodyweights.data)
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.error("❌ Could not connect to Supabase")
