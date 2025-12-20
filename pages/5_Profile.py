import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import (
    init_session_state, load_users_from_sheets,
    load_user_pins_from_sheets,
    user_selectbox_with_pin,
    load_data_from_sheets,
    get_bodyweight,
    set_bodyweight,
    get_user_1rm,
    get_working_max,
    add_new_user,
    delete_user,
    USER_LIST,
    PIN_LENGTH,
    USER_PLACEHOLDER,
    inject_global_styles,
    generate_instagram_story,
    get_endurance_training_enabled,
    set_endurance_training_enabled,
    get_workout_count,
    change_user_pin,
)

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

init_session_state()
inject_global_styles()



# Load users
available_users = load_users_from_sheets()
user_pins = load_user_pins_from_sheets()

# User selector in sidebar
st.sidebar.header("👤 User")
selected_user = user_selectbox_with_pin(
    available_users,
    user_pins,
    selector_key="user_selector_profile",
    label="Select User:"
)
st.session_state.current_user = selected_user

# ==================== SETTINGS DIALOG ====================
@st.dialog("⚙️ Training Settings", width="large")
def show_settings_dialog(selected_user):
    """Modal dialog for training settings"""
    
    # Tabs for different setting categories
    tab1, tab2 = st.tabs(["🏃 Training", "🔒 Security"])
    
    # ==================== TRAINING TAB ====================
    with tab1:
        st.markdown("### 🏃 Endurance Training")
        
        current_endurance_enabled = get_endurance_training_enabled(selected_user)
        workout_count_edge = get_workout_count(selected_user, "20mm Edge")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); margin-bottom: 16px;'>
                    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 10px;'>
                        <div style='font-size: 28px;'>🏃</div>
                        <div>
                            <div style='font-size: 18px; color: white; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.3);'>Repeaters Protocol</div>
                            <div style='font-size: 13px; color: rgba(255,255,255,0.9); text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>
                                Every 3rd edge workout focuses on endurance
                            </div>
                        </div>
                    </div>
                    <div style='background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px;'>
                        <div style='font-size: 12px; color: rgba(255,255,255,0.85); line-height: 1.5; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>
                            📊 <strong>Endurance (Repeaters):</strong> 55% max, 7s on/3s off, 6 hangs<br>
                            💪 <strong>Strength workouts:</strong> 80% max load, 5 reps (normal)
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            endurance_enabled = st.toggle(
                "Enable endurance training for 20mm Edge workouts",
                value=current_endurance_enabled,
                key="endurance_training_toggle",
                help="When enabled, every third edge workout will be a repeaters endurance session"
            )
            
            if endurance_enabled != current_endurance_enabled:
                set_endurance_training_enabled(selected_user, endurance_enabled)
                st.success(f"✅ Endurance training {'enabled' if endurance_enabled else 'disabled'}!")
        
        with col2:
            if endurance_enabled:
                cycle_position = workout_count_edge + 1
                next_workout_type = "Endurance 🏃" if workout_count_edge == 2 else f"Strength 💪"
                
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); 
                    padding: 24px 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(99,102,241,0.4);
                    display: flex; flex-direction: column; justify-content: center; min-height: 180px;'>
                        <div style='font-size: 13px; color: rgba(255,255,255,0.9); margin-bottom: 8px; text-shadow: 0 1px 2px rgba(0,0,0,0.3); text-transform: uppercase; letter-spacing: 1px;'>
                            Current Cycle
                        </div>
                        <div style='font-size: 48px; margin-bottom: 8px;'>
                            {'🏃' if workout_count_edge == 2 else '💪'}
                        </div>
                        <div style='font-size: 24px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 4px;'>
                            Workout {cycle_position}/3
                        </div>
                        <div style='font-size: 13px; color: rgba(255,255,255,0.85); text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>
                            Next: {next_workout_type}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='background: rgba(255,255,255,0.05); 
                    padding: 24px 20px; border-radius: 12px; text-align: center;
                    display: flex; flex-direction: column; justify-content: center; min-height: 180px;'>
                        <div style='font-size: 48px; margin-bottom: 12px;'>😴</div>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.6);'>
                            Endurance mode disabled
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    # ==================== SECURITY TAB ====================
    with tab2:
        st.markdown("### 🔒 Change PIN")
        
        st.markdown("""
            <div style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
            padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(239,68,68,0.4); margin-bottom: 16px;'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 10px;'>
                    <div style='font-size: 28px;'>🔒</div>
                    <div>
                        <div style='font-size: 18px; color: white; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.3);'>Security Settings</div>
                        <div style='font-size: 13px; color: rgba(255,255,255,0.9); text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>
                            Update your 4-digit PIN code
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("change_pin_form"):
            st.markdown("#### Enter PIN Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                old_pin = st.text_input("Current PIN", type="password", max_chars=4, key="old_pin_input")
            
            with col2:
                new_pin = st.text_input("New PIN (4 digits)", type="password", max_chars=4, key="new_pin_input")
            
            new_pin_confirm = st.text_input("Confirm New PIN", type="password", max_chars=4, key="new_pin_confirm")
            
            submit_pin = st.form_submit_button("🔒 Change PIN", use_container_width=True, type="primary")
            
            if submit_pin:
                if not old_pin or not new_pin or not new_pin_confirm:
                    st.error("❌ Please fill in all fields")
                elif new_pin != new_pin_confirm:
                    st.error("❌ New PINs don't match")
                elif len(new_pin) != 4 or not new_pin.isdigit():
                    st.error("❌ New PIN must be exactly 4 digits")
                elif old_pin == new_pin:
                    st.error("❌ New PIN must be different from current PIN")
                else:
                    success, message = change_user_pin(selected_user, old_pin, new_pin)
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
        
        st.warning("⚠️ Remember your PIN! You'll need it to access your profile.")

# ==================== HEADER WITH SETTINGS BUTTON ====================
header_col1, header_col2 = st.columns([6, 1])

with header_col1:
    st.markdown(
        """
        <div class='page-header' style='background: linear-gradient(135deg, #5651e5 0%, #6b3fa0 100%); 
        padding: 32px 24px; border-radius: 20px; box-shadow: 0 15px 40px rgba(102,126,234,0.5);
        border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
            <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>👤 Your Profile</h1>
            <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
                Track your journey, analyze your strength, dominate your training
            </p>
        </div>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    if selected_user == USER_PLACEHOLDER:
        if st.button("⚙️", use_container_width=True, help="Login to access settings", key="settings_btn", disabled=True):
            pass
    else:
        if st.button("⚙️", use_container_width=True, help="Training Settings", key="settings_btn"):
            show_settings_dialog(selected_user)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# Allow create new user even when locked
if selected_user == USER_PLACEHOLDER:
    st.markdown("## 🆕 Create Your Profile")
    st.info("👋 Welcome! Create a new profile to start tracking your training.")
    
    st.markdown("### ➥ Create New User")
    st.caption("Pins are stored in the `Users` sheet (column `PIN` next to `Username`). Keep them private!")

    col_user1, col_user2, col_user3, col_user4 = st.columns([2, 1.5, 1.2, 1])

    with col_user1:
        new_username = st.text_input("Username:", placeholder="Enter new username", key="new_user_input")

    with col_user2:
        initial_bw = st.number_input("Initial Bodyweight (kg):", min_value=40.0, max_value=150.0, value=78.0, step=0.5, key="new_user_bw")

    with col_user3:
        new_user_pin = st.text_input(f"4-digit PIN:", max_chars=PIN_LENGTH, type="password", key="new_user_pin")

    with col_user4:
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
        if st.button("Create User", use_container_width=True):
            if not new_username or new_username.strip() == "":
                st.error("❌ Please enter a username!")
            elif not new_user_pin or len(new_user_pin) != PIN_LENGTH or not new_user_pin.isdigit():
                st.error("❌ PIN must be exactly 4 digits.")
            else:
                cleaned_username = new_username.strip()
                
                # Get current users to prevent duplicates
                current_users = load_users_from_sheets()
                if cleaned_username in current_users:
                    st.error(f"❌ User '{cleaned_username}' already exists!")
                else:
                        ok, msg = add_new_user(cleaned_username, initial_bw, pin=new_user_pin)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.success(f"🎉 Welcome **{cleaned_username}**! Bodyweight **{initial_bw} kg**, PIN saved securely.")
                            st.balloons()
                            st.info("🔄 Profile created! Now select your profile from the sidebar and enter your PIN to log in.")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
    
    st.stop()

# All data comes from Supabase now
if True:
    # Load data
    df = load_data_from_sheets(None, user=selected_user)
    
    # ==================== PERSONAL STATS OVERVIEW ====================
    st.markdown(f"## 💪 {selected_user}'s Training Profile")
    
    if len(df) > 0:
        # Filter out 1RM tests
        df = df[~df['Exercise'].str.contains('1RM Test', na=False)]
        
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
                <div style='background: linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(79,172,254,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Total Sessions</div>
                    <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{total_sessions}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>workouts logged</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #d946b5 0%, #e23670 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(240,147,251,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Training Streak</div>
                    <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{current_streak}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>consecutive sessions</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #e1306c 0%, #f77737 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(250,112,154,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Total Volume</div>
                    <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{total_volume:,.0f}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>kg lifted</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(48,207,208,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Training Days</div>
                    <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{days_training}</div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>days since start</div>
                </div>
            """, unsafe_allow_html=True)
    
        st.markdown("---")
    
    # ==================== BODYWEIGHT ====================
    st.markdown("### ⚖️ Bodyweight")
    
    current_bw = get_bodyweight(selected_user)
    
    # Display current bodyweight
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #5651e5 0%, #6b3fa0 100%); 
        padding: 15px 20px; border-radius: 10px; margin-bottom: 15px; text-align: center;'>
            <div style='font-size: 14px; color: rgba(255,255,255,0.9); text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Current Bodyweight</div>
            <div style='font-size: 32px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{current_bw:.1f} kg</div>
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
            if new_bw != current_bw:
                set_bodyweight(selected_user, new_bw)
                st.success(f"✅ Updated to {new_bw:.1f}kg")
                st.rerun()
    
    # Bodyweight history chart
    from utils.helpers import get_bodyweight_history
    bw_history = get_bodyweight_history(selected_user)
    
    if not bw_history.empty and len(bw_history) > 1:
        st.markdown("#### 📊 Bodyweight History")
        
        fig_bw = go.Figure()
        
        fig_bw.add_trace(go.Scatter(
            x=bw_history['Date'],
            y=bw_history['Bodyweight_kg'],
            mode='lines+markers',
            name='Bodyweight',
            line=dict(color='#fbbf24', width=3),
            marker=dict(size=10, color='#fbbf24', line=dict(color='white', width=2)),
            fill='tozeroy',
            fillcolor='rgba(251, 191, 36, 0.2)'
        ))
        
        fig_bw.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=14),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='Date',
                title_font=dict(size=14, color='white')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='Bodyweight (kg)',
                title_font=dict(size=14, color='white')
            ),
            height=300,
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig_bw, use_container_width=True)
        
        # Show bodyweight stats
        bw_change = bw_history['Bodyweight_kg'].iloc[-1] - bw_history['Bodyweight_kg'].iloc[0]
        bw_change_pct = (bw_change / bw_history['Bodyweight_kg'].iloc[0]) * 100
        
        if abs(bw_change) > 0.5:
            change_emoji = "📊"
            change_text = "lost" if bw_change < 0 else "gained"
            
            st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 8px; margin-top: 10px;'>
                    <div style='color: #9ca3af; font-size: 14px;'>
                        {change_emoji} You've {change_text} <strong>{abs(bw_change):.1f} kg</strong> ({abs(bw_change_pct):.1f}%) since your first logged bodyweight
                    </div>
                </div>
            """, unsafe_allow_html=True)

    
    st.markdown("---")
    
    # ==================== CURRENT 1RMs WITH STRENGTH CHART ====================
    st.markdown("### 💪 Strength Profile")
    
    col1, col2, col3 = st.columns(3)
    
    exercises_display = ["20mm Edge", "Pinch", "Wrist Roller"]
    colors = [
        "linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%)",
        "linear-gradient(135deg, #e1306c 0%, #f77737 100%)",
        "linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
    ]
    
    # Store 1RMs for chart
    left_vals = []
    right_vals = []
    
    for idx, (col, exercise, color) in enumerate(zip([col1, col2, col3], exercises_display, colors)):
        with col:
            # Get stored 1RM (last recorded)
            recorded_L = get_user_1rm(selected_user, exercise, "L")
            recorded_R = get_user_1rm(selected_user, exercise, "R")
            
            # Get working max (predicted from recent performance)
            predicted_L = get_working_max(selected_user, exercise, "L")
            predicted_R = get_working_max(selected_user, exercise, "R")
            
            left_vals.append(predicted_L)
            right_vals.append(predicted_R)
            
            recorded_display_L = "Not Tested" if recorded_L == 0 else f"{recorded_L:.1f} kg"
            recorded_display_R = "Not Tested" if recorded_R == 0 else f"{recorded_R:.1f} kg"
            
            html_content = f'<div style="background: {color}; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);"><h4 style="margin: 0 0 15px 0; color: white; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{exercise}</h4><div style="margin-bottom: 12px;"><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-align: center; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">LAST RECORDED 1RM</div><div style="display: flex; justify-content: space-between; padding: 0 10px;"><div style="font-size: 14px; color: white; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">👈 {recorded_display_L}</div><div style="font-size: 14px; color: white; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">👉 {recorded_display_R}</div></div></div><div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 12px;"><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-align: center; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">PREDICTED 1RM (FROM TRAINING)</div><div style="display: flex; justify-content: space-between; padding: 0 10px;"><div style="font-size: 18px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">👈 {predicted_L:.1f} kg</div><div style="font-size: 18px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">👉 {predicted_R:.1f} kg</div></div></div></div>'
            st.markdown(html_content, unsafe_allow_html=True)
    
    st.caption("💡 Predicted 1RM updates automatically based on your recent training loads. Update recorded 1RM on Log Workout page.")
    
    # Strength balance chart
    st.markdown("---")
    st.markdown("### 📊 Strength Balance Analysis")
    st.caption("Predicted 1RM based on recent training performance")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=exercises_display,
        y=left_vals,
        name='Left Arm',
        marker_color='#4facfe',
        text=[f"{v:.1f} kg" for v in left_vals],
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=exercises_display,
        y=right_vals,
        name='Right Arm',
        marker_color='#f093fb',
        text=[f"{v:.1f} kg" for v in right_vals],
        textposition='auto'
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
        # Skip if either value is 0 (not tested yet)
        if left_vals[idx] == 0 or right_vals[idx] == 0:
            continue
            
        diff = abs(left_vals[idx] - right_vals[idx])
        max_val = max(left_vals[idx], right_vals[idx])
        
        # Only calculate if max_val is not zero
        if max_val > 0:
            pct_diff = (diff / max_val) * 100
            if pct_diff > 10:
                stronger = "Left" if left_vals[idx] > right_vals[idx] else "Right"
                imbalances.append(f"**{exercise}**: {stronger} arm is {pct_diff:.1f}% stronger ({diff:.1f} kg difference)")
    
    # Check if we have any data to analyze
    has_data = any(val > 0 for val in left_vals + right_vals)
    
    if not has_data:
        st.info("📊 Start training to see your strength balance analysis!")
    elif imbalances:
        st.warning("⚠️ **Strength Imbalances Detected:**\n\n" + "\n\n".join(imbalances))
        st.caption("💡 Consider focusing on your weaker arm to prevent injury and improve overall performance")
    else:
        st.success("✅ **Excellent balance!** Your left and right arm strength are well-matched")
    
    st.markdown("---")
    
    # ==================== CREATE NEW USER ====================
    st.markdown("### ➥ Create New User")
    st.caption("Pins are stored in the `Users` sheet (column `PIN` next to `Username`). Keep them private!")

    col_user1, col_user2, col_user3, col_user4 = st.columns([2, 1.5, 1.2, 1])

    with col_user1:
        new_username = st.text_input("Username:", placeholder="Enter new username", key="new_user_input")

    with col_user2:
        initial_bw = st.number_input("Initial Bodyweight (kg):", min_value=40.0, max_value=150.0, value=78.0, step=0.5, key="new_user_bw")

    with col_user3:
        new_user_pin = st.text_input(f"4-digit PIN:", max_chars=PIN_LENGTH, type="password", key="new_user_pin")

    with col_user4:
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
        if st.button("Create User", use_container_width=True):
            if not new_username or new_username.strip() == "":
                st.error("❌ Please enter a username!")
            elif not new_user_pin or len(new_user_pin) != PIN_LENGTH or not new_user_pin.isdigit():
                st.error("❌ PIN must be exactly 4 digits.")
            else:
                cleaned_username = new_username.strip()
                
                # Get current users to prevent duplicates
                current_users = load_users_from_sheets()
                if cleaned_username in current_users:
                    st.error(f"❌ User '{cleaned_username}' already exists!")
                else:
                    ok, msg = add_new_user(cleaned_username, initial_bw, pin=new_user_pin)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.success(f"🎉 Welcome **{cleaned_username}**! Bodyweight **{initial_bw} kg**, PIN saved securely.")
                        st.balloons()
                        st.info("🔄 Refreshing to load new user...")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    st.markdown("---")

    # ==================== DELETE YOUR PROFILE ====================
    st.markdown("### 🗑️ Delete Your Profile")

    st.warning("⚠️ **Warning:** Deleting your profile will remove all your data from the system. This action cannot be undone!")
    
    st.info(f"You can only delete your own profile: **{selected_user}**")

    if st.button("🗑️ Delete My Profile", use_container_width=False, type="secondary"):
        # Prevent deleting if it's the only user
        if len(available_users) <= 1:
            st.error("❌ Cannot delete the last user!")
        else:
            # Confirm deletion
            if st.session_state.get("confirm_delete") != selected_user:
                st.session_state.confirm_delete = selected_user
                st.warning(f"⚠️ Click 'Delete My Profile' again to confirm deletion of **{selected_user}**")
            else:
                ok, msg = delete_user(selected_user)
                if ok:
                    st.success(f"✅ Your profile **{selected_user}** has been deleted")
                    st.session_state.confirm_delete = None
                    st.session_state.current_user = USER_PLACEHOLDER
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
