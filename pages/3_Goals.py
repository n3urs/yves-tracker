import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Goals & Sharing", page_icon="🎯", layout="wide")

init_session_state()

st.title("🎯 Goals & Sharing")

# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    USER_LIST,
    index=USER_LIST.index(st.session_state.current_user),
    key="user_selector_goals"
)

selected_user = st.session_state.current_user

# Connect to sheet
worksheet = get_google_sheet()

# Load goals from Google Sheets when page loads
if worksheet and selected_user not in st.session_state.goals:
    st.session_state.goals[selected_user] = load_goals_from_sheets(worksheet, selected_user)

# ==================== GOAL TRACKER ====================
st.subheader("🎯 Goal Tracker")

base_exercises = ["20mm Edge", "Pinch", "Wrist Roller"]

# Add new goal form
with st.expander("➕ Add New Goal"):
    goal_exercise = st.selectbox("Exercise", base_exercises, key="goal_exercise")
    goal_arm = st.selectbox("Arm", ["Left", "Right", "Both"], key="goal_arm")
    goal_weight = st.number_input("Target Weight (kg)", min_value=20, max_value=200, value=60, step=5, key="goal_weight")
    goal_date = st.date_input("Target Date", value=datetime.now() + timedelta(weeks=8), key="goal_date")
    
    if st.button("Add Goal", key="add_goal_btn"):
        new_goal = {
            "exercise": goal_exercise,
            "arm": goal_arm,
            "target_weight": goal_weight,
            "target_date": goal_date.strftime("%Y-%m-%d"),
            "created_date": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state.goals[selected_user].append(new_goal)
        
        # Save to Google Sheets
        if worksheet:
            save_goals_to_sheets(worksheet, selected_user, st.session_state.goals[selected_user])
        
        st.success("🎉 Goal added and saved!")
        st.rerun()

# Display active goals
if len(st.session_state.goals[selected_user]) > 0:
    st.subheader("Active Goals:")
    
    for idx, goal in enumerate(st.session_state.goals[selected_user]):
        with st.container():
            col_info, col_delete = st.columns([5, 1])
            
            with col_info:
                st.write(f"**{goal['exercise']} ({goal['arm']})**")
                st.write(f"🎯 Target: {goal['target_weight']}kg by {goal['target_date']}")
                
                # Calculate progress
                if worksheet:
                    df_user = load_data_from_sheets(worksheet, user=selected_user)
                    if len(df_user) > 0:
                        df_user["Date"] = pd.to_datetime(df_user["Date"])
                        df_user["Actual_Load_kg"] = pd.to_numeric(df_user["Actual_Load_kg"], errors='coerce')
                        
                        df_exercise = df_user[df_user["Exercise"] == goal['exercise']]
                        if len(df_exercise) > 0:
                            if goal['arm'] == "Both":
                                current_max = df_exercise['Actual_Load_kg'].max()
                            else:
                                arm_letter = "L" if goal['arm'] == "Left" else "R"
                                df_arm = df_exercise[df_exercise["Arm"] == arm_letter]
                                current_max = df_arm['Actual_Load_kg'].max() if len(df_arm) > 0 else 0
                            
                            progress = (current_max / goal['target_weight']) * 100
                            progress = min(progress, 100)
                            st.progress(progress / 100, text=f"{progress:.0f}% complete ({current_max:.1f}kg / {goal['target_weight']}kg)")
                            
                            days_left = (datetime.strptime(goal['target_date'], "%Y-%m-%d") - datetime.now()).days
                            if days_left > 0:
                                st.caption(f"⏰ {days_left} days remaining")
                            else:
                                st.caption("🏁 Goal date passed")
            
            with col_delete:
                if st.button(f"🗑️", key=f"delete_goal_{idx}"):
                    st.session_state.goals[selected_user].pop(idx)
                    
                    # Save to Google Sheets
                    if worksheet:
                        save_goals_to_sheets(worksheet, selected_user, st.session_state.goals[selected_user])
                    
                    st.rerun()
        
        st.markdown("---")
else:
    st.info("No goals set yet. Add one above!")

# ==================== WORKOUT SUMMARY EXPORT ====================
st.markdown("---")
st.subheader("📤 Share Your Progress")

if worksheet:
    df_fresh = load_data_from_sheets(worksheet, user=selected_user)
    
    if len(df_fresh) > 0:
        col_share1, col_share2 = st.columns([1, 2])
        
        with col_share1:
            time_period = st.selectbox(
                "Time Period:",
                options=[7, 14, 30, 60, 90],
                format_func=lambda x: f"Last {x} Days" if x < 30 else f"Last {x//30} Month{'s' if x >= 60 else ''}",
                key="share_period"
            )
        
        with col_share2:
            if st.button("🎨 Generate Social Media Summary", key="generate_summary_btn", use_container_width=True):
                with st.spinner("Creating your awesome summary..."):
                    summary_img = generate_workout_summary_image(df_fresh, selected_user, time_period)
                    
                    if summary_img:
                        st.success("✅ Summary generated!")
                        st.image(summary_img, use_container_width=True)
                        
                        st.download_button(
                            label="💾 Download Image",
                            data=summary_img,
                            file_name=f"{selected_user}_training_summary_{time_period}days.png",
                            mime="image/png",
                            use_container_width=True
                        )
                        st.info("📱 Tip: Perfect for Instagram Stories (1080x1920), WhatsApp, or Discord!")
                    else:
                        st.warning("Not enough data for the selected time period.")
        
        # CSV Export
        st.markdown("---")
        st.subheader("💾 Export All Data")
        csv_data = df_fresh.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV Backup",
            data=csv_data,
            file_name=f"{selected_user}_workout_data_backup.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No data yet to share. Log some workouts first!")
        st.page_link("pages/1_Log_Workout.py", label="📝 Log Your First Workout →", use_container_width=True)

# ==================== TRAINING CONSISTENCY HEATMAP ====================
if worksheet:
    df_fresh = load_data_from_sheets(worksheet, user=selected_user)
    
    if len(df_fresh) > 0:
        st.markdown("---")
        st.subheader("📅 Training Consistency (Last 12 Weeks)")
        
        heatmap_result = create_heatmap(df_fresh)
        if heatmap_result:
            heatmap_data, date_range = heatmap_result
            
            fig3, ax3 = plt.subplots(figsize=(14, 3))
            im = ax3.imshow(heatmap_data, cmap='Greens', aspect='auto', vmin=0, vmax=3)
            
            ax3.set_yticks(np.arange(7))
            ax3.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
            ax3.set_xticks(np.arange(12))
            ax3.set_xticklabels([f'W{i+1}' for i in range(12)])
            
            cbar = plt.colorbar(im, ax=ax3, orientation='horizontal', pad=0.1)
            cbar.set_label('Sessions per day', rotation=0)
            ax3.set_title("Training Frequency Heatmap (Green = More Sessions)")
            
            plt.tight_layout()
            st.pyplot(fig3)
        
        # Training streak
        df_fresh_sorted = df_fresh.sort_values("Date")
        df_fresh_sorted["Date"] = pd.to_datetime(df_fresh_sorted["Date"])
        unique_dates = df_fresh_sorted["Date"].dt.date.unique()
        
        current_streak = 0
        today = datetime.now().date()
        
        if len(unique_dates) > 0 and unique_dates[-1] == today:
            current_streak = 1
            for i in range(len(unique_dates) - 2, -1, -1):
                if (unique_dates[i+1] - unique_dates[i]).days == 1:
                    current_streak += 1
                else:
                    break
        
        if current_streak > 0:
            st.success(f"🔥 **Current Streak: {current_streak} days!** Keep it up!")
        else:
            st.info("💪 Start a new training streak today!")
    else:
        st.info("Not enough data yet for heatmap. Keep logging workouts!")
