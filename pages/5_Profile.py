import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import (
    init_session_state,
    get_google_sheet,
    load_users_from_sheets,
    load_data_from_sheets,
    get_bodyweight,      # Add these 4 functions
    set_bodyweight,
    get_user_1rms,
    add_new_user,
    USER_LIST
)

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

init_session_state()

# ==================== HEADER ====================
st.markdown(
    """
    <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    padding: 30px 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(102,126,234,0.4);'>
        <h1 style='color: white; font-size: 42px; margin: 0;'>👤 Your Profile</h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 8px;'>
            Track your journey, analyze your strength, dominate your training
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
    key="user_selector_profile"
)

selected_user = st.session_state.current_user

if workout_sheet:
    # Load data
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    # ==================== PERSONAL STATS OVERVIEW ====================
    st.markdown(f"## 💪 {selected_user}'s Training Profile")
    
    if len(df) > 0:
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Calculate stats
        total_sessions = len(df['Date'].dt.date.unique())
        total_reps = (pd.to_numeric(df['Reps_Per_Set'], errors='coerce') * 
                     pd.to_numeric(df['Sets_Completed'], errors='coerce')).sum()
        total_volume = (pd.to_numeric(df['Actual_Load_kg'], errors='coerce') * 
                       pd.to_numeric(df['Reps_Per_Set'], errors='coerce') * 
                       pd.to_numeric(df['Sets_Completed'], errors='coerce')).sum()
        
        # Training streak
        dates = sorted(df['Date'].dt.date.unique())
        current_streak = 1
        for i in range(len(dates)-1, 0, -1):
            if (dates[i] - dates[i-1]).days <= 3:  # 3 days tolerance
                current_streak += 1
            else:
                break
        
        # Days since start
        days_training = (datetime.now() - df['Date'].min()).days
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(79,172,254,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Total Sessions</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{total_sessions}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.7); margin-top: 5px;'>workouts logged</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(240,147,251,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Training Streak</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{current_streak}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.7); margin-top: 5px;'>consecutive sessions</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(250,112,154,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Total Volume</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{total_volume:,.0f}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.7); margin-top: 5px;'>kg lifted</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(48,207,208,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Training Days</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{days_training}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.7); margin-top: 5px;'>days since start</div>
                </div>
            """, unsafe_allow_html=True)
    
        st.markdown("---")
    
    # ==================== BODYWEIGHT ====================
    st.markdown("### ⚖️ Bodyweight")
    
    current_bw = get_bodyweight(spreadsheet, selected_user) if spreadsheet else 78.0
    
    # Display current bodyweight
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 15px 20px; border-radius: 10px; margin-bottom: 15px; text-align: center;'>
            <div style='font-size: 14px; color: rgba(255,255,255,0.8);'>Current Bodyweight</div>
            <div style='font-size: 32px; font-weight: bold; color: white;'>{current_bw} kg</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption("Your bodyweight is used to calculate relative strength metrics.")
    
    col_bw1, col_bw2 = st.columns([3, 1])
    
    with col_bw1:
        new_bw = st.number_input(
            "Update Bodyweight (kg):",
            min_value=40.0,
            max_value=150.0,
            value=current_bw,
            step=0.5,
            key="bodyweight_input"
        )
    
    with col_bw2:
        if st.button("⚖️ Update Bodyweight", use_container_width=True):
            if new_bw != current_bw and spreadsheet:
                set_bodyweight(spreadsheet, selected_user, new_bw)
                st.success(f"✅ Updated to {new_bw}kg")
                st.rerun()

    
    # ==================== CURRENT 1RMs WITH STRENGTH CHART ====================
    st.markdown("### 💪 Current 1RMs")
    
    col1, col2, col3 = st.columns(3)
    
    exercises_display = ["20mm Edge", "Pinch", "Wrist Roller"]
    colors = [
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
    ]
    
    # Store 1RMs for chart
    left_vals = []
    right_vals = []
    
    for idx, (col, exercise, color) in enumerate(zip([col1, col2, col3], exercises_display, colors)):
        with col:
            val_L = get_user_1rms(spreadsheet, selected_user, exercise, "L")  # Fixed function name
            val_R = get_user_1rms(spreadsheet, selected_user, exercise, "R")  # Fixed function name
            
            left_vals.append(val_L)
            right_vals.append(val_R)
            
            st.markdown(f"""
                <div style='background: {color}; 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
                    <h4 style='margin: 0 0 15px 0; color: white; text-align: center;'>{exercise}</h4>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.8);'>👈 Left</div>
                            <div style='font-size: 28px; font-weight: bold; color: white;'>{val_L} kg</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 12px; color: rgba(255,255,255,0.8);'>👉 Right</div>
                            <div style='font-size: 28px; font-weight: bold; color: white;'>{val_R} kg</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.caption("💡 1RMs are automatically updated when you log 1RM tests")
    
    # Strength balance chart
    st.markdown("---")
    st.markdown("### 📊 Strength Balance Analysis")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=exercises_display,
        y=left_vals,
        name='Left Arm',
        marker_color='#4facfe',
        text=left_vals,
        textposition='auto',
        texttemplate='%{text} kg'
    ))
    
    fig.add_trace(go.Bar(
        x=exercises_display,
        y=right_vals,
        name='Right Arm',
        marker_color='#f093fb',
        text=right_vals,
        textposition='auto',
        texttemplate='%{text} kg'
    ))
    
    fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=14),
        xaxis=dict(
            showgrid=False,
            title='Exercise',
            title_font=dict(size=16, color='white')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            title='1RM (kg)',
            title_font=dict(size=16, color='white')
        ),
        height=400,
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Balance analysis
    imbalances = []
    for idx, exercise in enumerate(exercises_display):
        diff = abs(left_vals[idx] - right_vals[idx])
        pct_diff = (diff / max(left_vals[idx], right_vals[idx])) * 100
        if pct_diff > 10:
            stronger = "Left" if left_vals[idx] > right_vals[idx] else "Right"
            imbalances.append(f"**{exercise}**: {stronger} arm is {pct_diff:.1f}% stronger ({diff:.1f} kg difference)")
    
    if imbalances:
        st.warning("⚠️ **Strength Imbalances Detected:**\n\n" + "\n\n".join(imbalances))
        st.caption("💡 Consider focusing on your weaker arm to prevent injury and improve overall performance")
    else:
        st.success("✅ **Excellent balance!** Your left and right arm strength are well-matched")
    
    st.markdown("---")
    
   # ==================== CREATE NEW USER ====================
st.markdown("### ➕ Create New User")

col_user1, col_user2, col_user3 = st.columns([2, 2, 1])

with col_user1:
    new_username = st.text_input("Username:", placeholder="Enter new username", key="new_user_input")

with col_user2:
    initial_bw = st.number_input("Initial Bodyweight (kg):", min_value=40.0, max_value=150.0, value=78.0, step=0.5, key="new_user_bw")

with col_user3:
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    if st.button("Create User", use_container_width=True):
        if new_username and new_username.strip() != "":
            if not spreadsheet:
                st.error("❌ Could not connect to Google Sheets.")
            else:
                cleaned_username = new_username.strip()
                
                # Get current users to prevent duplicates
                current_users = load_users_from_sheets(spreadsheet)
                if cleaned_username in current_users:
                    st.error(f"❌ User '{cleaned_username}' already exists!")
                else:
                    ok, msg = add_new_user(spreadsheet, cleaned_username, initial_bw)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.success(f"🎉 Welcome **{cleaned_username}**! Initial bodyweight set to **{initial_bw} kg**")
                        st.balloons()
                        st.info("🔄 Refreshing to load new user...")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        else:
            st.error("❌ Please enter a username!")

