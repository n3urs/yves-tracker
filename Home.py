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
    calculate_plates,
    load_custom_workout_logs
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
    # Welcome banner for new users
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
        padding: 20px 24px; border-radius: 16px; margin: 20px 0; box-shadow: 0 6px 20px rgba(240,147,251,0.3);
        border: 1px solid rgba(255,255,255,0.1); text-align: center;'>
            <div style='font-size: 32px; margin-bottom: 10px;'>👋</div>
            <h3 style='color: white; font-weight: 600; font-size: 22px; margin: 0 0 10px 0; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
                Welcome! Ready to track your finger strength?
            </h3>
            <p style='color: rgba(255,255,255,0.95); font-size: 15px; margin: 0 0 16px 0; line-height: 1.5;'>
                Create your profile to start logging workouts and monitoring your progress 💪
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create profile button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🆕 Create Your Profile", use_container_width=True, type="primary"):
            st.switch_page("pages/5_Profile.py")
    
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    st.info("🔒 Already have a profile? Select it from the sidebar and enter your PIN.")
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
            {"value": f"{total_volume:,.0f}", "label": "Total Volume (kg lifted)", "caption": "Logged load"},
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
            
            # Add custom workouts
            custom_workout_df = load_custom_workout_logs(spreadsheet, selected_user)
            if len(custom_workout_df) > 0:
                custom_workout_df["Date"] = pd.to_datetime(custom_workout_df["Date"], errors="coerce").dt.date
                for date in custom_workout_df["Date"].dropna().unique():
                    date_str = str(date)
                    if date_str not in calendar_data:
                        calendar_data[date_str] = "Custom"
            
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
                    elif activity == "Custom":
                        color = "#14b8a6"
                        label = "Custom"
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
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #14b8a6; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Custom Workout</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #a855f7; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Board Session</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #4ade80; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Climbing</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #fb923c; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Work Pullups</div>
                <div><span style='display: inline-block; width: 18px; height: 18px; background: #2d2d2d; border-radius: 3px; margin-right: 8px; vertical-align: middle;'></span>Rest</div>
            </div>
            """
            
            st.markdown(calendar_html + legend_html, unsafe_allow_html=True)
            
            gym_days = sum(1 for v in calendar_data.values() if v == "Gym")
            custom_days = sum(1 for v in calendar_data.values() if v == "Custom")
            board_days = sum(1 for v in calendar_data.values() if v == "Board")
            climb_days = sum(1 for v in calendar_data.values() if v == "Climbing")
            work_days = sum(1 for v in calendar_data.values() if v == "Work")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("🏋️ Gym Days (365d)", gym_days)
            with col2:
                st.metric("💪 Custom Days (365d)", custom_days)
            with col3:
                st.metric("🎯 Board Days (365d)", board_days)
            with col4:
                st.metric("🧗 Climbing Days (365d)", climb_days)
            with col5:
                st.metric("🏃 Work Days (365d)", work_days)

        st.markdown("---")
        
        # CURRENT STRENGTH (WORKING MAX)
        st.markdown("### 💪 Your Current Strength")
        st.caption("📊 Based on recent training performance (auto-updated from last 8 weeks)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            edge_L_kg = get_working_max(spreadsheet, selected_user, "20mm Edge", "L")
            edge_R_kg = get_working_max(spreadsheet, selected_user, "20mm Edge", "R")
            stored_edge_L_kg = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "L")
            stored_edge_R_kg = get_user_1rm(spreadsheet, selected_user, "20mm Edge", "R")
            
            if edge_L_kg > stored_edge_L_kg + 1:
                indicator_L = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{(edge_L_kg - stored_edge_L_kg):.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
                
            if edge_R_kg > stored_edge_R_kg + 1:
                indicator_R = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{(edge_R_kg - stored_edge_R_kg):.1f}kg from baseline</div>'
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
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{edge_L_kg:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.9); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>RIGHT</div>
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{edge_R_kg:.1f} kg</div>
                            {indicator_R}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            pinch_L_kg = get_working_max(spreadsheet, selected_user, "Pinch", "L")
            pinch_R_kg = get_working_max(spreadsheet, selected_user, "Pinch", "R")
            stored_pinch_L_kg = get_user_1rm(spreadsheet, selected_user, "Pinch", "L")
            stored_pinch_R_kg = get_user_1rm(spreadsheet, selected_user, "Pinch", "R")
            
            if pinch_L_kg > stored_pinch_L_kg + 1:
                indicator_L = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{(pinch_L_kg - stored_pinch_L_kg):.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
                
            if pinch_R_kg > stored_pinch_R_kg + 1:
                indicator_R = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{(pinch_R_kg - stored_pinch_R_kg):.1f}kg from baseline</div>'
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
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{pinch_L_kg:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.9); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>RIGHT</div>
                            <div style='font-size: 32px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{pinch_R_kg:.1f} kg</div>
                            {indicator_R}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            wrist_L_kg = get_working_max(spreadsheet, selected_user, "Wrist Roller", "L")
            wrist_R_kg = get_working_max(spreadsheet, selected_user, "Wrist Roller", "R")
            stored_wrist_L_kg = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "L")
            stored_wrist_R_kg = get_user_1rm(spreadsheet, selected_user, "Wrist Roller", "R")
            
            if wrist_L_kg > stored_wrist_L_kg + 1:
                indicator_L = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{(wrist_L_kg - stored_wrist_L_kg):.1f}kg from baseline</div>'
            else:
                indicator_L = '<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-top: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✓ From test</div>'
                
            if wrist_R_kg > stored_wrist_R_kg + 1:
                indicator_R = f'<div style="font-size: 11px; color: rgba(255,255,255,0.95); margin-top: 8px; background: rgba(74,222,128,0.35); padding: 6px 10px; border-radius: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">📈 +{(wrist_R_kg - stored_wrist_R_kg):.1f}kg from baseline</div>'
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
                            <div style='font-size: 32px; font-weight: 700; color: white;'>{wrist_L_kg:.1f} kg</div>
                            {indicator_L}
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;'>Right</div>
                            <div style='font-size: 32px; font-weight: 700; color: white;'>{wrist_R_kg:.1f} kg</div>
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
st.markdown("### 📖 Complete Guide - Everything You Need to Know")
st.caption("New to climbing or finger training? Start here! 🎯")

with st.expander("🎯 **EXERCISE TECHNIQUES - The Three Core Lifts**", expanded=False):
    st.markdown("""
    ### 🖐️ **20mm Edge Pickup (Half-Crimp Strength)**
    
    **What it trains:** Crimp grip strength for tiny edges and crimpy boulder problems.
    
    **Equipment needed:**
    - Portable hangboard edge (18-20mm depth)
    - Lifting pin with weight plates
    - Carabiner to attach edge to pin
    
    **How to perform:**
    1. Clip the edge to a lifting pin loaded with plates on the floor
    2. Stand so the device is under your armpit, arm along your body's front
    3. Grip the edge with a **half-crimp** (fingers bent at middle joint, thumb wrapped)
    4. Keep your shoulder packed down and back
    5. Brace your core, bend knees slightly
    6. **Lift by driving through your legs** - the arm just holds, legs do the work
    7. Lift weight off ground 2-3 inches, pause briefly
    8. Set it back down with control
    9. Reset your grip between each rep
    
    **Common mistakes:**
    - Pulling with arm instead of driving with legs → Keep arm close to body
    - Open grip instead of half-crimp → Fingers should be bent
    - Loose shoulder → Keep it packed and stable
    
    ---
    
    ### 🤏 **Pinch Block Pickup (Thumb Opposition Strength)**
    
    **What it trains:** Pinch grip for volumes, slopers, and pinch blocks.
    
    **Equipment needed:**
    - Pinch block (thick gripable block)
    - Lifting pin with weight plates
    - Carabiner to attach
    
    **How to perform:**
    1. Attach pinch block to lifting pin with plates
    2. Place **thumb on one side, fingers on the other**
    3. **Thumb positioning is key:** Deep along the side, not on top
    4. Fingers should be fairly straight (not crimped)
    5. Slightly pronate (rotate) your wrist inward so the block "cams" into your hand
    6. Stand over the pin, arm close to body
    7. Drive through legs to lift the weight
    8. Squeeze the block hard throughout the lift
    9. Set down, reset grip, repeat
    
    **Common mistakes:**
    - Thumb on top of block → Put it on the side for better leverage
    - Crimping fingers → Keep them straighter
    - Arm too far from body → Keep it close
    
    ---
    
    ### 💪 **Wrist Roller Pickup (Open-Hand & Wrist Strength)**
    
    **What it trains:** Open-hand grip for slopers, wrist stability, forearm endurance.
    
    **Equipment needed:**
    - Wrist roller handle OR thick dowel/pipe
    - Lifting pin with weight plates
    - Carabiner or rope
    
    **How to perform (NEW METHOD - Pickups, not rolling):**
    1. Connect the handle **directly to a short lifting pin** with plates
    2. Do NOT use a long rope for rolling - we're doing pickups!
    3. Stand with handle hanging near front of your thigh
    4. Grip the handle with **fingers wrapped around, thumb underneath and alongside fingers**
    5. **This is the key grip:** Thumb is not opposing - it's tucked next to your fingers on the underside
    6. Keep arm mostly straight, shoulder relaxed but stable
    7. Maintain an **open-hand grip** (not crimped, but fingers wrapped)
    8. Drive through legs to lift weight off ground
    9. Hold strong wrist position throughout
    10. Lower with control, reset, repeat
    
    **What this feels like:**
    - Like gripping a thick sloper or jug
    - Wrist stays neutral (not bent)
    - Forearms working hard to maintain grip
    - More "squeezing around" than "pinching"
    
    **Common mistakes:**
    - Trying to "roll" the weight → Just do pickups with the direct connection
    - Bending wrist excessively → Keep it neutral
    - Crimping fingers → Keep them more open/wrapped
    - Pulling with arm → Drive with legs
    
    **Why this exercise?**  
    Builds crushing strength for slopers, jugs, and any open-handed grip. Strengthens wrists for dynamic moves.
    """)

with st.expander("📝 **HOW TO LOG WORKOUTS - Step-by-Step**", expanded=False):
    st.markdown("""
    ### Standard Exercise Logging
    
    1. **Go to Log Workout page** (from sidebar or Quick Actions)
    2. **Select your exercise type:**
       - **Standard Exercises** → 20mm Edge, Pinch, or Wrist Roller
       - **Custom Workouts** → Your personalized templates
       - **Other Activities** → Climbing, Board sessions, Work pullups
       - **Update 1RM** → Test and log your maximum strength
    
    3. **For Standard Exercises:**
       - Click "Log Standard Workout" button
       - Select your exercise (20mm Edge, Pinch, or Wrist Roller)
       - Review your **last workout** and **AI suggestions**
       - The app shows recommended weight based on your last session
       - Enter the **actual weight you lifted** (in kg)
       - Choose if logging same weight for both arms or different
       - Enter **reps per set** (usually 3-5 for strength, 6+ for endurance)
       - Enter **sets completed** (usually 3-5)
       - Rate your **RPE** (1-10, how hard it felt)
       - Add notes (optional but recommended!)
       - Click "Log Workout" to save
    
    4. **For Custom Workouts:**
       - Click "Log Custom Workout"
       - Select from your saved templates
       - Fill in the metrics your template tracks (weight, reps, duration, etc.)
       - Add notes and submit
    
    5. **For Other Activities:**
       - Click "Log Activity"
       - Choose: Climbing, Board, or Work Pullups
       - Enter date and duration
       - Add session notes
       - Submit!
    
    6. **For 1RM Tests:**
       - Click "Update 1RM"
       - Select exercise to test
       - View your current 1RM
       - Enter your new maximum for left and right arm
       - Choose if you want to log it as a workout entry too
       - Submit to update your training targets
    
    ---
    
    ### Understanding the Smart Suggestions
    
    The app analyzes your last workout and suggests:
    - **Keep pushing** 💪 → Last session was good, try adding weight
    - **Increase load** 📈 → RPE was too easy, go heavier
    - **Same load** ⚖️ → Perfect difficulty, repeat the weight
    - **Reduce load** 📉 → RPE was too high, drop weight slightly
    - **First workout** 🎯 → Starting suggestion based on your 1RM
    
    These suggestions help you **progress safely** without overdoing it!
    """)

with st.expander("📊 **UNDERSTANDING YOUR STATS & DASHBOARD**", expanded=False):
    st.markdown("""
    ### Home Page Metrics Explained
    
    **Training Sessions**
    - Total number of unique days you've trained
    - Each day counts once, even if you log multiple exercises
    
    **Days Since Last**
    - How many days since your last logged workout
    - Helps you track consistency
    - App warns if you're inactive for 5+ days
    
    **Total Volume**
    - Sum of: Weight × Reps × Sets for all workouts
    - Measures total work done over time
    - Higher volume = more training stimulus
    
    **Average RPE**
    - Your average effort level across recent workouts
    - If consistently high (9-10): You might be overdoing it
    - If consistently low (5-6): You can probably push harder
    - Ideal range: 7-8 for most sessions
    
    **This Week Sessions**
    - Number of training days in current week (Monday-Sunday)
    - Target: 3-6 sessions per week for best results
    
    ---
    
    ### Current Strength (Working Max)
    
    The app shows your **current estimated strength** for each exercise:
    
    - **From test** ✓ → Based on your last 1RM test
    - **+X kg from baseline** 📈 → You're getting stronger! Your recent training suggests you can lift more than your last test
    
    **How it works:**
    - App tracks your last 8 weeks of training
    - Uses the Epley formula to estimate your true max
    - If you're consistently lifting heavier weights for reps, it estimates you're stronger
    - When you see "+X kg", consider doing a new 1RM test to confirm!
    
    **Left vs Right Arm:**
    - Tracks each arm independently
    - Helps identify imbalances
    - Train both equally to prevent injury
    
    ---
    
    ### Training Calendar
    
    **Color coding:**
    - 🟣 **Purple** = Gym (Standard finger training)
    - 🟢 **Teal** = Custom Workout
    - 💜 **Purple** = Board Session (Kilter, etc.)
    - 🟢 **Green** = Outdoor Climbing
    - 🟠 **Orange** = Work Pullups
    - ⬛ **Gray** = Rest Day
    
    **How to use it:**
    - Quickly visualize your training frequency
    - Spot gaps in your schedule
    - See your consistency over 365 days
    - Aim for 3-6 colored squares per week
    """)

with st.expander("⚙️ **SETTINGS & ADVANCED FEATURES**", expanded=False):
    st.markdown("""
    ### Profile Page Settings
    
    **Bodyweight Tracking**
    - Update your weight in the sidebar or Profile page
    - Used to calculate relative strength ratios
    - Helps track if you're gaining/losing weight
    
    **Creating New Users**
    - Share the tracker with your climbing crew!
    - Each user has their own:
      - Training history
      - Strength stats
      - Custom workouts
      - PIN for privacy
    
    **PIN Security**
    - Each user can set a 4-digit PIN
    - Required to access your profile
    - Prevents accidental data mixing
    - Change it anytime in Profile settings
    
    ---
    
    ### Endurance Training Mode (3rd Session Toggle)
    
    **What is it?**  
    A special training protocol for sport climbing endurance, automatically activated every 3rd workout for each exercise.
    
    **How to enable:**
    1. Go to **Profile** page
    2. Find "Endurance Training" section
    3. Toggle ON for exercises you want endurance training
    4. Choose which exercises (20mm Edge, Pinch, Wrist Roller)
    
    **When enabled:**
    - Every 3rd session becomes an **endurance workout**
    - Automatically sets **55% of your 1RM** (lighter weight)
    - Default: **6 hangs × 3 sets**
    - Protocol: **7 seconds on, 3 seconds off** (repeaters)
    - You'll see a green banner: "ENDURANCE SESSION - REPEATERS"
    
    **Example sequence:**
    - Session 1: Strength (80% 1RM, 5 reps, 3 sets)
    - Session 2: Strength (80% 1RM, 5 reps, 3 sets)
    - Session 3: **Endurance** (55% 1RM, 6 hangs, 3 sets) ← Automatic!
    - Session 4: Strength (back to normal)
    - Session 5: Strength
    - Session 6: **Endurance** (every 3rd)
    
    **Why use it?**
    - Builds **local endurance** in fingers
    - Prepares you for long sport routes
    - Prevents plateau from only doing heavy strength work
    - Balances power and endurance
    
    **Who should use it?**
    - Sport climbers training for multi-pitch or endurance routes
    - Anyone plateauing on pure strength training
    - People transitioning to longer climbing sessions
    
    **Who shouldn't use it?**
    - Pure boulderers focused only on max strength
    - Beginners (first 3-6 months, focus on strength)
    - During a strength-building phase
    
    ---
    
    ### Custom Workouts
    
    **Creating Templates:**
    1. Go to **Custom Workouts** page
    2. Click "Create New Workout"
    3. Name your workout
    4. Choose workout type (Strength, Cardio, Flexibility, etc.)
    5. Select what to track:
       - ✅ Weight (if using loads)
       - ✅ Sets & Reps
       - ✅ Duration (for timed exercises)
       - ✅ Distance (for cardio)
       - ✅ RPE (always recommended)
    6. Add description
    7. Save template
    
    **Logging Custom Workouts:**
    - Go to Log Workout → Custom Workouts
    - Select your saved template
    - Fill in only the metrics you chose to track
    - Much faster than standard logging for specialized exercises
    
    **Example custom workouts:**
    - Campus board progressions
    - System wall power endurance
    - Hangboard max hangs
    - Core strength circuits
    - Flexibility/yoga sessions
    - Cardio (running, cycling)
    """)

with st.expander("📈 **PROGRESS TRACKING & ANALYSIS**", expanded=False):
    st.markdown("""
    ### Progress Page - What You'll See
    
    **Load Over Time Charts**
    - Line graphs showing weight lifted per exercise
    - Separate charts for left and right arm
    - Helps visualize strength gains
    - Look for upward trends!
    
    **RPE Trends**
    - Track if workouts are getting easier/harder
    - Flat RPE with increasing weight = getting stronger! 💪
    - Rising RPE = possible overtraining, consider deload
    
    **Recent Workouts Table**
    - Last 20 workouts with all details
    - Filter by exercise, arm, date range
    - Export data if needed
    
    **Summary Statistics**
    - Personal records (heaviest lifts)
    - Average load per exercise
    - Training frequency per exercise
    - Consistency metrics
    
    ---
    
    ### Goals Page - Training Plans
    
    **Weekly Schedule**
    - Suggested training split
    - Exercise rotation recommendations
    - Rest day guidance
    - Based on your training history
    
    **Technique Reminders**
    - Exercise-specific cues for each lift
    - Common mistakes to avoid
    - Form check reminders
    
    **Streak Tracking**
    - Current training streak (consecutive days/weeks)
    - Longest streak achieved
    - Motivation to stay consistent!
    """)

with st.expander("🏆 **LEADERBOARD & COMPETITION**", expanded=False):
    st.markdown("""
    ### Compete With Your Crew!
    
    **Rankings Available:**
    
    1. **Absolute Strength Rankings**
       - Who lifts the most weight (kg) per exercise
       - Separated by arm (L/R)
       - Updated in real-time
    
    2. **Relative Strength Rankings**
       - Weight lifted ÷ bodyweight
       - More fair comparison across different body sizes
       - Shows true strength-to-weight ratio
    
    3. **Volume Rankings**
       - Total kg lifted over time period
       - Measures work capacity and consistency
       - Rewards those who train hard and often
    
    4. **Arm Balance Score**
       - Measures left vs right arm strength difference
       - Closer to 100% = better balance
       - Important for injury prevention
    
    **How to Use It:**
    - Friendly competition motivates training!
    - Don't compare yourself too harshly to others
    - Focus on beating your own PRs first
    - Use it to find training partners at similar levels
    """)

with st.expander("💡 **PRO TIPS & BEST PRACTICES**", expanded=False):
    st.markdown("""
    ### Training Frequency
    - **Beginners:** 2-3 sessions/week
    - **Intermediate:** 3-4 sessions/week  
    - **Advanced:** 4-6 sessions/week
    - Always include 1-2 full rest days per week
    
    ### Progressive Overload
    - Aim to increase weight by **2.5-5kg every 2-3 weeks**
    - Don't rush! Fingers adapt slowly (6-8 weeks per adaptation)
    - If you can't add weight, add reps or sets
    - Deload (reduce weight 20%) every 4-6 weeks
    
    ### RPE Guidelines
    - **Strength training:** Target RPE 7-8
    - **Endurance training:** Target RPE 6-7
    - **Testing 1RM:** RPE 10 (max effort)
    - **Recovery sessions:** RPE 5-6
    
    ### When to Test 1RM
    - Every 3-4 weeks for beginners
    - Every 4-6 weeks for intermediate
    - Every 6-8 weeks for advanced
    - After taking a week off
    - When app shows +5kg+ estimated increase
    
    ### Injury Prevention
    - Always warm up (10 min light cardio + finger warm-up)
    - Don't train through finger pain
    - Watch for imbalances (>10% difference = address it)
    - Take rest days seriously
    - If RPE is consistently 9-10, you need rest
    
    ### Nutrition & Recovery
    - Get adequate protein (1.6-2.2g/kg bodyweight)
    - Sleep 7-9 hours per night
    - Stay hydrated during training
    - Consider collagen supplementation for finger health
    
    ### Climbing Integration
    - Don't finger train day before projecting
    - Can do light finger training after easy climbing
    - Heavy finger training requires 48h recovery
    - Reduce finger training volume during climbing trips
    """)

with st.expander("❓ **FAQ - Common Questions**", expanded=False):
    st.markdown("""
    **Q: I'm brand new to climbing. Can I start finger training?**  
    A: Wait at least 6-12 months of regular climbing first. Build base strength in your fingers through actual climbing before adding weighted training. Your tendons need time to adapt!
    
    **Q: What is RPE?**  
    A: Rate of Perceived Exertion - how hard the set felt on a scale of 1-10:
    - 5 = Very easy, could do many more reps
    - 7 = Could do 3 more reps  
    - 8 = Could do 2 more reps
    - 9 = Could do 1 more rep  
    - 10 = Absolute maximum, couldn't do another rep
    
    **Q: How does the strength calculation work?**  
    A: Uses the Epley Formula: 1RM = weight × (1 + reps/30). Analyzes your last 8 weeks of training to estimate current max strength. More accurate than guessing!
    
    **Q: What if I can't hit the prescribed weight?**  
    A: Totally fine! Enter what you actually lifted. The app learns from this and adjusts future suggestions. Never force a weight that feels unsafe.
    
    **Q: Should I train both arms equally?**  
    A: YES! Even if you climb one-handed moves, train both equally to:
    - Prevent muscle imbalances
    - Reduce injury risk
    - Maintain body symmetry
    - Be prepared for any route
    
    **Q: My right arm is way stronger. What do I do?**  
    A: Common issue! Solutions:
    - Do extra sets with weaker arm
    - Start each session with weaker arm
    - Use slightly heavier weight for weaker arm
    - Don't let strong arm dominate
    - Be patient - takes months to balance
    
    **Q: Can I train fingers every day?**  
    A: NO! Fingers need 48h recovery minimum. Tendons are slow to heal. Overtraining = injury. Stick to 3-6 sessions per week with rest days.
    
    **Q: What's better - heavy weight/low reps or light weight/high reps?**  
    A: Both! 
    - Heavy (80%+ 1RM, 3-5 reps) = max strength
    - Light (50-60% 1RM, 6-10 reps) = endurance
    - Train both with the 3rd session toggle!
    
    **Q: The app says I should add weight but I don't feel ready.**  
    A: Trust your body over the app! Suggestions are guidelines. If something feels wrong, don't do it. Log a lighter weight and the app will adjust.
    
    **Q: How long until I see progress?**  
    A: Initial gains: 2-4 weeks (neural adaptation)
    Real strength: 6-8 weeks (tissue adaptation)
    Significant gains: 12-16 weeks (consistent training)
    Be patient! Fingers adapt slowly.
    
    **Q: Can I do finger training and project hard the same day?**  
    A: Not recommended. Either:
    - Finger train → 48h rest → project
    - Easy climbing → finger train same day
    - Heavy climbing → skip finger training that day
    
    **Q: What if I miss a week of training?**  
    A: No big deal! Life happens. When returning:
    - Reduce weight by 10-15%
    - Work back up over 2-3 sessions
    - Don't jump straight to previous weights
    - Your strength drops slower than you think!
    
    **Q: Should I feel sore after finger training?**  
    A: Mild forearm soreness is normal. Finger joint pain is NOT normal:
    - ✅ Forearm muscle fatigue = good
    - ✅ Mild finger pump = normal
    - ❌ Sharp finger pain = stop immediately
    - ❌ Persistent joint pain = see doctor
    - ❌ Swollen fingers = overtraining
    
    **Q: Can multiple people use this tracker?**  
    A: Absolutely! Go to Profile → Create New User. Each person gets:
    - Separate training history
    - Personal stats
    - Custom PIN
    - Individual settings
    Perfect for sharing with climbing partners or gym!
    """)

with st.expander("🚨 **INJURY PREVENTION & SAFETY**", expanded=False):
    st.markdown("""
    ### Warning Signs - STOP Training If:
    - Sharp, acute pain in fingers or elbows
    - Swelling in finger joints
    - Numbness or tingling
    - Pain that doesn't go away after warm-up
    - Pain that wakes you up at night
    - Weakness in grip that persists days after training
    
    ### Common Finger Injuries
    
    **A2 Pulley Strain** (most common)
    - Location: Base of finger, palm side
    - Feels like: Sharp pain when crimping
    - Cause: Too much volume, too heavy weight, insufficient warm-up
    - Prevention: Gradual progression, proper technique, adequate rest
    
    **Flexor Tendon Strain**
    - Location: Forearm into fingers
    - Feels like: Dull ache along tendon path
    - Cause: Overuse, inadequate recovery
    - Prevention: Listen to your body, take rest days
    
    **Collateral Ligament Sprain**
    - Location: Sides of finger joints
    - Feels like: Pain when moving finger sideways
    - Cause: Awkward hand positions, overstressing
    - Prevention: Controlled movements, good form
    
    ### If You Get Injured
    1. **STOP immediately** - don't "push through"
    2. **Rest** - minimum 48h, possibly weeks
    3. **Ice** - 15-20 min several times daily
    4. **Elevate** - reduce swelling
    5. **See a doctor** - especially if severe or persistent
    6. **Gradual return** - start at 50% previous weight
    7. **Listen to your body** - pain = stop
    
    ### Warm-Up Protocol (NEVER SKIP!)
    1. **General warm-up** (5-10 min)
       - Light cardio (jump rope, jog, bike)
       - Get heart rate up, break light sweat
    
    2. **Specific warm-up** (5-10 min)
       - Wrist circles (20 each direction)
       - Finger flexion/extension (20 reps)
       - Gentle finger pulls (all fingers)
       - Light grip squeezes with stress ball
       - Arm circles and shoulder rolls
    
    3. **Exercise-specific warm-up** (2-3 sets)
       - Start with 40% of working weight
       - Then 60% of working weight
       - Then 80% of working weight
       - Full rest between warm-up sets
       - Now ready for working sets!
    
    ### Cool-Down & Recovery
    - Light cardio (5 min) to flush metabolites
    - Gentle stretching (NOT aggressive!)
    - Finger massage and mobility work
    - Ice fingers if feeling tweaky
    - Protein within 2h post-workout
    - Sleep well!
    """)

with st.expander("🎓 **Getting Started Checklist**", expanded=False):
    st.markdown("""
    ### Your First Week
    
    #### Day 1: Setup & First Test
    - [ ] Create your profile
    - [ ] Set your bodyweight
    - [ ] Set your PIN
    - [ ] Do proper warm-up
    - [ ] Test your 1RM on one exercise (start with 20mm Edge)
    - [ ] Log the test (Update 1RM page)
    
    #### Day 3: First Training Session
    - [ ] Warm up properly
    - [ ] Log Workout → Standard Exercise
    - [ ] Select 20mm Edge
    - [ ] Use 80% of your 1RM
    - [ ] Do 5 reps × 3 sets
    - [ ] Rate your RPE honestly
    - [ ] Add notes about how it felt
    
    #### Day 5: Second Exercise
    - [ ] Repeat process for Pinch or Wrist Roller
    - [ ] Follow app's weight suggestions
    - [ ] Focus on perfect technique
    - [ ] Don't go too heavy!
    
    #### Day 7: Recovery & Review
    - [ ] Full rest day (no finger training)
    - [ ] Check Progress page
    - [ ] Review your first week
    - [ ] Plan next week's schedule
    
    ### Your First Month Goals
    - [ ] Establish consistent training schedule (3-4x/week)
    - [ ] Test 1RM on all three exercises
    - [ ] Learn proper technique for each lift
    - [ ] Build the habit of logging every workout
    - [ ] Start tracking your calendar consistently
    - [ ] Join the leaderboard competition
    - [ ] Stay injury-free!
    
    ### When You're Ready to Level Up
    - [ ] Enable endurance training toggle (after 2-3 months)
    - [ ] Create custom workout templates
    - [ ] Log climbing and board sessions
    - [ ] Set specific strength goals
    - [ ] Train with friends using the tracker
    - [ ] Analyze your progress trends
    - [ ] Compete on the leaderboard
    
    ### Remember
    ✅ **Consistency beats intensity**  
    ✅ **Technique beats weight**  
    ✅ **Recovery is part of training**  
    ✅ **Progress takes time (months, not weeks)**  
    ✅ **Pain is a signal to stop, not push through**  
    ✅ **Every workout logged is a win**  
    
    🎯 **You've got this! Start today, log consistently, watch yourself get stronger!** 💪
    """)

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 14px; padding: 20px;'>
        💪 Built for climbers, by climbers | Keep crushing it! 🧗
    </div>
""", unsafe_allow_html=True)
