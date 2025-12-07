import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Goals", page_icon="🎯", layout="wide")

init_session_state()

# ==================== HEADER ====================
st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
    padding: 30px 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(250,112,154,0.4);'>
        <h1 style='color: white; font-size: 42px; margin: 0;'>🎯 Goals & Training Plan</h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 8px;'>
            Set ambitious targets and crush them one rep at a time
        </p>
    </div>
""", unsafe_allow_html=True)

# Connect to Google Sheets
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

# Load users
if spreadsheet:
    available_users = load_users_from_sheets(spreadsheet)
else:
    available_users = USER_LIST.copy()

# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    available_users,
    index=available_users.index(st.session_state.current_user) if st.session_state.current_user in available_users else 0,
    key="user_selector_goals"
)

selected_user = st.session_state.current_user

if workout_sheet:
    # Load data
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    # ==================== WEEKLY WORKOUT TRACKER ====================
    st.markdown("### 📅 This Week's Progress")
    
    # Calculate this week's sessions
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # Monday
    df['Date'] = pd.to_datetime(df['Date'])
    df_week = df[df['Date'] >= week_start]
    sessions_this_week = len(df_week['Date'].dt.date.unique()) if len(df) > 0 else 0
    
    weekly_target = 3  # Default target
    progress_pct = min((sessions_this_week / weekly_target) * 100, 100)
    
    # Visual progress bar
    if sessions_this_week >= weekly_target:
        bar_color = "#4ade80"
        status_emoji = "🔥"
        status_text = "Target smashed!"
    elif sessions_this_week >= weekly_target - 1:
        bar_color = "#fbbf24"
        status_emoji = "💪"
        status_text = "Almost there!"
    else:
        bar_color = "#3b82f6"
        status_emoji = "📈"
        status_text = "Keep going!"
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 25px; border-radius: 12px; margin-bottom: 20px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                <div>
                    <div style='font-size: 18px; font-weight: bold; color: white;'>{status_emoji} Weekly Workouts</div>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 5px;'>{status_text}</div>
                </div>
                <div style='font-size: 36px; font-weight: bold; color: {bar_color};'>{sessions_this_week}/{weekly_target}</div>
            </div>
            <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 20px; overflow: hidden;'>
                <div style='background: {bar_color}; height: 100%; width: {progress_pct}%; transition: width 0.3s ease;'></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== WEIGHT GOALS ====================
    st.markdown("### 🎯 Your Weight Goals")
    
    # Initialize goals sheet if it doesn't exist
    try:
        goals_sheet = spreadsheet.worksheet("Goals")
    except:
        # Create new sheet
        goals_sheet = spreadsheet.add_worksheet(title="Goals", rows=100, cols=10)
        goals_sheet.append_row(["User", "Exercise", "Arm", "Target_Weight", "Completed", "Date_Set", "Date_Completed"])
    
    # Load active goals
    goals_data = goals_sheet.get_all_records()
    goals_df = pd.DataFrame(goals_data)
    
    # Filter active goals - FIX: handle different data types for Completed
    if len(goals_df) > 0:
        # Convert Completed to string and check for various "false" values
        goals_df['Completed_str'] = goals_df['Completed'].astype(str).str.lower()
        active_goals = goals_df[(goals_df['User'] == selected_user) & 
                                (goals_df['Completed_str'].isin(['false', '0', '', 'no']))]
    else:
        active_goals = pd.DataFrame()
    
    # Display active goals with progress
    if len(active_goals) > 0:
        for idx, goal in active_goals.iterrows():
            exercise = goal['Exercise']
            arm = goal['Arm']
            target = float(goal['Target_Weight'])
            
            # Get current 1RM
            current = get_user_1rm(spreadsheet, selected_user, exercise, arm)
            
            # Calculate progress
            if current >= target:
                # Goal achieved!
                progress_pct = 100
                bar_color = "#4ade80"
                status = "🎉 ACHIEVED!"
                
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #4ade80 0%, #10b981 100%); 
                    padding: 25px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 6px 20px rgba(74,222,128,0.4);'>
                        <div style='font-size: 32px; text-align: center; margin-bottom: 10px;'>🎉</div>
                        <div style='font-size: 24px; font-weight: bold; color: white; text-align: center;'>
                            Goal Achieved!
                        </div>
                        <div style='font-size: 18px; color: rgba(255,255,255,0.9); text-align: center; margin-top: 8px;'>
                            {exercise} ({arm} arm): {target} kg
                        </div>
                        <div style='font-size: 16px; color: rgba(255,255,255,0.8); text-align: center; margin-top: 5px;'>
                            You hit {current} kg - that's {current - target:.1f} kg over your goal! 💪
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Dismiss button
                if st.button(f"✅ Mark as Complete & Celebrate", key=f"complete_{idx}"):
                    # Update goal as completed
                    row_num = idx + 2  # +2 because of header and 0-indexing
                    goals_sheet.update_cell(row_num, 5, "TRUE")  # Completed column (as string)
                    goals_sheet.update_cell(row_num, 7, datetime.now().strftime("%Y-%m-%d"))  # Date completed
                    st.balloons()
                    st.rerun()
            else:
                # Still working towards goal
                progress_pct = (current / target) * 100
                remaining = target - current
                
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
                                    Current: {current} kg → Target: {target} kg
                                </div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='font-size: 28px; font-weight: bold; color: {bar_color};'>{progress_pct:.0f}%</div>
                                <div style='font-size: 12px; color: rgba(255,255,255,0.6);'>{remaining:.1f} kg to go</div>
                            </div>
                        </div>
                        <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 16px; overflow: hidden;'>
                            <div style='background: {bar_color}; height: 100%; width: {progress_pct}%; transition: width 0.3s ease;'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Delete goal button
                if st.button(f"🗑️ Remove Goal", key=f"delete_{idx}"):
                    row_num = idx + 2
                    goals_sheet.delete_rows(row_num)
                    st.rerun()
    else:
        st.info("📝 No active goals set. Create one below!")
    
    st.markdown("---")
    
    # ==================== CREATE NEW GOAL ====================
    st.markdown("### ➕ Set a New Goal")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        goal_exercise = st.selectbox("Exercise:", ["20mm Edge", "Pinch", "Wrist Roller"], key="goal_exercise")
    
    with col2:
        goal_arm = st.selectbox("Arm:", ["L", "R"], key="goal_arm")
    
    with col3:
        current_1rm = get_user_1rm(spreadsheet, selected_user, goal_exercise, goal_arm)
        goal_weight = st.number_input(
            f"Target Weight (kg) - Current: {current_1rm} kg",
            min_value=float(current_1rm),
            max_value=200.0,
            value=float(current_1rm) + 5.0,
            step=0.25,
            key="goal_weight"
        )
    
    if st.button("🎯 Create Goal", type="primary", use_container_width=True):
        # Add goal to sheet
        goals_sheet.append_row([
            selected_user,
            goal_exercise,
            goal_arm,
            goal_weight,
            "FALSE",  # Not completed (as string)
            datetime.now().strftime("%Y-%m-%d"),
            ""  # Date completed (empty)
        ])
        st.success(f"✅ Goal created! Target: {goal_weight} kg on {goal_exercise} ({goal_arm} arm)")
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
            edge_L = get_user_1rm(spreadsheet, selected_user, exercise, "L")
            edge_R = get_user_1rm(spreadsheet, selected_user, exercise, "R")
            
            st.markdown(f"""
                <div style='background: {color}; 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
                    <h4 style='margin: 0 0 15px 0; color: white; text-align: center;'>{exercise}</h4>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.8);'>👈 Left</div>
                            <div style='font-size: 28px; font-weight: bold; color: white;'>{edge_L} kg</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.8);'>👉 Right</div>
                            <div style='font-size: 28px; font-weight: bold; color: white;'>{edge_R} kg</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== COMPLETED GOALS HISTORY ====================
    if len(goals_df) > 0:
        # Filter completed goals - handle different true values
        completed_goals = goals_df[(goals_df['User'] == selected_user) & 
                                   (goals_df['Completed_str'].isin(['true', '1', 'yes', 'TRUE']))]
        
        if len(completed_goals) > 0:
            st.markdown("### 🏆 Completed Goals")
            
            for idx, goal in completed_goals.iterrows():
                st.markdown(f"""
                    <div style='background: rgba(74,222,128,0.1); border-left: 4px solid #4ade80; 
                    padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                        <div style='font-size: 16px; font-weight: bold; color: #4ade80;'>
                            ✅ {goal['Exercise']} - {goal['Arm']} Arm: {goal['Target_Weight']} kg
                        </div>
                        <div style='font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 5px;'>
                            Completed: {goal['Date_Completed']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

else:
    st.error("⚠️ Could not connect to Google Sheets.")
