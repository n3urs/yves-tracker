import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import *
from utils.helpers import USER_PLACEHOLDER
from datetime import datetime
from utils.helpers import (
    is_endurance_workout,
    increment_workout_count,
    get_endurance_training_enabled,
    get_workout_count
)

st.set_page_config(page_title="Log Workout", page_icon="📝", layout="wide")

init_session_state()
inject_global_styles()

# ==================== HEADER ====================
st.markdown("""
    <div class='page-header' style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    padding: 32px 24px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 15px 40px rgba(102,126,234,0.5);
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
        <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>📝 Log Workout</h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
            Record your training session and track your progress
        </p>
    </div>
""", unsafe_allow_html=True)

# Connect to sheet
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

# Load users dynamically from Google Sheets
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
    selector_key="user_selector_log",
    label="Select User:"
)
st.session_state.current_user = selected_user

if selected_user == USER_PLACEHOLDER:
    st.info("🔒 Select a profile from the sidebar to log a workout.")
    st.stop()

# Bodyweight input
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Bodyweight")
current_bw_kg = get_bodyweight(spreadsheet, selected_user) if spreadsheet else 78.0

new_bw_kg = st.sidebar.number_input(
    "Your bodyweight (kg):",
    min_value=40.0,
    max_value=150.0,
    value=current_bw_kg,
    step=0.5,
    key="bodyweight_input"
)

if new_bw_kg != current_bw_kg and spreadsheet:
    set_bodyweight(spreadsheet, selected_user, new_bw_kg)
    st.sidebar.success(f"✅ Bodyweight updated to {new_bw_kg:.1f}kg")

# Check if connected before showing tabs
if not spreadsheet:
    st.error("❌ Could not connect to Google Sheets. Please check your configuration.")
else:
    # TABS FOR WORKOUT vs 1RM TEST
    tab1, tab2 = st.tabs(["💪 Log Training Session", "🏆 Update 1RM"])
    
    # ==================== TAB 1: REGULAR WORKOUT ====================
    with tab1:
        st.markdown("### 🎯 Select Workout Type")
        
        # Initialize workout type selection
        if 'workout_type' not in st.session_state:
            st.session_state.workout_type = "Standard Exercises"
        
        workout_type_col1, workout_type_col2 = st.columns(2)
        
        with workout_type_col1:
            if st.button("🏋️ Standard Exercises", use_container_width=True, 
                        type="primary" if st.session_state.workout_type == "Standard Exercises" else "secondary"):
                st.session_state.workout_type = "Standard Exercises"
                st.rerun()
        
        with workout_type_col2:
            if st.button("✨ Custom Workout", use_container_width=True,
                        type="primary" if st.session_state.workout_type == "Custom Workout" else "secondary"):
                st.session_state.workout_type = "Custom Workout"
                st.rerun()
        
        st.markdown("---")
        
        # ==================== STANDARD EXERCISES ====================
        if st.session_state.workout_type == "Standard Exercises":
            st.markdown("### 🎯 Select Exercise")
            
            col1, col2, col3 = st.columns(3)
            
            # Exercise selection with visual cards
            if 'selected_exercise' not in st.session_state:
                st.session_state.selected_exercise = "20mm Edge"
        
            with col1:
                if st.button("🖐️ 20mm Edge", use_container_width=True, type="primary" if st.session_state.selected_exercise == "20mm Edge" else "secondary"):
                    st.session_state.selected_exercise = "20mm Edge"
                    st.rerun()
        
            with col2:
                if st.button("🤏 Pinch", use_container_width=True, type="primary" if st.session_state.selected_exercise == "Pinch" else "secondary"):
                    st.session_state.selected_exercise = "Pinch"
                    st.rerun()
        
            with col3:
                if st.button("💪 Wrist Roller", use_container_width=True, type="primary" if st.session_state.selected_exercise == "Wrist Roller" else "secondary"):
                    st.session_state.selected_exercise = "Wrist Roller"
                    st.rerun()
        
            exercise = st.session_state.selected_exercise
        
            # Get working max (auto-updated from recent lifts)
            current_1rm_L = get_working_max(spreadsheet, selected_user, exercise, "L")
            current_1rm_R = get_working_max(spreadsheet, selected_user, exercise, "R")
        
            st.markdown("---")
        
            # Get last workout data for both arms
            last_workout_L = get_last_workout(spreadsheet, selected_user, exercise, "L")
            last_workout_R = get_last_workout(spreadsheet, selected_user, exercise, "R")
        
            # Check if this should be an endurance workout
            is_endurance = is_endurance_workout(spreadsheet, selected_user, exercise)
        
            # Generate suggestions
            suggestion_L = generate_workout_suggestion(last_workout_L, is_endurance)
            suggestion_R = generate_workout_suggestion(last_workout_R, is_endurance)
        
            # Show last workout and suggestions
            st.markdown("### 📋 Last Workout & Suggestions")
            st.caption("💡 Smart recommendations based on your previous performance")
        
            col_info_L, col_info_R = st.columns(2)
        
            with col_info_L:
                if last_workout_L:
                    weight_L_kg = last_workout_L['weight']
                    rpe_L_val = last_workout_L['rpe']
                    emoji_L = suggestion_L['emoji']
                    sugg_title_L = suggestion_L['suggestion']
                    sugg_msg_L = suggestion_L['message']
                
                    html_content = f'<div style="background: linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%); padding: 24px; border-radius: 16px; box-shadow: 0 8px 24px rgba(79,172,254,0.4);"><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 18px;"><div style="font-size: 24px;">💪</div><div style="font-size: 18px; color: white; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">Left Arm</div></div><div style="background: rgba(0,0,0,0.2); padding: 18px; border-radius: 12px; margin-bottom: 16px;"><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;"><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">WEIGHT</div><div style="font-size: 28px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{weight_L_kg:.1f} kg</div></div><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">RPE</div><div style="font-size: 28px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{rpe_L_val}/10</div></div></div></div><div style="background: rgba(0,0,0,0.25); padding: 14px 16px; border-radius: 10px; display: flex; align-items: center; gap: 12px;"><div style="font-size: 28px;">{emoji_L}</div><div><div style="font-size: 15px; font-weight: 700; color: white; margin-bottom: 3px; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">{sugg_title_L}</div><div style="font-size: 12px; color: rgba(255,255,255,0.95); line-height: 1.4; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">{sugg_msg_L}</div></div></div></div>'
                    st.markdown(html_content, unsafe_allow_html=True)
                else:
                    emoji_L = suggestion_L['emoji']
                    sugg_msg_L = suggestion_L['message']
                    html_content = f'<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 32px 24px; border-radius: 16px; text-align: center; box-shadow: 0 8px 24px rgba(79,172,254,0.4);"><div style="font-size: 18px; color: white; font-weight: 700; margin-bottom: 16px;">💪 Left Arm</div><div style="font-size: 48px; margin: 20px 0;">{emoji_L}</div><div style="font-size: 15px; color: white; font-weight: 600; line-height: 1.6;">{sugg_msg_L}</div></div>'
                    st.markdown(html_content, unsafe_allow_html=True)
        
            with col_info_R:
                if last_workout_R:
                    weight_R_kg = last_workout_R['weight']
                    rpe_R_val = last_workout_R['rpe']
                    emoji_R = suggestion_R['emoji']
                    sugg_title_R = suggestion_R['suggestion']
                    sugg_msg_R = suggestion_R['message']
                
                    html_content = f'<div style="background: linear-gradient(135deg, #d946b5 0%, #e23670 100%); padding: 24px; border-radius: 16px; box-shadow: 0 8px 24px rgba(240,147,251,0.4);"><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 18px;"><div style="font-size: 24px;">💪</div><div style="font-size: 18px; color: white; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">Right Arm</div></div><div style="background: rgba(0,0,0,0.2); padding: 18px; border-radius: 12px; margin-bottom: 16px;"><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;"><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">WEIGHT</div><div style="font-size: 28px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{weight_R_kg:.1f} kg</div></div><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">RPE</div><div style="font-size: 28px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{rpe_R_val}/10</div></div></div></div><div style="background: rgba(0,0,0,0.25); padding: 14px 16px; border-radius: 10px; display: flex; align-items: center; gap: 12px;"><div style="font-size: 28px;">{emoji_R}</div><div><div style="font-size: 15px; font-weight: 700; color: white; margin-bottom: 3px; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">{sugg_title_R}</div><div style="font-size: 12px; color: rgba(255,255,255,0.95); line-height: 1.4; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">{sugg_msg_R}</div></div></div></div>'
                    st.markdown(html_content, unsafe_allow_html=True)
                else:
                    emoji_R = suggestion_R['emoji']
                    sugg_msg_R = suggestion_R['message']
                    html_content = f'<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 32px 24px; border-radius: 16px; text-align: center; box-shadow: 0 8px 24px rgba(240,147,251,0.4);"><div style="font-size: 18px; color: white; font-weight: 700; margin-bottom: 16px;">💪 Right Arm</div><div style="font-size: 48px; margin: 20px 0;">{emoji_R}</div><div style="font-size: 15px; color: white; font-weight: 600; line-height: 1.6;">{sugg_msg_R}</div></div>'
                    st.markdown(html_content, unsafe_allow_html=True)
        
            st.markdown("---")
        
            # Show endurance mode banner if applicable
            if is_endurance:
                workout_count = get_workout_count(spreadsheet, selected_user, exercise)
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(16,185,129,0.5);
                    border: 2px solid rgba(255,255,255,0.2); animation: pulse 2s ease-in-out infinite;'>
                        <div style='text-align: center;'>
                            <div style='font-size: 36px; margin-bottom: 8px;'>🏃</div>
                            <div style='font-size: 24px; color: white; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 8px;'>
                                ENDURANCE SESSION - REPEATERS
                            </div>
                            <div style='font-size: 15px; color: rgba(255,255,255,0.95); text-shadow: 0 1px 2px rgba(0,0,0,0.3); line-height: 1.6;'>
                                Sport climbing endurance protocol for sustained routes<br>
                                <strong>55% max load • 7 seconds on, 3 seconds off • 6 hangs per set</strong>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
            # Set target percentage based on workout type
            if is_endurance:
                target_pct = 55  # 50-60% for endurance (using middle value)
            else:
                target_pct = 80  # Normal strength training
        
            # Calculate suggested loads (in kg, will convert for display)
            if is_endurance:
                # For endurance: use 55% of 1RM (middle of 50-60% range)
                suggested_load_L_kg = current_1rm_L * 0.55
                suggested_load_R_kg = current_1rm_R * 0.55
            else:
                # For strength: based on last workout or 80% of 1RM
                if last_workout_L and suggestion_L.get('weight_change', 0) != 0:
                    suggested_load_L_kg = last_workout_L['weight'] + suggestion_L['weight_change']
                else:
                    suggested_load_L_kg = current_1rm_L * 0.8
                
                if last_workout_R and suggestion_R.get('weight_change', 0) != 0:
                    suggested_load_R_kg = last_workout_R['weight'] + suggestion_R['weight_change']
                else:
                    suggested_load_R_kg = current_1rm_R * 0.8
            
            # Actual Weight Lifted
            st.markdown("### ⚖️ Actual Weight Lifted (kg)")
            use_same_weight = st.checkbox("Log same workout for both arms (weight, reps, sets, RPE)", value=True, key="same_weight_toggle")
        
            if use_same_weight:
                actual_load_both = st.number_input(
                    "Weight Lifted (kg) - Both Arms:",
                    min_value=0.0,
                    max_value=200.0,
                    value=(suggested_load_L_kg + suggested_load_R_kg) / 2,
                    step=0.25,
                    key="actual_load_both",
                    help="Enter the weight you actually lifted"
                )
                actual_load_L = actual_load_both
                actual_load_R = actual_load_both
            else:
                col_L, col_R = st.columns(2)
                with col_L:
                    actual_load_L = st.number_input(
                        "Left Arm Weight (kg):",
                        min_value=0.0,
                        max_value=200.0,
                        value=suggested_load_L_kg,
                        step=0.25,
                        key="actual_load_L"
                    )
                with col_R:
                    actual_load_R = st.number_input(
                        "Right Arm Weight (kg):",
                        min_value=0.0,
                        max_value=200.0,
                        value=suggested_load_R_kg,
                        step=0.25,
                        key="actual_load_R"
                    )
        
            st.markdown("---")
        
            # Workout Details
            st.markdown("### 📊 Workout Details")
        
            # Get default values - use endurance defaults if it's an endurance workout
            if is_endurance:
                default_reps_L = 6  # 6 hangs for repeaters protocol
                default_reps_R = 6
                default_sets_L = 3
                default_sets_R = 3
                default_rpe_L = 7  # Should feel challenging but sustainable
                default_rpe_R = 7
            else:
                default_reps_L = last_workout_L['reps'] if last_workout_L else 5
                default_reps_R = last_workout_R['reps'] if last_workout_R else 5
                default_sets_L = last_workout_L['sets'] if last_workout_L else 3
                default_sets_R = last_workout_R['sets'] if last_workout_R else 3
                default_rpe_L = last_workout_L['rpe'] if last_workout_L else 7
                default_rpe_R = last_workout_R['rpe'] if last_workout_R else 7
        
            if use_same_weight:
                # Same details for both arms
                col_reps, col_sets, col_rpe = st.columns(3)
            
                with col_reps:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(103,126,234,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>🔢</div>
                            <div style='font-size: 12px; color: #888;'>Reps per Set</div>
                        </div>
                    """, unsafe_allow_html=True)
                    max_reps = 20 if is_endurance else 15
                    reps_per_set = st.number_input("", min_value=1, max_value=max_reps, value=default_reps_L, step=1, key="reps_input", label_visibility="collapsed")
                    reps_per_set_L = reps_per_set
                    reps_per_set_R = reps_per_set
            
                with col_sets:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(240,147,251,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>📚</div>
                            <div style='font-size: 12px; color: #888;'>Sets Completed</div>
                        </div>
                    """, unsafe_allow_html=True)
                    sets_completed = st.number_input("", min_value=1, max_value=10, value=default_sets_L, step=1, key="sets_input", label_visibility="collapsed")
                    sets_completed_L = sets_completed
                    sets_completed_R = sets_completed
            
                with col_rpe:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(250,112,154,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>💥</div>
                            <div style='font-size: 12px; color: #888;'>RPE (1-10)</div>
                        </div>
                    """, unsafe_allow_html=True)
                    rpe = st.slider("", min_value=1, max_value=10, value=default_rpe_L, step=1, key="rpe_slider", label_visibility="collapsed")
                    rpe_L = rpe
                    rpe_R = rpe
            else:
                # Different details for each arm
                st.markdown("#### Left Arm")
                col_reps_L, col_sets_L, col_rpe_L = st.columns(3)
            
                with col_reps_L:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(79,172,254,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>🔢</div>
                            <div style='font-size: 12px; color: #888;'>Reps per Set</div>
                        </div>
                    """, unsafe_allow_html=True)
                    max_reps_L = 20 if is_endurance else 15
                    reps_per_set_L = st.number_input("", min_value=1, max_value=max_reps_L, value=default_reps_L, step=1, key="reps_input_L", label_visibility="collapsed")
            
                with col_sets_L:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(79,172,254,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>📚</div>
                            <div style='font-size: 12px; color: #888;'>Sets Completed</div>
                        </div>
                    """, unsafe_allow_html=True)
                    sets_completed_L = st.number_input("", min_value=1, max_value=10, value=default_sets_L, step=1, key="sets_input_L", label_visibility="collapsed")
            
                with col_rpe_L:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(79,172,254,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>💥</div>
                            <div style='font-size: 12px; color: #888;'>RPE (1-10)</div>
                        </div>
                    """, unsafe_allow_html=True)
                    rpe_L = st.slider("", min_value=1, max_value=10, value=default_rpe_L, step=1, key="rpe_slider_L", label_visibility="collapsed")
            
                st.markdown("#### Right Arm")
                col_reps_R, col_sets_R, col_rpe_R = st.columns(3)
            
                with col_reps_R:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(240,147,251,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>🔢</div>
                            <div style='font-size: 12px; color: #888;'>Reps per Set</div>
                        </div>
                    """, unsafe_allow_html=True)
                    max_reps_R = 20 if is_endurance else 15
                    reps_per_set_R = st.number_input("", min_value=1, max_value=max_reps_R, value=default_reps_R, step=1, key="reps_input_R", label_visibility="collapsed")
            
                with col_sets_R:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(240,147,251,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>📚</div>
                            <div style='font-size: 12px; color: #888;'>Sets Completed</div>
                        </div>
                    """, unsafe_allow_html=True)
                    sets_completed_R = st.number_input("", min_value=1, max_value=10, value=default_sets_R, step=1, key="sets_input_R", label_visibility="collapsed")
            
                with col_rpe_R:
                    st.markdown("""
                        <div style='text-align: center; padding: 10px; background: rgba(240,147,251,0.1); border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 24px;'>💥</div>
                            <div style='font-size: 12px; color: #888;'>RPE (1-10)</div>
                        </div>
                    """, unsafe_allow_html=True)
                    rpe_R = st.slider("", min_value=1, max_value=10, value=default_rpe_R, step=1, key="rpe_slider_R", label_visibility="collapsed")
        
            st.markdown("---")
        
            # Session Notes
            st.markdown("### 📝 Session Notes")
            notes = st.text_area(
                "How did it feel?",
                placeholder="e.g., Felt strong today, left arm a bit tired...",
                key="notes_input",
                label_visibility="collapsed"
            )
        
            # Quick note buttons
            st.markdown("**Quick Tags:**")
            if 'quick_note_append' not in st.session_state:
                st.session_state.quick_note_append = ""
        
            quick_cols = st.columns(len(QUICK_NOTES))
            for idx, (emoji_label, note_text) in enumerate(QUICK_NOTES.items()):
                if quick_cols[idx].button(emoji_label, key=f"quick_{note_text}"):
                    if st.session_state.quick_note_append:
                        st.session_state.quick_note_append += f" {note_text}"
                    else:
                        st.session_state.quick_note_append = note_text
                    st.rerun()
        
            if st.session_state.quick_note_append:
                final_notes = (notes + " " + st.session_state.quick_note_append).strip()
                st.info(f"📌 Notes to save: {final_notes}")
            else:
                final_notes = notes
        
            if st.session_state.quick_note_append:
                if st.button("🗑️ Clear tags"):
                    st.session_state.quick_note_append = ""
                    st.rerun()
        
            st.markdown("---")
        
            # Submit button
            if st.button("✅ Log Workout", type="primary", use_container_width=True):
                workout_data_L = {
                    "User": selected_user,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Exercise": exercise,
                    "Arm": "L",
                    "1RM_Reference": current_1rm_L,
                    "Target_Percentage": target_pct,
                    "Prescribed_Load_kg": suggested_load_L_kg,
                    "Actual_Load_kg": actual_load_L,
                    "Reps_Per_Set": reps_per_set_L,
                    "Sets_Completed": sets_completed_L,
                    "RPE": rpe_L,
                    "Notes": final_notes
                }
            
                workout_data_R = {
                    "User": selected_user,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Exercise": exercise,
                    "Arm": "R",
                    "1RM_Reference": current_1rm_R,
                    "Target_Percentage": target_pct,
                    "Prescribed_Load_kg": suggested_load_R_kg,
                    "Actual_Load_kg": actual_load_R,
                    "Reps_Per_Set": reps_per_set_R,
                    "Sets_Completed": sets_completed_R,
                    "RPE": rpe_R,
                    "Notes": final_notes
                }
            
                success_L = save_workout_to_sheets(workout_sheet, workout_data_L)
                success_R = save_workout_to_sheets(workout_sheet, workout_data_R)
            
                if success_L and success_R:
                    # Increment workout count for endurance tracking
                    if get_endurance_training_enabled(spreadsheet, selected_user):
                        increment_workout_count(spreadsheet, selected_user, exercise)
                    
                    st.session_state.quick_note_append = ""
                    
                    if is_endurance:
                        st.success("✅ Endurance workout logged successfully! 🏃")
                    else:
                        st.success("✅ Workout logged successfully for both arms!")
                    st.balloons()
                else:
                    st.error("❌ Failed to save workout. Please try again.")
        
        # ==================== CUSTOM WORKOUT LOGGING ====================
        elif st.session_state.workout_type == "Custom Workout":
            st.markdown("### ✨ Select Custom Workout")
            
            # Load user's custom workouts
            user_workouts = get_user_custom_workouts(spreadsheet, selected_user)
            
            if user_workouts.empty:
                st.warning("You haven't created any custom workouts yet!")
                st.info("Go to the Custom Workouts page to create your first workout template.")
                if st.button("🏋️ Go to Custom Workouts", use_container_width=True):
                    st.switch_page("pages/6_Custom_Workouts.py")
            else:
                # Dropdown to select workout
                workout_names = user_workouts['WorkoutName'].tolist()
                selected_workout_name = st.selectbox(
                    "Choose a workout:",
                    workout_names,
                    key="custom_workout_select"
                )
                
                # Get the selected workout details
                workout_details = user_workouts[user_workouts['WorkoutName'] == selected_workout_name].iloc[0]
                
                # Display workout info
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 12px; margin: 20px 0;'>
                        <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>
                            🏋️ {selected_workout_name}
                        </div>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9);'>
                            Type: {workout_details['WorkoutType']} | {workout_details.get('Description', '')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 📊 Enter Workout Data")
                
                # Create dynamic form based on tracked metrics
                col1, col2, col3 = st.columns(3)
                
                workout_weight = None
                workout_sets = None
                workout_reps = None
                workout_duration = None
                workout_distance = None
                workout_rpe = None
                
                with col1:
                    if workout_details.get('TracksWeight', False):
                        workout_weight = st.number_input(
                            "Weight (kg)",
                            min_value=0.0,
                            max_value=500.0,
                            value=0.0,
                            step=0.5,
                            key="custom_weight"
                        )
                    
                    if workout_details.get('TracksSets', False):
                        workout_sets = st.number_input(
                            "Sets",
                            min_value=1,
                            max_value=20,
                            value=3,
                            step=1,
                            key="custom_sets"
                        )
                
                with col2:
                    if workout_details.get('TracksReps', False):
                        workout_reps = st.number_input(
                            "Reps",
                            min_value=1,
                            max_value=100,
                            value=10,
                            step=1,
                            key="custom_reps"
                        )
                    
                    if workout_details.get('TracksDuration', False):
                        workout_duration = st.number_input(
                            "Duration (min)",
                            min_value=1,
                            max_value=600,
                            value=30,
                            step=1,
                            key="custom_duration"
                        )
                
                with col3:
                    if workout_details.get('TracksDistance', False):
                        workout_distance = st.number_input(
                            "Distance (km)",
                            min_value=0.0,
                            max_value=100.0,
                            value=5.0,
                            step=0.1,
                            key="custom_distance"
                        )
                    
                    if workout_details.get('TracksRPE', False):
                        workout_rpe = st.slider(
                            "RPE (1-10)",
                            min_value=1,
                            max_value=10,
                            value=7,
                            step=1,
                            key="custom_rpe"
                        )
                
                st.markdown("---")
                
                # Notes
                custom_notes = st.text_area(
                    "Session notes (optional):",
                    placeholder="How did it feel?",
                    key="custom_notes"
                )
                
                st.markdown("---")
                
                # Submit button
                if st.button("✅ Log Custom Workout", type="primary", use_container_width=True):
                    success = log_custom_workout(
                        spreadsheet=spreadsheet,
                        user=selected_user,
                        workout_id=workout_details['WorkoutID'],
                        workout_name=selected_workout_name,
                        date=datetime.now(),
                        weight=workout_weight,
                        sets=workout_sets,
                        reps=workout_reps,
                        duration=workout_duration,
                        distance=workout_distance,
                        rpe=workout_rpe,
                        notes=custom_notes
                    )
                    
                    if success:
                        st.success(f"✅ {selected_workout_name} logged successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to log workout. Please try again.")
    
    # ==================== TAB 2: 1RM UPDATE ====================
    with tab2:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
            padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
                <div style='font-size: 32px; margin-bottom: 10px;'>🏆</div>
                <div style='font-size: 24px; font-weight: bold; color: white;'>Update Your 1RM</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;'>
                    Test your max strength and update your training targets
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Select Exercise to Test")
        test_exercise = st.selectbox(
            "",
            ["20mm Edge", "Pinch", "Wrist Roller"],
            key="test_exercise_select",
            label_visibility="collapsed"
        )
        
        current_1rm_L_test = get_user_1rm(spreadsheet, selected_user, test_exercise, "L")
        current_1rm_R_test = get_user_1rm(spreadsheet, selected_user, test_exercise, "R")
        
        st.markdown("---")
        st.markdown("### 📊 Current 1RMs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                padding: 25px; border-radius: 12px; text-align: center;'>
                    <div style='font-size: 16px; color: #555; margin-bottom: 8px;'>Left Arm (Current)</div>
                    <div style='font-size: 40px; font-weight: bold; color: #333;'>{current_1rm_L_test:.1f} kg</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                padding: 25px; border-radius: 12px; text-align: center;'>
                    <div style='font-size: 16px; color: #555; margin-bottom: 8px;'>Right Arm (Current)</div>
                    <div style='font-size: 40px; font-weight: bold; color: #333;'>{current_1rm_R_test:.1f} kg</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🆕 Enter New 1RM Results")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Left Arm**")
            new_1rm_L = st.number_input(
                "New 1RM (kg):",
                min_value=0.0,
                max_value=200.0,
                value=float(current_1rm_L_test),
                step=0.25,
                key="new_1rm_L"
            )
            
            if new_1rm_L > current_1rm_L_test:
                st.success(f"🎉 New PR! +{(new_1rm_L - current_1rm_L_test):.2f} kg")
            elif new_1rm_L < current_1rm_L_test:
                st.warning(f"⚠️ Lower than current (-{(current_1rm_L_test - new_1rm_L):.2f} kg)")
        
        with col_right:
            st.markdown("**Right Arm**")
            new_1rm_R = st.number_input(
                "New 1RM (kg):",
                min_value=0.0,
                max_value=200.0,
                value=float(current_1rm_R_test),
                step=0.25,
                key="new_1rm_R"
            )
            
            if new_1rm_R > current_1rm_R_test:
                st.success(f"🎉 New PR! +{(new_1rm_R - current_1rm_R_test):.2f} kg")
            elif new_1rm_R < current_1rm_R_test:
                st.warning(f"⚠️ Lower than current (-{(current_1rm_R_test - new_1rm_R):.2f} kg)")
        
        st.markdown("---")
        
        log_test_as_workout = st.checkbox(
            "Also log this as a workout entry",
            value=True,
            help="Records the test in your workout history"
        )
        
        test_notes = st.text_area(
            "Test Notes (optional):",
            placeholder="How did the test feel?",
            key="test_notes"
        )
        
        st.markdown("---")
        
        if st.button("🏆 Update 1RMs", type="primary", use_container_width=True):
            success_L = update_user_1rm(spreadsheet, selected_user, test_exercise, "L", new_1rm_L)
            success_R = update_user_1rm(spreadsheet, selected_user, test_exercise, "R", new_1rm_R)
            
            if success_L and success_R:
                st.success("✅ 1RMs updated successfully!")
                
                if log_test_as_workout:
                    workout_data_L = {
                        "User": selected_user,
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Exercise": f"1RM Test - {test_exercise}",
                        "Arm": "L",
                        "1RM_Reference": new_1rm_L,
                        "Target_Percentage": 100,
                        "Prescribed_Load_kg": new_1rm_L,
                        "Actual_Load_kg": new_1rm_L,
                        "Reps_Per_Set": 1,
                        "Sets_Completed": 1,
                        "RPE": 10,
                        "Notes": test_notes
                    }
                    
                    workout_data_R = {
                        "User": selected_user,
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Exercise": f"1RM Test - {test_exercise}",
                        "Arm": "R",
                        "1RM_Reference": new_1rm_R,
                        "Target_Percentage": 100,
                        "Prescribed_Load_kg": new_1rm_R,
                        "Actual_Load_kg": new_1rm_R,
                        "Reps_Per_Set": 1,
                        "Sets_Completed": 1,
                        "RPE": 10,
                        "Notes": test_notes
                    }
                    
                    save_workout_to_sheets(workout_sheet, workout_data_L)
                    save_workout_to_sheets(workout_sheet, workout_data_R)
                    st.success("📝 Test also logged in workout history!")
                
                st.balloons()
            else:
                st.error("❌ Failed to update 1RMs. Please try again.")
        
        st.caption("💡 Tip: Test your 1RM every 3-4 weeks for accurate training targets")

# ==================== LOG OTHER ACTIVITIES ====================
st.markdown("---")
st.markdown("### 🗓️ Log Other Training Activities")
st.info("📌 Track all your training to see your full weekly progress and calendar!")

tab_climb, tab_board, tab_work = st.tabs(["🧗 Log Climbing Session", "🎯 Log Board Session", "💪 Log Work Pullups"])

with tab_climb:
    st.markdown("**Record a climbing session**")
    
    col_date, col_duration = st.columns(2)
    
    with col_date:
        climb_date = st.date_input(
            "Session date:",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            key="climb_date",
            help="Select the date of your climbing session"
        )
    
    with col_duration:
        climb_duration = st.number_input(
            "Duration (minutes):",
            min_value=5,
            max_value=480,
            value=60,
            step=5,
            key="climb_duration"
        )
    
    climb_notes = st.text_area(
        "Session notes (optional):",
        placeholder="e.g., Boulderryn, felt strong on V5s",
        key="climb_notes"
    )
    
    if st.button("Log Climbing Session", type="primary", use_container_width=True, key="log_climb"):
        if log_activity_to_sheets(spreadsheet, selected_user, "Climbing", climb_duration, climb_notes, climb_date):
            st.success(f"✅ Climbing session logged for {climb_date.strftime('%Y-%m-%d')}! ({climb_duration} min)")
            st.balloons()
        else:
            st.error("❌ Failed to log climbing session.")

with tab_board:
    st.markdown("**Record a Kilter Board / training board session**")
    
    col_date, col_duration = st.columns(2)
    
    with col_date:
        board_date = st.date_input(
            "Session date:",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            key="board_date",
            help="Select the date of your board session"
        )
    
    with col_duration:
        board_duration = st.number_input(
            "Duration (minutes):",
            min_value=5,
            max_value=480,
            value=90,
            step=5,
            key="board_duration"
        )
    
    board_notes = st.text_area(
        "Session notes (optional):",
        placeholder="e.g., Kilter board projecting, sent a few V7s",
        key="board_notes"
    )
    
    if st.button("Log Board Session", type="primary", use_container_width=True, key="log_board"):
        if log_activity_to_sheets(spreadsheet, selected_user, "Board", board_duration, board_notes, board_date):
            st.success(f"✅ Board session logged for {board_date.strftime('%Y-%m-%d')}! ({board_duration} min)")
            st.balloons()
        else:
            st.error("❌ Failed to log board session.")

with tab_work:
    st.markdown("**Quick log for pullups at work**")
    
    work_date = st.date_input(
        "Session date:",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        key="work_date",
        help="Select the date you did pullups"
    )
    
    work_notes = st.text_input(
        "Notes (optional):",
        placeholder="e.g., 3 sets during lunch break",
        key="work_notes"
    )
    
    if st.button("Log Work Pullups", type="primary", use_container_width=True, key="log_work"):
        if log_activity_to_sheets(spreadsheet, selected_user, "Work", None, work_notes, work_date):
            st.success(f"✅ Work pullups logged for {work_date.strftime('%Y-%m-%d')}!")
        else:
            st.error("❌ Failed to log work pullups.")
