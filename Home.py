import streamlit as st
import sys
from textwrap import dedent
import pandas as pd
from datetime import datetime, timedelta
sys.path.append('.')
from utils.helpers import (
    init_session_state,
    inject_global_styles,
    USER_PLACEHOLDER,
    USER_LIST,
    INACTIVITY_THRESHOLD_DAYS,
    get_google_sheet,
    load_users_from_sheets,
    load_user_pins_from_sheets,
    user_selectbox_with_pin,
    load_data_from_sheets,
    load_activity_log,
    calculate_training_streak,
    get_bodyweight,
    get_user_1rm,
    get_working_max,
    calculate_relative_strength,
    estimate_1rm_epley,
    calculate_plates
)

st.set_page_config(page_title="Yves Climbing Tracker", page_icon="🧗", layout="wide")

init_session_state()
inject_global_styles()

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
    padding: 32px 24px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 15px 40px rgba(102,126,234,0.5);
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
        <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>
            🧗 Yves Climbing Tracker
        </h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
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
    user_pins = load_user_pins_from_sheets(spreadsheet)
else:
    available_users = USER_LIST.copy()
    user_pins = {user: "0000" for user in available_users}

# User selector in sidebar
st.sidebar.header("👤 User")
selected_user = user_selectbox_with_pin(
    available_users,
    user_pins,
    selector_key="user_selector_home",
    label="Select User:"
)
st.session_state.current_user = selected_user

if selected_user == USER_PLACEHOLDER:
    st.info("🔒 Select a profile from the sidebar and enter the PIN to unlock your dashboard.")
    st.stop()

# ==================== PERSONALIZED WELCOME ====================

# ==================== QUICK STATS OVERVIEW ====================
if workout_sheet:
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    if len(df) > 0:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['DateOnly'] = df['Date'].dt.date
        valid_dates = df['DateOnly'].dropna()
        total_sessions = len(valid_dates.unique())
        unique_dates_sorted = sorted(valid_dates.unique())
        current_streak = calculate_training_streak(unique_dates_sorted)
        last_workout = df['Date'].dropna().max()
        days_since = (pd.Timestamp.now() - last_workout).days if pd.notna(last_workout) else None
        df['WeekID'] = df['Date'].dt.to_period('W')
        active_weeks = len(df['WeekID'].dropna().unique())

        if days_since is not None and days_since >= INACTIVITY_THRESHOLD_DAYS:
            st.warning(f"⏰ It's been {days_since} days since your last logged workout. Head to **Log Workout** to keep the streak alive!")
        elif days_since is None:
            st.info("No dated workouts yet. Log your first session to start earning badges!")
        
        df_volume = df[~df['Exercise'].str.contains('1RM Test', na=False)]
        total_volume = (pd.to_numeric(df_volume['Actual_Load_kg'], errors='coerce') *
                        pd.to_numeric(df_volume['Reps_Per_Set'], errors='coerce') *
                        pd.to_numeric(df_volume['Sets_Completed'], errors='coerce')).sum()
        today_date = datetime.now().date()
        week_start = today_date - timedelta(days=today_date.weekday())
        df_week = df[(df["DateOnly"] >= week_start) & (df["DateOnly"] <= today_date)]
        sessions_this_week = len(df_week["DateOnly"].dropna().unique())

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

        hero_status = (
            "No sessions yet—log your first workout to get momentum."
            if days_since is None
            else ("Logged a session today. 🔥" if days_since == 0 else f"Last trained {days_since} day(s) ago.")
        )
        next_label = next_workout if next_workout else "Recovery Day"
        next_hint = "Auto-suggested rotation" if next_workout else "Take it easy today"
        hero_subtitle = f"{total_sessions} sessions • {active_weeks} active weeks"
        hero_html = f'<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 20px; padding: 28px 32px; margin: 20px 0 30px; box-shadow: 0 8px 24px rgba(240,147,251,0.4); border: 1px solid rgba(255,255,255,0.1);"><div style="display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap;"><div><div style="text-transform: uppercase; letter-spacing: 1px; font-size: 11px; opacity: 0.8; color: rgba(255,255,255,0.8);">Welcome back</div><div style="font-size: 32px; font-weight: 700; margin: 8px 0 12px; color: white;">{selected_user}! 👋</div><div style="font-size: 15px; line-height: 1.5; color: rgba(255,255,255,0.95);">{hero_status}</div><div style="margin-top: 10px; opacity: 0.85; font-size: 13px; color: rgba(255,255,255,0.9);">{hero_subtitle}</div></div><div style="text-align: right;"><div style="text-transform: uppercase; letter-spacing: 1px; font-size: 11px; opacity: 0.8; color: rgba(255,255,255,0.8);">Next focus</div><div style="font-size: 26px; font-weight: 700; margin: 8px 0 8px; color: white;">{next_label}</div><div style="font-size: 13px; opacity: 0.85; color: rgba(255,255,255,0.9);">{next_hint}</div></div></div></div>'
        st.markdown(hero_html, unsafe_allow_html=True)

        st.markdown("### 📊 Performance Dashboard")
        avg_rpe = df['RPE'].mean() if 'RPE' in df.columns else 0
        stat_cards = [
            {"value": f"{total_sessions}", "label": "Training Sessions", "caption": "Unique workout days"},
            {"value": f"{days_since if days_since is not None else '--'}", "label": "Days Since Last", "caption": "Keep the streak alive"},
            {"value": f"{total_volume:,.0f}", "label": "Total Volume (kg)", "caption": "Logged load"},
            {"value": f"{avg_rpe:.1f}/10", "label": "Average RPE", "caption": "Effort lately"},
            {"value": f"{sessions_this_week}", "label": "This Week", "caption": "Sessions logged"},
        ]
        stat_cols = st.columns(len(stat_cards))
        gradients = [
            'linear-gradient(135deg, #5651e5 0%, #6b3fa0 100%)',
            'linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%)',
            'linear-gradient(135deg, #e1306c 0%, #f77737 100%)',
            'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
            'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)'
        ]
        for i, (col, card) in enumerate(zip(stat_cols, stat_cards)):
            gradient = gradients[i]
            col.markdown(
                f"""
                <div style='background: {gradient};
                            border-radius: 16px;
                            padding: 20px;
                            text-align: center;
                            box-shadow: 0 4px 12px rgba(102,126,234,0.3);
                            border: 1px solid rgba(255,255,255,0.1);'>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.9); font-weight: 500; margin-bottom: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>{card['label']}</div>
                    <div style='font-size: 32px; font-weight: 700; color: white; margin: 6px 0; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{card['value']}</div>
                    <div style='font-size: 11px; color: rgba(255,255,255,0.85); margin-top: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>{card['caption']}</div>
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
                    elif activity == "Board":
                        color = "#a855f7"
                        label = "Board"
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
            <div style='margin-top: 20px; margin-bottom: 20px; display: flex; gap: 25px; font-size: 15px; justify-content: center; flex-wrap: wrap;'>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #667eea; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Gym (Finger Training)</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #a855f7; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Board Session</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #4ade80; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Climbing</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #fb923c; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Work Pullups</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #2d2d2d; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Rest</div>
            </div>
            """
            
            st.markdown(calendar_html + legend_html, unsafe_allow_html=True)
            
            gym_days = sum(1 for v in calendar_data.values() if v == "Gym")
            board_days = sum(1 for v in calendar_data.values() if v == "Board")
            climb_days = sum(1 for v in calendar_data.values() if v == "Climbing")
            work_days = sum(1 for v in calendar_data.values() if v == "Work")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏋️ Gym Days (365d)", gym_days)
            with col2:
                st.metric("🎯 Board Days (365d)", board_days)
            with col3:
                st.metric("🧗 Climbing Days (365d)", climb_days)
            with col4:
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
                indicator_L = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{edge_L - stored_edge_L:.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
                
            if edge_R > stored_edge_R + 1:
                indicator_R = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{edge_R - stored_edge_R:.1f}kg from baseline</div>'
            else:
                indicator_R = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%); 
                padding: 24px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 8px 24px rgba(79,172,254,0.4);
                border: 1px solid rgba(255,255,255,0.15);'>
                    <h4 style='margin: 0 0 18px 0; color: white; font-weight: 700; font-size: 18px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>🖐️ 20mm Edge</h4>
                    <div style='display: flex; justify-content: space-between; gap: 20px;'>
                        <div>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.9); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>LEFT</div>
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{edge_L:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.9); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>RIGHT</div>
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{edge_R:.1f} kg</div>
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
                indicator_L = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{pinch_L - stored_pinch_L:.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
                
            if pinch_R > stored_pinch_R + 1:
                indicator_R = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{pinch_R - stored_pinch_R:.1f}kg from baseline</div>'
            else:
                indicator_R = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #e1306c 0%, #f77737 100%); 
                padding: 24px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 8px 24px rgba(250,112,154,0.4);
                border: 1px solid rgba(255,255,255,0.15);'>
                    <h4 style='margin: 0 0 18px 0; color: white; font-weight: 700; font-size: 18px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>🤏 Pinch</h4>
                    <div style='display: flex; justify-content: space-between; gap: 20px;'>
                        <div>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.9); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>LEFT</div>
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{pinch_L:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.9); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>RIGHT</div>
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{pinch_R:.1f} kg</div>
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
                indicator_L = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{wrist_L - stored_wrist_L:.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
                
            if wrist_R > stored_wrist_R + 1:
                indicator_R = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{wrist_R - stored_wrist_R:.1f}kg from baseline</div>'
            else:
                indicator_R = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); 
                padding: 24px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 8px 24px rgba(48,207,208,0.4);
                border: 1px solid rgba(255,255,255,0.15);'>
                    <h4 style='margin: 0 0 18px 0; color: white; font-weight: 700; font-size: 18px;'>💪 Wrist Roller</h4>
                    <div style='display: flex; justify-content: space-between; gap: 20px;'>
                        <div>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;'>Left</div>
                            <div style='font-size: 32px; font-weight: 700; color: white;'>{wrist_L:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;'>Right</div>
                            <div style='font-size: 32px; font-weight: 700; color: white;'>{wrist_R:.1f} kg</div>
                            {indicator_R}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
    else:
        empty_hero = f'<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 20px; padding: 32px; margin: 20px 0 30px; box-shadow: 0 8px 24px rgba(240,147,251,0.4); border: 1px solid rgba(255,255,255,0.1);"><div style="text-align: center;"><div style="font-size: 48px; margin-bottom: 16px;">👋</div><h2 style="color: white; font-weight: 700; font-size: 32px; margin: 0 0 12px 0;">Welcome {selected_user}!</h2><p style="color: rgba(255,255,255,0.95); font-size: 16px; margin: 8px 0;">No training data yet. Log your first workout to unlock stats.</p><p style="color: rgba(255,255,255,0.85); font-size: 14px; margin-top: 12px;">Your dashboard will populate automatically.</p></div></div>'
        st.markdown(empty_hero, unsafe_allow_html=True)
        st.info("📝 No workout data yet. Head to **Log Workout** to get started!")

st.markdown("---")
st.markdown("### ⚡ Quick Actions")
quick_actions = [
    {"emoji": "📝", "title": "Log Workout", "desc": "Capture your latest sets & notes.", "href": "/Log_Workout", "gradient": "linear-gradient(135deg, #5651e5 0%, #6b3fa0 100%)"},
    {"emoji": "📈", "title": "View Progress", "desc": "Visualise PRs and trends.", "href": "/Progress", "gradient": "linear-gradient(135deg, #d946b5 0%, #e23670 100%)"},
    {"emoji": "🎯", "title": "Training Plan", "desc": "Review the upcoming focus.", "href": "/Goals", "gradient": "linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%)"},
]
quick_cols = st.columns(len(quick_actions))
for col, action in zip(quick_cols, quick_actions):
    col.markdown(
        f"""
        <a href='{action['href']}' target='_self' style='text-decoration:none;'>
            <div style='background: {action['gradient']};
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 16px;
                        padding: 24px;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(102,126,234,0.3);
                        color: #fff;'>
                <div style='font-size: 36px; margin-bottom: 12px;'>{action['emoji']}</div>
                <div style='font-size: 18px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{action['title']}</div>
                <div style='font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>{action['desc']}</div>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

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

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 14px; padding: 20px;'>
        💪 Built for climbers, by climbers | Keep crushing it! 🧗
    </div>
""", unsafe_allow_html=True)
