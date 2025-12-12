import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
from utils.helpers import USER_PLACEHOLDER
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Goals", page_icon="🎯", layout="wide")

init_session_state()
inject_global_styles()

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

# Connect to Google Sheets
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

# Load users
if spreadsheet:
    available_users = load_users_from_sheets(spreadsheet)
    user_pins = load_user_pins_from_sheets(spreadsheet)
else:
    available_users = USER_LIST.copy()
    user_pins = {user: "0000" for user in available_users}

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

if workout_sheet:
    # Load data
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    activity_df = load_activity_log(spreadsheet, user=selected_user)
    
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
    
    st.info("💪 **Your weekly targets:** 2-3 Finger Training sessions • 1 Board Session • 2-3 Climbing Sessions")
    
    
    # Calculate this week's progress
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    
    # Gym sessions (finger training)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df_week = df[(df["Date"] >= week_start) & (df["Date"] <= today)]
    gym_sessions = len(df_week["Date"].unique()) if len(df_week) > 0 else 0
    
    # Activity sessions
    board_sessions = 0
    climb_sessions = 0
    if len(activity_df) > 0:
        activity_df["Date"] = pd.to_datetime(activity_df["Date"], errors="coerce").dt.date
        activity_week = activity_df[(activity_df["Date"] >= week_start) & (activity_df["Date"] <= today)]
        board_sessions = len(activity_week[activity_week["ActivityType"] == "Board"])
        climb_sessions = len(activity_week[activity_week["ActivityType"] == "Climbing"])
    
    # Weekly goals
    gym_target = (2, 3)  # 2-3 sessions
    board_target = 1
    climb_target = (2, 3)  # 2-3 sessions
    
    # Create goal cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gym_status = "✅" if gym_sessions >= gym_target[1] else "⏳"
        gym_color = "#4ade80" if gym_sessions >= gym_target[1] else "#fbbf24" if gym_sessions >= gym_target[0] else "#667eea"
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, {gym_color}20, {gym_color}10); 
            padding: 24px; border-radius: 16px; border: 2px solid {gym_color}40; text-align: center;
            transition: all 0.3s ease;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>🏋️</div>
                <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>Finger Training</div>
                <div style='font-size: 42px; font-weight: 800; color: {gym_color};'>{gym_sessions}/{gym_target[1]}</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px;'>Target: {gym_target[0]}-{gym_target[1]} sessions</div>
                <div style='font-size: 24px; margin-top: 10px;'>{gym_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        board_status = "✅" if board_sessions >= board_target else "⏳"
        board_color = "#a855f7" if board_sessions >= board_target else "#667eea"
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, {board_color}20, {board_color}10); 
            padding: 24px; border-radius: 16px; border: 2px solid {board_color}40; text-align: center;
            transition: all 0.3s ease;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>🎯</div>
                <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>Board Session</div>
                <div style='font-size: 42px; font-weight: 800; color: {board_color};'>{board_sessions}/{board_target}</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px;'>Target: {board_target} session</div>
                <div style='font-size: 24px; margin-top: 10px;'>{board_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        climb_status = "✅" if climb_sessions >= climb_target[1] else "⏳"
        climb_color = "#4ade80" if climb_sessions >= climb_target[1] else "#fbbf24" if climb_sessions >= climb_target[0] else "#667eea"
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, {climb_color}20, {climb_color}10); 
            padding: 24px; border-radius: 16px; border: 2px solid {climb_color}40; text-align: center;
            transition: all 0.3s ease;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>🧗</div>
                <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>Climbing</div>
                <div style='font-size: 42px; font-weight: 800; color: {climb_color};'>{climb_sessions}/{climb_target[1]}</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px;'>Target: {climb_target[0]}-{climb_target[1]} sessions</div>
                <div style='font-size: 24px; margin-top: 10px;'>{climb_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Overall progress
    total_sessions = gym_sessions + board_sessions + climb_sessions
    total_min = gym_target[0] + board_target + climb_target[0]
    total_max = gym_target[1] + board_target + climb_target[1]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if total_sessions >= total_min:
        overall_status = "🔥 Crushing it! You've hit your minimum weekly targets!"
        overall_color = "#4ade80"
    elif total_sessions >= total_min - 2:
        overall_status = "💪 Almost there! Just a few more sessions to hit your goals!"
        overall_color = "#fbbf24"
    else:
        overall_status = "📈 Keep going! You've got this week!"
        overall_color = "#667eea"
    
    progress_pct = min(total_sessions / total_max * 100, 100)
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 28px; border-radius: 16px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;'>
                <div>
                    <div style='font-size: 22px; font-weight: 700; color: white;'>Total Weekly Sessions</div>
                    <div style='font-size: 15px; color: rgba(255,255,255,0.7); margin-top: 6px;'>{overall_status}</div>
                </div>
                <div style='font-size: 44px; font-weight: 800; color: {overall_color};'>{total_sessions}/{total_max}</div>
            </div>
            <div style='background: rgba(255,255,255,0.1); border-radius: 12px; height: 24px; overflow: hidden;'>
                <div style='background: {overall_color}; height: 100%; width: {progress_pct}%; transition: width 0.5s ease;'></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== WEIGHT GOALS ====================
    st.markdown("### 🎯 Your Weight Goals")
    
    # Initialize goals sheet - IMPROVED ERROR HANDLING
    try:
        # Try to get existing Goals worksheet
        all_sheets = [ws.title for ws in spreadsheet.worksheets()]
        
        if "Goals" in all_sheets:
            goals_sheet = spreadsheet.worksheet("Goals")
        else:
            # Only create if it doesn't exist
            time.sleep(0.5)  # Prevent rate limiting
            goals_sheet = spreadsheet.add_worksheet(title="Goals", rows=100, cols=10)
            goals_sheet.append_row(["User", "Exercise", "Arm", "Target_Weight", "Completed", "Date_Set", "Date_Completed"])
    except Exception as e:
        st.error(f"Error accessing Goals sheet: {e}")
        goals_sheet = None
    
    if goals_sheet:
        # Load active goals
        try:
            goals_data = goals_sheet.get_all_records()
            goals_df = pd.DataFrame(goals_data)
        except Exception as e:
            st.error(f"Error loading goals: {e}")
            goals_df = pd.DataFrame()
        
        # Filter active goals - handle empty dataframe and different data types
        if len(goals_df) > 0 and 'Completed' in goals_df.columns:
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
                        time.sleep(1)  # Brief delay before rerun
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
                        time.sleep(1)
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
            try:
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
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error creating goal: {e}")
    
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
    if goals_sheet and len(goals_df) > 0 and 'Completed_str' in goals_df.columns:
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
