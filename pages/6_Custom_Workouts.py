import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import *
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Custom Workouts", page_icon="🏋️", layout="wide")

init_session_state()
inject_global_styles()

# ==================== HEADER ====================
st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    padding: 32px 24px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 15px 40px rgba(102,126,234,0.5);
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
        <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>
            🏋️ Custom Workouts
        </h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
            Create your own custom workout templates
        </p>
    </div>
""", unsafe_allow_html=True)



# User selector in sidebar
available_users = load_users_from_sheets()
user_pins = load_user_pins_from_sheets()

st.sidebar.header("👤 User")
selected_user = user_selectbox_with_pin(
    available_users,
    user_pins,
    selector_key="user_selector_custom_workouts",
    label="Select User:"
)

if selected_user == USER_PLACEHOLDER:
    st.warning("🔒 Please select a user profile to manage custom workouts.")
    st.stop()

st.session_state.current_user = selected_user

# Load existing custom workout templates from Supabase via helpers
def get_user_custom_workouts(df_templates, user):
    """Get custom workouts created by a specific user"""
    if df_templates.empty:
        return pd.DataFrame()
    return df_templates[df_templates['CreatedBy'] == user]

def get_other_users_workouts(df_templates, user):
    """Get custom workouts created by other users"""
    if df_templates.empty:
        return pd.DataFrame()
    return df_templates[df_templates['CreatedBy'] != user]

# Load templates
df_templates = load_custom_workout_templates()

# ==================== YOUR CUSTOM WORKOUTS ====================
st.markdown("## 💪 Your Custom Workouts")

user_workouts = get_user_custom_workouts(df_templates, selected_user)

if not user_workouts.empty:
    for idx, workout in user_workouts.iterrows():
        with st.expander(f"🏋️ {workout['WorkoutName']} ({workout['WorkoutType']})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Type:** {workout['WorkoutType']}")
                st.write(f"**Description:** {workout.get('Description', 'N/A')}")
                
                tracked_metrics = []
                if workout.get('TracksWeight', False): tracked_metrics.append("Weight")
                if workout.get('TracksSets', False): tracked_metrics.append("Sets")
                if workout.get('TracksReps', False): tracked_metrics.append("Reps")
                if workout.get('TracksDuration', False): tracked_metrics.append("Duration")
                if workout.get('TracksDistance', False): tracked_metrics.append("Distance")
                if workout.get('TracksRPE', False): tracked_metrics.append("RPE")
                
                st.write(f"**Tracks:** {', '.join(tracked_metrics)}")
                st.caption(f"Created: {workout.get('CreatedDate', 'Unknown')}")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{workout['WorkoutID']}"):
                    st.warning("⚠️ Delete function needs to be implemented with Supabase")
                    # TODO: Implement delete_custom_workout_template() in helpers.py
else:
    st.info("You haven't created any custom workouts yet. Create one below!")

# ==================== BROWSE OTHER USERS' WORKOUTS ====================
st.markdown("## 👥 Browse Workouts from Other Users")
st.caption("Copy a workout template created by another user to add it to your collection")

other_workouts = get_other_users_workouts(df_templates, selected_user)

if not other_workouts.empty:
    for idx, workout in other_workouts.iterrows():
        with st.expander(f"🏋️ {workout['WorkoutName']} ({workout['WorkoutType']}) - by {workout['CreatedBy']}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Type:** {workout['WorkoutType']}")
                st.write(f"**Description:** {workout.get('Description', 'N/A')}")
                
                tracked_metrics = []
                if workout.get('TracksWeight', False): tracked_metrics.append("Weight")
                if workout.get('TracksSets', False): tracked_metrics.append("Sets")
                if workout.get('TracksReps', False): tracked_metrics.append("Reps")
                if workout.get('TracksDuration', False): tracked_metrics.append("Duration")
                if workout.get('TracksDistance', False): tracked_metrics.append("Distance")
                if workout.get('TracksRPE', False): tracked_metrics.append("RPE")
                
                st.write(f"**Tracks:** {', '.join(tracked_metrics)}")
            
            with col2:
                if st.button("📋 Copy to My Workouts", key=f"copy_{workout['WorkoutID']}"):
                    st.warning("⚠️ Copy function needs to be implemented with Supabase")
                    # TODO: Implement copy_custom_workout_template() in helpers.py
else:
    st.info("No workouts created by other users yet.")

# ==================== CREATE NEW CUSTOM WORKOUT ====================
st.markdown("## ✨ Create New Custom Workout")

with st.form("create_custom_workout"):
    st.markdown("### Basic Information")
    workout_name = st.text_input("Workout Name *", placeholder="e.g., Campus Board Ladder, Running, Yoga Flow")
    workout_description = st.text_area("Description (optional)", placeholder="Brief description of the workout...")
    
    st.markdown("### Workout Type")
    workout_type = st.selectbox(
        "Select Type *",
        ["Strength", "Cardio", "Bodyweight", "Flexibility", "Other"]
    )
    
    st.markdown("### Metrics to Track")
    st.caption("Select which metrics you want to log for this workout")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        track_weight = st.checkbox("Weight (kg)", value=(workout_type == "Strength"))
        track_sets = st.checkbox("Sets", value=(workout_type in ["Strength", "Bodyweight"]))
    
    with col2:
        track_reps = st.checkbox("Reps", value=(workout_type in ["Strength", "Bodyweight"]))
        track_duration = st.checkbox("Duration (min)", value=(workout_type in ["Cardio", "Flexibility"]))
    
    with col3:
        track_distance = st.checkbox("Distance (km)", value=(workout_type == "Cardio"))
        track_rpe = st.checkbox("RPE (1-10)", value=True)
    
    submitted = st.form_submit_button("🚀 Create Workout", use_container_width=True)
    
    if submitted:
        if not workout_name:
            st.error("Please enter a workout name!")
        elif not any([track_weight, track_sets, track_reps, track_duration, track_distance, track_rpe]):
            st.error("Please select at least one metric to track!")
        else:
            success = save_custom_workout_template(
                selected_user,
                workout_name,
                workout_type,
                workout_description,
                track_weight,
                track_sets,
                track_reps,
                track_duration,
                track_distance,
                track_rpe
            )
            if success:
                st.success(f"✅ Workout '{workout_name}' created successfully!")
                st.rerun()
            else:
                st.error("Failed to create workout. Please try again.")

# ==================== SIDEBAR INFO ====================
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Quick Tips")
st.sidebar.info("""
**Creating Custom Workouts:**
- Give it a clear, descriptive name
- Select the workout type
- Choose which metrics to track
- You can see others' workouts and copy them

**Using Custom Workouts:**
- Go to Log Workout page
- Select from your custom workouts
- Enter the relevant metrics
- Track progress in Progress page
""")
