import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import *
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Yves Climbing Tracker", page_icon="🧗", layout="wide")

init_session_state()

# Current date banner
today = datetime.now()
friendly_date = today.strftime("%A %d %B %Y")

st.markdown(
    f"""
    <div style="text-align: center; color: rgba(255,255,255,0.9); margin-top: -10px; margin-bottom: 10px;">
        <span style="font-size: 16px;">📅 {friendly_date}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==================== HEADER WITH BANNER ====================
st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    padding: 40px 20px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
        <h1 style='color: white; font-size: 48px; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            🧗 Yves Climbing Tracker
        </h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 20px; margin-top: 10px;'>
            Build unbreakable finger strength, track your gains, dominate the leaderboard
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
    key="user_selector_home"
)

selected_user = st.session_state.current_user

# ==================== PERSONALIZED WELCOME ====================
st.markdown(f"## Welcome back, {selected_user}! 👋")

# ==================== QUICK STATS OVERVIEW ====================
if workout_sheet:
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    if len(df) > 0:
        st.markdown("### 📊 Your Stats at a Glance")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Total SESSIONS (unique dates)
        with col1:
            df['Date'] = pd.to_datetime(df['Date'])
            total_sessions = len(df['Date'].dt.date.unique())
            
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(240,147,251,0.4);'>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{total_sessions}</div>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;'>Training Sessions</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Last workout
        with col2:
            last_workout = df['Date'].max()
            days_since = (pd.Timestamp.now() - last_workout).days
            
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(79,172,254,0.4);'>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{days_since}</div>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;'>Days Since Last</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Total volume (excluding 1RM tests)
        with col3:
            df_volume = df[~df['Exercise'].str.contains('1RM Test', na=False)]
            
            total_volume = (pd.to_numeric(df_volume['Actual_Load_kg'], errors='coerce') *
                           pd.to_numeric(df_volume['Reps_Per_Set'], errors='coerce') *
                           pd.to_numeric(df_volume['Sets_Completed'], errors='coerce')).sum()
        
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(250,112,154,0.4);'>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{total_volume:,.0f}</div>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;'>Total Volume (kg)</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Avg RPE
        with col4:
            avg_rpe = df['RPE'].mean() if 'RPE' in df.columns else 0
            
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(48,207,208,0.4);'>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{avg_rpe:.1f}/10</div>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;'>Average RPE</div>
                </div>
            """, unsafe_allow_html=True)
        
        # This week's sessions
        with col5:
            today_date = datetime.now().date()
            week_start = today_date - timedelta(days=today_date.weekday())
        
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
            df_week = df[(df["Date"] >= week_start) & (df["Date"] <= today_date)]
            sessions_this_week = len(df_week["Date"].unique())
        
            st.markdown(
                f"""
                <div style="text-align: center; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                            padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(168,237,234,0.4);">
                    <div style="font-size: 36px; font-weight: bold; color: #333;">
                        {sessions_this_week}
                    </div>
                    <div style="font-size: 14px; color: #555; margin-top: 5px;">
                        This Week
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Next workout suggestion
        next_workout = None
        try:
            df_ex = df[df["Exercise"].isin(["Pinch", "Wrist Roller"])].copy()
            if len(df_ex) > 0:
                df_ex["Date"] = pd.to_datetime(df_ex["Date"], errors="coerce")
                last_row = df_ex.sort_values("Date").iloc[-1]
                last_ex = last_row["Exercise"]
                next_workout = "Wrist Roller" if last_ex == "Pinch" else "Pinch"
            else:
                next_workout = "Pinch"
        except Exception:
            next_workout = None
    
        if next_workout:
            st.markdown(
                f"""
                <div style="margin-top: 20px; margin-bottom: 10px;">
                    <div style="
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        padding: 18px 24px;
                        border-radius: 14px;
                        box-shadow: 0 6px 18px rgba(79,172,254,0.4);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <div>
                            <div style="font-size: 14px; color: rgba(255,255,255,0.85);">
                                Next planned session
                            </div>
                            <div style="font-size: 22px; font-weight: 700; color: #ffffff; margin-top: 4px;">
                                {next_workout}
                            </div>
                        </div>
                        <div style="font-size: 32px;">
                            💡
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 📅 Training Activity Calendar")
        
        # Load all activities
        if spreadsheet:
            activity_df = load_activity_log(spreadsheet, selected_user)
            workout_df = df if len(df) > 0 else pd.DataFrame()
            
            calendar_data = {}
            
            # Add gym workouts
            if len(workout_df) > 0:
                workout_df["Date"] = pd.to_datetime(workout_df["Date"], errors="coerce").dt.date
                for date in workout_df["Date"].dropna().unique():
                    calendar_data[str(date)] = "Gym"
            
            # Add climbing and work
            if len(activity_df) > 0:
                activity_df["Date"] = pd.to_datetime(activity_df["Date"], errors="coerce").dt.date
                for _, row in activity_df.iterrows():
                    date_str = str(row["Date"])
                    activity_type = row["ActivityType"]
                    if date_str not in calendar_data:
                        calendar_data[date_str] = activity_type
            
            # Generate calendar
            today_cal = datetime.now().date()
            start_date = today_cal - timedelta(days=364)
            
            squares_list = []
            for i in range(365):
                current_date = start_date + timedelta(days=i)
                date_str = str(current_date)
                
                if date_str in calendar_data:
                    activity = calendar_data[date_str]
                    if activity == "Gym":
                        color = "#667eea"
                        label = "Gym"
                    elif activity == "Climbing":
                        color = "#4ade80"
                        label = "Climbing"
                    elif activity == "Work":
                        color = "#fb923c"
                        label = "Work"
                    else:
                        color = "#667eea"
                        label = "Gym"
                else:
                    color = "#2d2d2d"
                    label = "Rest"
                
                square = f'<div title="{current_date.strftime("%Y-%m-%d")} - {label}" style="width: 18px; height: 18px; background: {color}; border-radius: 3px;"></div>'
                squares_list.append(square)
            
            calendar_html = '<div style="display: flex; flex-wrap: wrap; gap: 4px; max-width: 100%; margin: 20px 0;">' + ''.join(squares_list) + '</div>'
            
            legend_html = """
            <div style='margin-top: 20px; margin-bottom: 20px; display: flex; gap: 30px; font-size: 16px; justify-content: center;'>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #667eea; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Gym (Arm Lifting)</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #4ade80; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Climbing</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #fb923c; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Work Pullups</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #2d2d2d; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Rest</div>
            </div>
            """
            
            st.markdown(calendar_html + legend_html, unsafe_allow_html=True)
            
            gym_days = sum(1 for v in calendar_data.values() if v == "Gym")
            climb_days = sum(1 for v in calendar_data.values() if v == "Climbing")
            work_days = sum(1 for v in calendar_data.values() if v == "Work")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏋️ Gym Days (365d)", gym_days)
            with col2:
                st.metric("🧗 Climbing Days (365d)", climb_days)
            with col3:
                st.metric("💪 Work Days (365d)", work_days)

        st.markdown("---")
        
        # CURRENT STRENGTH (WORKING MAX)
        st.markdown("### 💪 Your Current Strength")
        st.caption("📊 Based on recent training performance (auto-updated from last 8 weeks)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            edge_L = get_working_max(spreadsheet, selected_user, "20mm Edge", "L")
            edge_R = get_working_max(spreadsheet, selected_user, "20mm Edge", "R")
            stored_edge_L = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "L")
            stored_edge_R = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "R")
            
            if edge_L > stored_edge_L + 1:
                indicator_L = f'<div style="font-size: 11px; color: #4ade80; margin-top: 5px;">📈 +{edge_L - stored_edge_L:.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: #888; margin-top: 5px;">✓ From test</div>'
                
            if edge_R > stored_edge_R + 1:
                indicator_R = f'<div style="font-size: 11px; color: #4ade80; margin-top: 5px;">📈 +{edge_R - stored_edge_R:.1f}kg from baseline</div>'
            else:
                indicator_R = '<div style="font-size: 11px; color: #888; margin-top: 5px;">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: rgba(255,215,0,0.1); border-left: 5px solid #FFD700; 
                padding: 20px; border-radius: 10px; margin-bottom: 15px;'>
                    <h4 style='margin: 0 0 15px 0; color: #FFD700;'>🖐️ 20mm Edge</h4>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <div style='font-size: 12px; color: #888;'>Left</div>
                            <div style='font-size: 28px; font-weight: bold;'>{edge_L:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 12px; color: #888;'>Right</div>
                            <div style='font-size: 28px; font-weight: bold;'>{edge_R:.1f} kg</div>
                            {indicator_R}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            pinch_L = get_working_max(spreadsheet, selected_user, "Pinch", "L")
            pinch_R = get_working_max(spreadsheet, selected_user, "Pinch", "R")
            stored_pinch_L = get_user_1rm(spreadsheet, selected_user, "Pinch", "L")
            stored_pinch_R = get_user_1rm(spreadsheet, selected_user, "Pinch", "R")
            
            if pinch_L > stored_pinch_L + 1:
                indicator_L = f'<div style="font-size: 11px; color: #4ade80; margin-top: 5px;">📈 +{pinch_L - stored_pinch_L:.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: #888; margin-top: 5px;">✓ From test</div>'
                
            if pinch_R > stored_pinch_R + 1:
                indicator_R = f'<div style="font-size: 11px; color: #4ade80; margin-top: 5px;">📈 +{pinch_R - stored_pinch_R:.1f}kg from baseline</div>'
            else:
                indicator_R = '<div style="font-size: 11px; color: #888; margin-top: 5px;">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: rgba(192,192,192,0.1); border-left: 5px solid #C0C0C0; 
                padding: 20px; border-radius: 10px; margin-bottom: 15px;'>
                    <h4 style='margin: 0 0 15px 0; color: #C0C0C0;'>🤏 Pinch</h4>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <div style='font-size: 12px; color: #888;'>Left</div>
                            <div style='font-size: 28px; font-weight: bold;'>{pinch_L:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 12px; color: #888;'>Right</div>
                            <div style='font-size: 28px; font-weight: bold;'>{pinch_R:.1f} kg</div>
                            {indicator_R}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            wrist_L = get_working_max(spreadsheet, selected_user, "Wrist Roller", "L")
            wrist_R = get_working_max(spreadsheet, selected_user, "Wrist Roller", "R")
            stored_wrist_L = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "L")
            stored_wrist_R = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "R")
            
            if wrist_L > stored_wrist_L + 1:
                indicator_L = f'<div style="font-size: 11px; color: #4ade80; margin-top: 5px;">📈 +{wrist_L - stored_wrist_L:.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: #888; margin-top: 5px;">✓ From test</div>'
                
            if wrist_R > stored_wrist_R + 1:
                indicator_R = f'<div style="font-size: 11px; color: #4ade80; margin-top: 5px;">📈 +{wrist_R - stored_wrist_R:.1f}kg from baseline</div>'
            else:
                indicator_R = '<div style="font-size: 11px; color: #888; margin-top: 5px;">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: rgba(205,127,50,0.1); border-left: 5px solid #CD7F32; 
                padding: 20px; border-radius: 10px; margin-bottom: 15px;'>
                    <h4 style='margin: 0 0 15px 0; color: #CD7F32;'>💪 Wrist Roller</h4>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <div style='font-size: 12px; color: #888;'>Left</div>
                            <div style='font-size: 28px; font-weight: bold;'>{wrist_L:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 12px; color: #888;'>Right</div>
                            <div style='font-size: 28px; font-weight: bold;'>{wrist_R:.1f} kg</div>
                            {indicator_R}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
    else:
        st.info("📝 No workout data yet. Head to **Log Workout** to get started!")

# ==================== QUICK ACTIONS ====================
st.markdown("---")
st.markdown("### 🚀 Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <a href='/Log_Workout' target='_self' style='text-decoration: none;'>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; border-radius: 15px; text-align: center; cursor: pointer; 
            transition: transform 0.2s; box-shadow: 0 6px 20px rgba(102,126,234,0.4);'>
                <div style='font-size: 48px; margin-bottom: 10px;'>📝</div>
                <div style='font-size: 20px; font-weight: bold; color: white;'>Log Workout</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.8); margin-top: 8px;'>
                    Record your latest training session
                </div>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <a href='/Progress' target='_self' style='text-decoration: none;'>
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
            padding: 30px; border-radius: 15px; text-align: center; cursor: pointer; 
            transition: transform 0.2s; box-shadow: 0 6px 20px rgba(240,147,251,0.4);'>
                <div style='font-size: 48px; margin-bottom: 10px;'>📈</div>
                <div style='font-size: 20px; font-weight: bold; color: white;'>View Progress</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.8); margin-top: 8px;'>
                    Track your gains over time
                </div>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <a href='/Goals' target='_self' style='text-decoration: none;'>
            <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
            padding: 30px; border-radius: 15px; text-align: center; cursor: pointer; 
            transition: transform 0.2s; box-shadow: 0 6px 20px rgba(79,172,254,0.4);'>
                <div style='font-size: 48px; margin-bottom: 10px;'>🎯</div>
                <div style='font-size: 20px; font-weight: bold; color: white;'>Training Plan</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.8); margin-top: 8px;'>
                    View your weekly schedule
                </div>
            </div>
        </a>
    """, unsafe_allow_html=True)

# ==================== HOW TO USE GUIDE ====================
st.markdown("---")
st.markdown("### 📖 How to Use This Tracker")

with st.expander("💪 **Exercise Technique Tips**", expanded=False):
    st.markdown("""
    **Lifting Edge (18–20 mm pickup)**
    
    - Clip a portable edge or hangboard to a lifting pin loaded with plates on the floor.
    - Stand so the device is roughly under your armpit, arm in line with the front of your body.
    - Take a solid half‑crimp on the edge with a comfortable, slightly rounded radius.
    - Brace your trunk, bend the knees, then lift by driving through the legs while keeping the shoulder packed and the arm close.
    - Set the weight back down between reps; focus on crisp, controlled pickups rather than long holds.
    
    **Pinch Block Pickup**
    
    - Attach a pinch block to the same style of lifting pin and plates.
    - Place the thumb deep along the side of the block and keep the fingers a bit straighter than a normal climbing grip.
    - Slightly pronate the wrist so the block "cams" into the hand and feels locked in.
    - Stand over the pin, arm close to the body, and lift mainly from the legs while maintaining that precise pinch.
    - Put the weight down between reps and reset your grip each time so every lift is consistent.
    
    **Wrist Wrench / Heavy Roller Pickup**
    
    - Connect the wrist‑wrench or heavy‑roller handle directly to a short lifting pin with plates.
    - Stand so the handle hangs near the front of your thigh with the arm mostly straight and shoulder relaxed.
    - Avoid using a long rope and "rolling" the weight; instead, keep the connection short so the lift comes from driving through the legs.
    - Maintain a strong wrist and open‑hand position against the handle as you pick the weight up and set it back down.
    - Use smooth, powerful reps to develop forearm and wrist strength that carries over to slopers and open‑hand grips.
    """)

with st.expander("🎓 **Getting Started Guide**", expanded=False):
    st.markdown("""
    #### 1️⃣ **Log Your Workouts**
    - Go to **Log Workout** page
    - Select your exercise (20mm Edge, Pinch, or Wrist Roller)
    - The app will show your current strength and calculate target weights
    - Enter the weight you lifted, reps, sets, and RPE
    - Add notes about how it felt
    - Click "Log Workout" to save!
    
    #### 2️⃣ **Track Your Progress**
    - Visit the **Progress** page to see:
        - Charts showing your load over time
        - RPE trends to monitor fatigue
        - Summary statistics
        - Recent workout history
    
    #### 3️⃣ **Follow Your Training Plan**
    - Check the **Goals** page for:
        - Weekly training schedule
        - Technique tips for each exercise
        - Current strength levels
        - Training consistency tracker
    
    #### 4️⃣ **Compete on the Leaderboard**
    - Head to **Leaderboard** to:
        - See who's lifting the most weight
        - Compare left vs right arm strength
        - View total training volume rankings
        - Get motivated by your crew!
    
    #### 5️⃣ **Manage Your Profile**
    - Use **Profile** page to:
        - Update your bodyweight
        - View all your current strength levels
        - Create new users for your climbing crew
    
    ---
    
    #### 💡 **Pro Tips**
    - **1RM Tests**: Log "1RM Test" exercises every 3-4 weeks to update your baseline
    - **Auto-Updates**: Your strength estimates update automatically based on recent training
    - **Consistency**: Train 3-6x per week following the schedule
    - **Recovery**: Watch your RPE trends - if consistently high, take a rest day
    - **Progression**: Aim to increase weight by 2.5-5kg every 2-3 weeks
    - **Balance**: Train both arms equally to prevent imbalances
    """)

with st.expander("❓ **FAQ - Frequently Asked Questions**", expanded=False):
    st.markdown("""
    **Q: What is RPE?**  
    A: Rate of Perceived Exertion - how hard the set felt on a scale of 1-10. 
    - 7 = Could do 3 more reps
    - 8 = Could do 2 more reps  
    - 9 = Could do 1 more rep
    - 10 = Absolute maximum effort
    
    **Q: How does the strength calculation work?**  
    A: The app uses your recent training loads (last 8 weeks) to estimate your current strength using the Epley formula. If you haven't done a 1RM test recently but have been lifting heavier in training, it will show your estimated strength is higher than your baseline test.
    
    **Q: How often should I test my 1RM?**  
    A: Every 3-4 weeks. The app auto-estimates between tests, but periodic testing keeps your baseline accurate.
    
    **Q: What if I can't hit the prescribed weight?**  
    A: That's fine! Enter what you actually lifted. The app tracks everything and adjusts.
    
    **Q: Can multiple people use this tracker?**  
    A: Yes! Go to Profile → Create New User to add climbing partners.
    
    **Q: What do the plate calculations mean?**  
    A: The app shows exactly which weight plates to load on each side of the cable machine.
    
    **Q: Why does it show "+X kg from baseline"?**  
    A: This means your recent training suggests you're stronger than your last test. Consider doing a new 1RM test to confirm!
    """)

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 14px; padding: 20px;'>
        💪 Built for climbers, by climbers | Keep crushing it! 🧗
    </div>
""", unsafe_allow_html=True)
