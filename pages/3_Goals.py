import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import *
from utils.helpers import USER_PLACEHOLDER, _load_sheet_data
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Goals", page_icon="🎯", layout="wide")

init_session_state()
inject_global_styles()

# ==================== SETTINGS MODAL ====================
@st.dialog("⚙️ Weekly Goals Settings", width="large")
def goals_settings_modal(selected_user):
    """Modal for customizing weekly training goals"""
    st.markdown("Customize your weekly training targets")
    
    # Activity types available
    activity_types = {
        "Gym": {"emoji": "🏋️", "name": "Finger Training", "type": "gym"},
        "Board": {"emoji": "🎯", "name": "Board Session", "type": "Board"},
        "Climbing": {"emoji": "🧗", "name": "Climbing", "type": "Climbing"},
        "Custom": {"emoji": "💪", "name": "Custom Workout", "type": "custom"},
        "Work": {"emoji": "🏃", "name": "Work Pullups", "type": "Work"}
    }
    
    # Load current settings
    goal1_type = get_user_setting(selected_user, "weekly_goal_1_type", "Gym")
    goal1_target = get_user_setting(selected_user, "weekly_goal_1_target", 3)
    
    goal2_type = get_user_setting(selected_user, "weekly_goal_2_type", "Board")
    goal2_target = get_user_setting(selected_user, "weekly_goal_2_target", 1)
    
    goal3_type = get_user_setting(selected_user, "weekly_goal_3_type", "Climbing")
    goal3_target = get_user_setting(selected_user, "weekly_goal_3_target", 3)
    
    st.markdown("#### Goal 1")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_goal1_type = st.selectbox(
            "Activity Type",
            list(activity_types.keys()),
            index=list(activity_types.keys()).index(goal1_type) if goal1_type in activity_types else 0,
            key="goal1_type"
        )
    with col2:
        new_goal1_target = st.number_input("Target", min_value=0, max_value=10, value=int(goal1_target), key="goal1_target")
    
    st.markdown("#### Goal 2")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_goal2_type = st.selectbox(
            "Activity Type",
            list(activity_types.keys()),
            index=list(activity_types.keys()).index(goal2_type) if goal2_type in activity_types else 1,
            key="goal2_type"
        )
    with col2:
        new_goal2_target = st.number_input("Target", min_value=0, max_value=10, value=int(goal2_target), key="goal2_target")
    
    st.markdown("#### Goal 3")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_goal3_type = st.selectbox(
            "Activity Type",
            list(activity_types.keys()),
            index=list(activity_types.keys()).index(goal3_type) if goal3_type in activity_types else 2,
            key="goal3_type"
        )
    with col2:
        new_goal3_target = st.number_input("Target", min_value=0, max_value=10, value=int(goal3_target), key="goal3_target")
    
    if st.button("💾 Save Settings", use_container_width=True, type="primary"):
        with st.spinner("Saving settings..."):
            set_user_setting(selected_user, "weekly_goal_1_type", new_goal1_type)
            set_user_setting(selected_user, "weekly_goal_1_target", new_goal1_target)
            set_user_setting(selected_user, "weekly_goal_2_type", new_goal2_type)
            set_user_setting(selected_user, "weekly_goal_2_target", new_goal2_target)
            set_user_setting(selected_user, "weekly_goal_3_type", new_goal3_type)
            set_user_setting(selected_user, "weekly_goal_3_target", new_goal3_target)
            st.success("✅ Settings saved!")
            st.rerun()

# ==================== HEADER ====================
st.markdown("""
    <div class='page-header' style='text-align: center; background: linear-gradient(135deg, #e1306c 0%, #f77737 100%); 
    padding: 32px 24px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 15px 40px rgba(250,112,154,0.5);
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
        <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>🎯 Goals & Training Plan</h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
            Set ambitious targets and crush them one rep at a time
        </p>
    </div>
""", unsafe_allow_html=True)



# Load users
available_users = load_users_from_sheets()
user_pins = load_user_pins_from_sheets()

# User selector in sidebar
st.sidebar.header("👤 User")
selected_user = user_selectbox_with_pin(
    available_users,
    user_pins,
    selector_key="user_selector_goals",
    label="Select User:"
)
st.session_state.current_user = selected_user

if selected_user == USER_PLACEHOLDER:
    st.info("🔒 Select a profile from the sidebar to view training goals.")
    st.stop()

# Settings button in the top right (after user is selected)
col_left, col_right = st.columns([6, 1])
with col_right:
    if st.button("⚙️", key="goals_settings_btn", help="Weekly Goals Settings"):
        goals_settings_modal(selected_user)

# All data comes from Supabase now
if True:
    # Load data
    df = load_data_from_sheets(None, user=selected_user)
    activity_df = load_activity_log(user=selected_user)
    
    # ==================== WEEKLY GOALS - MAIN SECTION ====================
    st.markdown("""
        <div class='section-heading'>
            <div class='section-dot'></div>
            <div>
                <h3>🎯 Weekly Training Goals</h3>
                <p>Consistency is key to getting stronger!</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Load user's goal settings
    goal1_type = get_user_setting(selected_user, "weekly_goal_1_type", "Gym")
    goal1_target = int(get_user_setting(selected_user, "weekly_goal_1_target", 3))
    
    goal2_type = get_user_setting(selected_user, "weekly_goal_2_type", "Board")
    goal2_target = int(get_user_setting(selected_user, "weekly_goal_2_target", 1))
    
    goal3_type = get_user_setting(selected_user, "weekly_goal_3_type", "Climbing")
    goal3_target = int(get_user_setting(selected_user, "weekly_goal_3_target", 3))
    
    # Activity type metadata
    activity_types = {
        "Gym": {"emoji": "🏋️", "name": "Finger Training", "color": "#667eea"},
        "Board": {"emoji": "🎯", "name": "Board Session", "color": "#a855f7"},
        "Climbing": {"emoji": "🧗", "name": "Climbing", "color": "#4ade80"},
        "Custom": {"emoji": "💪", "name": "Custom Workout", "color": "#14b8a6"},
        "Work": {"emoji": "🏃", "name": "Work Pullups", "color": "#fb923c"}
    }
    
    st.info(f"💪 **Your weekly targets:** {goal1_target} {activity_types[goal1_type]['name']} • {goal2_target} {activity_types[goal2_type]['name']} • {goal3_target} {activity_types[goal3_type]['name']}")
    
    # Calculate this week's progress
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    
    # Count sessions for each goal type
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df_week = df[(df["Date"] >= week_start) & (df["Date"] <= today)]
    
    custom_workout_df = load_custom_workout_logs(selected_user)
    
    def count_sessions(goal_type):
        """Count sessions for a specific goal type this week"""
        if goal_type == "Gym":
            return len(df_week["Date"].unique()) if len(df_week) > 0 else 0
        elif goal_type == "Custom":
            if len(custom_workout_df) > 0:
                custom_workout_df["Date"] = pd.to_datetime(custom_workout_df["Date"], errors="coerce").dt.date
                custom_week = custom_workout_df[(custom_workout_df["Date"] >= week_start) & (custom_workout_df["Date"] <= today)]
                return len(custom_week["Date"].unique()) if len(custom_week) > 0 else 0
            return 0
        else:  # Board, Climbing, Work
            if len(activity_df) > 0:
                activity_df["Date"] = pd.to_datetime(activity_df["Date"], errors="coerce").dt.date
                activity_week = activity_df[(activity_df["Date"] >= week_start) & (activity_df["Date"] <= today)]
                return len(activity_week[activity_week["ActivityType"] == goal_type])
            return 0
    
    goal1_sessions = count_sessions(goal1_type)
    goal2_sessions = count_sessions(goal2_type)
    goal3_sessions = count_sessions(goal3_type)
    
    # Create goal cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        goal1_meta = activity_types[goal1_type]
        goal1_status = "✅" if goal1_sessions >= goal1_target else "⏳"
        goal1_color = "#4ade80" if goal1_sessions >= goal1_target else goal1_meta["color"]
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, {goal1_color}20, {goal1_color}10); 
            padding: 24px; border-radius: 16px; border: 2px solid {goal1_color}40; text-align: center;
            transition: all 0.3s ease;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>{goal1_meta['emoji']}</div>
                <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>{goal1_meta['name']}</div>
                <div style='font-size: 42px; font-weight: 800; color: {goal1_color};'>{goal1_sessions}/{goal1_target}</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px;'>Target: {goal1_target} session{"s" if goal1_target != 1 else ""}</div>
                <div style='font-size: 24px; margin-top: 10px;'>{goal1_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        goal2_meta = activity_types[goal2_type]
        goal2_status = "✅" if goal2_sessions >= goal2_target else "⏳"
        goal2_color = "#4ade80" if goal2_sessions >= goal2_target else goal2_meta["color"]
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, {goal2_color}20, {goal2_color}10); 
            padding: 24px; border-radius: 16px; border: 2px solid {goal2_color}40; text-align: center;
            transition: all 0.3s ease;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>{goal2_meta['emoji']}</div>
                <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>{goal2_meta['name']}</div>
                <div style='font-size: 42px; font-weight: 800; color: {goal2_color};'>{goal2_sessions}/{goal2_target}</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px;'>Target: {goal2_target} session{"s" if goal2_target != 1 else ""}</div>
                <div style='font-size: 24px; margin-top: 10px;'>{goal2_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        goal3_meta = activity_types[goal3_type]
        goal3_status = "✅" if goal3_sessions >= goal3_target else "⏳"
        goal3_color = "#4ade80" if goal3_sessions >= goal3_target else goal3_meta["color"]
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, {goal3_color}20, {goal3_color}10); 
            padding: 24px; border-radius: 16px; border: 2px solid {goal3_color}40; text-align: center;
            transition: all 0.3s ease;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>{goal3_meta['emoji']}</div>
                <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>{goal3_meta['name']}</div>
                <div style='font-size: 42px; font-weight: 800; color: {goal3_color};'>{goal3_sessions}/{goal3_target}</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px;'>Target: {goal3_target} session{"s" if goal3_target != 1 else ""}</div>
                <div style='font-size: 24px; margin-top: 10px;'>{goal3_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Overall progress
    total_sessions = goal1_sessions + goal2_sessions + goal3_sessions
    total_target = goal1_target + goal2_target + goal3_target
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if total_sessions >= total_target:
        overall_status = "🔥 Crushing it! You've hit your weekly targets!"
        overall_color = "#4ade80"
    elif total_sessions >= total_target - 1:
        overall_status = "💪 Almost there! Just one more session to hit your goals!"
        overall_color = "#fbbf24"
    else:
        overall_status = "📈 Keep going! You've got this week!"
        overall_color = "#667eea"
    
    progress_pct = min(total_sessions / total_target * 100, 100) if total_target > 0 else 0
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 28px; border-radius: 16px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;'>
                <div>
                    <div style='font-size: 22px; font-weight: 700; color: white;'>Total Weekly Sessions</div>
                    <div style='font-size: 15px; color: rgba(255,255,255,0.7); margin-top: 6px;'>{overall_status}</div>
                </div>
                <div style='font-size: 44px; font-weight: 800; color: {overall_color};'>{total_sessions}/{total_target}</div>
            </div>
            <div style='background: rgba(255,255,255,0.1); border-radius: 12px; height: 24px; overflow: hidden;'>
                <div style='background: {overall_color}; height: 100%; width: {progress_pct}%; transition: width 0.5s ease;'></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== WEIGHT GOALS ====================
    st.markdown("### 🎯 Your Weight Goals")
    
    # Load active goals from Supabase
    try:
        goals_df = load_goals(selected_user)
        
        # Filter active goals
        if len(goals_df) > 0 and 'Completed' in goals_df.columns:
            active_goals = goals_df[goals_df['Completed'] == False]
        else:
            active_goals = pd.DataFrame()
        
        # Display active goals with progress
        if len(active_goals) > 0:
            for idx, goal in active_goals.iterrows():
                goal_id = goal['id']
                exercise = goal['Exercise']
                arm = goal['Arm']
                target_kg = float(goal['Target_Weight'])
                
                # Get current 1RM (in kg)
                current_kg = get_user_1rm(selected_user, exercise, arm)
                
                # Calculate progress
                if current_kg >= target_kg:
                    # Goal achieved!
                    over_kg = current_kg - target_kg
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #4ade80 0%, #10b981 100%); 
                        padding: 25px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 6px 20px rgba(74,222,128,0.4);'>
                            <div style='font-size: 32px; text-align: center; margin-bottom: 10px;'>🎉</div>
                            <div style='font-size: 24px; font-weight: bold; color: white; text-align: center;'>
                                Goal Achieved!
                            </div>
                            <div style='font-size: 18px; color: rgba(255,255,255,0.9); text-align: center; margin-top: 8px;'>
                                {exercise} ({arm} arm): {target_kg:.1f} kg
                            </div>
                            <div style='font-size: 16px; color: rgba(255,255,255,0.8); text-align: center; margin-top: 5px;'>
                                You hit {current_kg:.1f} kg - that's {over_kg:.1f} kg over your goal! 💪
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Dismiss button
                    if st.button(f"✅ Mark as Complete & Celebrate", key=f"complete_{goal_id}"):
                        if complete_goal(goal_id):
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                else:
                    # Still working towards goal
                    progress_pct = (current_kg / target_kg) * 100
                    remaining_kg = target_kg - current_kg
                    
                    if progress_pct >= 90:
                        bar_color = "#fbbf24"
                        status_emoji = "🔥"
                    elif progress_pct >= 70:
                        bar_color = "#3b82f6"
                        status_emoji = "💪"
                    else:
                        bar_color = "#8b5cf6"
                        status_emoji = "📈"
                    
                    arm_emoji = "👈" if arm == "L" else "👉"
                    
                    st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 15px;'>
                            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                                <div>
                                    <div style='font-size: 20px; font-weight: bold; color: white;'>
                                        {status_emoji} {exercise} - {arm_emoji} {arm} Arm
                                    </div>
                                    <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 5px;'>
                                        Current: {current_kg:.1f} kg → Target: {target_kg:.1f} kg
                                    </div>
                                </div>
                                <div style='text-align: right;'>
                                    <div style='font-size: 28px; font-weight: bold; color: {bar_color};'>{progress_pct:.0f}%</div>
                                    <div style='font-size: 12px; color: rgba(255,255,255,0.6);'>{remaining_kg:.1f} kg to go</div>
                                </div>
                            </div>
                            <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 16px; overflow: hidden;'>
                                <div style='background: {bar_color}; height: 100%; width: {progress_pct}%; transition: width 0.3s ease;'></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Delete goal button
                    if st.button(f"🗑️ Remove Goal", key=f"delete_{goal_id}"):
                        if delete_goal(goal_id):
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("📝 No active goals set. Create one below!")
    except Exception as e:
        st.error(f"Error loading goals: {e}")
        
    st.markdown("---")
    
    # ==================== CREATE NEW GOAL ====================
    st.markdown("### ➕ Set a New Goal")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        goal_exercise = st.selectbox("Exercise:", ["20mm Edge", "Pinch", "Wrist Roller"], key="goal_exercise")
    
    with col2:
        goal_arm = st.selectbox("Arm:", ["L", "R"], key="goal_arm")
    
    with col3:
        current_1rm_kg = get_user_1rm(selected_user, goal_exercise, goal_arm)
        
        # Input in kg
        goal_weight_kg = st.number_input(
            f"Target Weight (kg) - Current: {current_1rm_kg:.1f} kg",
            min_value=float(current_1rm_kg),
            max_value=200.0,
            value=float(current_1rm_kg) + 5.0,
            step=0.25,
            key="goal_weight"
        )
    
    if st.button("🎯 Create Goal", type="primary", use_container_width=True):
        if save_goal(selected_user, goal_exercise, goal_arm, goal_weight_kg):
            st.success(f"✅ Goal created! Target: {goal_weight_kg:.1f} kg on {goal_exercise} ({goal_arm} arm)")
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    
    # ==================== CURRENT 1RMs ====================
    st.markdown("### 💪 Current 1RMs")
    
    col1, col2, col3 = st.columns(3)
    
    exercises_display = ["20mm Edge", "Pinch", "Wrist Roller"]
    colors = [
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
    ]
    
    for idx, (col, exercise, color) in enumerate(zip([col1, col2, col3], exercises_display, colors)):
        with col:
            edge_L_kg = get_user_1rm(selected_user, exercise, "L")
            edge_R_kg = get_user_1rm(selected_user, exercise, "R")
            
            st.markdown(f"""
                <div style='background: {color}; 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
                    <h4 style='margin: 0 0 15px 0; color: white; text-align: center;'>{exercise}</h4>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.8);'>👈 Left</div>
                            <div style='font-size: 28px; font-weight: bold; color: white;'>{edge_L_kg:.1f} kg</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.8);'>👉 Right</div>
                            <div style='font-size: 28px; font-weight: bold; color: white;'>{edge_R_kg:.1f} kg</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== COMPLETED GOALS HISTORY ====================
    try:
        # Load all goals and filter completed ones
        all_goals = load_goals(selected_user)
        if len(all_goals) > 0 and 'Completed' in all_goals.columns:
            completed_goals = all_goals[all_goals['Completed'] == True]
            
            if len(completed_goals) > 0:
                st.markdown("### 🏆 Completed Goals")
                
                for idx, goal in completed_goals.iterrows():
                    date_completed = goal.get('Date_Completed', 'N/A')
                    st.markdown(f"""
                        <div style='background: rgba(74,222,128,0.1); border-left: 4px solid #4ade80; 
                        padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 16px; font-weight: bold; color: #4ade80;'>
                                ✅ {goal['Exercise']} - {goal['Arm']} Arm: {goal['Target_Weight']} kg
                            </div>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 5px;'>
                                Completed: {date_completed}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading completed goals: {e}")

else:
    st.error("⚠️ Could not connect to database.")
