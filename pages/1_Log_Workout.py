import streamlit as st
import sys
import time
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
            Choose what you want to log
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
current_bw_kg = get_bodyweight(selected_user)

new_bw_kg = st.sidebar.number_input(
    "Your bodyweight (kg):",
    min_value=40.0,
    max_value=150.0,
    value=current_bw_kg,
    step=0.5,
    key="bodyweight_input"
)

if new_bw_kg != current_bw_kg:
    set_bodyweight(selected_user, new_bw_kg)
    st.sidebar.success(f"✅ Bodyweight updated to {new_bw_kg:.1f}kg")

# Initialize modal states
if 'show_standard_modal' not in st.session_state:
    st.session_state.show_standard_modal = False
if 'show_custom_modal' not in st.session_state:
    st.session_state.show_custom_modal = False
if 'show_activity_modal' not in st.session_state:
    st.session_state.show_activity_modal = False
if 'show_1rm_modal' not in st.session_state:
    st.session_state.show_1rm_modal = False
if 'selected_activity_type' not in st.session_state:
    st.session_state.selected_activity_type = None

# ==================== MAIN SELECTION GRID ====================
st.markdown("## 🎯 What would you like to log?")
st.markdown("")

# First row: Main workout types
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 10px;
        box-shadow: 0 8px 24px rgba(102,126,234,0.4); border: 2px solid rgba(255,255,255,0.1);'>
            <div style='font-size: 48px; margin-bottom: 12px;'>🏋️</div>
            <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>Standard Exercises</div>
            <div style='font-size: 13px; color: rgba(255,255,255,0.85);'>
                20mm Edge • Pinch • Roller
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Log Standard Workout", use_container_width=True, type="primary", key="btn_standard"):
        # Reset all other modals
        st.session_state.show_custom_modal = False
        st.session_state.show_activity_modal = False
        st.session_state.show_1rm_modal = False
        st.session_state.show_standard_modal = True
        st.rerun()

with col2:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
        padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 10px;
        box-shadow: 0 8px 24px rgba(240,147,251,0.4); border: 2px solid rgba(255,255,255,0.1);'>
            <div style='font-size: 48px; margin-bottom: 12px;'>✨</div>
            <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>Custom Workouts</div>
            <div style='font-size: 13px; color: rgba(255,255,255,0.85);'>
                Your personalized templates
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Log Custom Workout", use_container_width=True, type="primary", key="btn_custom"):
        # Reset all other modals
        st.session_state.show_standard_modal = False
        st.session_state.show_activity_modal = False
        st.session_state.show_1rm_modal = False
        st.session_state.show_custom_modal = True
        st.rerun()

with col3:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
        padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 10px;
        box-shadow: 0 8px 24px rgba(79,172,254,0.4); border: 2px solid rgba(255,255,255,0.1);'>
            <div style='font-size: 48px; margin-bottom: 12px;'>🗓️</div>
            <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 8px;'>Climbing & Other Activities</div>
            <div style='font-size: 13px; color: rgba(255,255,255,0.85);'>
                Climbing • Board • Work Pullups
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Log Activity", use_container_width=True, type="primary", key="btn_activity"):
        # Reset all other modals
        st.session_state.show_standard_modal = False
        st.session_state.show_custom_modal = False
        st.session_state.show_1rm_modal = False
        st.session_state.show_activity_modal = True
        st.rerun()

st.markdown("")

# Second row: 1RM Test
col_center = st.columns([1, 2, 1])[1]
with col_center:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
        padding: 25px 20px; border-radius: 16px; text-align: center; margin-bottom: 10px;
        box-shadow: 0 8px 24px rgba(250,112,154,0.4); border: 2px solid rgba(255,255,255,0.1);'>
            <div style='font-size: 42px; margin-bottom: 10px;'>🏆</div>
            <div style='font-size: 20px; font-weight: 700; color: white; margin-bottom: 6px;'>Update 1RM</div>
            <div style='font-size: 13px; color: rgba(255,255,255,0.85);'>
                Test and update your max strength
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Update 1RM", use_container_width=True, type="primary", key="btn_1rm"):
        # Reset all other modals
        st.session_state.show_standard_modal = False
        st.session_state.show_custom_modal = False
        st.session_state.show_activity_modal = False
        st.session_state.show_1rm_modal = True
        st.rerun()

# ==================== MODAL: STANDARD WORKOUT ====================
@st.dialog("🏋️ Log Standard Workout", width="large")
def show_standard_workout_modal():
    # Date picker
    workout_date = st.date_input(
        "📅 Workout Date:",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        help="Select a past date if you forgot to log a workout",
        key="modal_standard_date"
    )
    
    st.markdown("### 🎯 Select Exercise")
    
    col1, col2, col3 = st.columns(3)
    
    if 'selected_exercise' not in st.session_state:
        st.session_state.selected_exercise = "20mm Edge"
    
    with col1:
        if st.button("🖐️ 20mm Edge", use_container_width=True, type="primary" if st.session_state.selected_exercise == "20mm Edge" else "secondary", key="modal_20mm"):
            st.session_state.selected_exercise = "20mm Edge"
            st.rerun()
    
    with col2:
        if st.button("🤏 Pinch", use_container_width=True, type="primary" if st.session_state.selected_exercise == "Pinch" else "secondary", key="modal_pinch"):
            st.session_state.selected_exercise = "Pinch"
            st.rerun()
    
    with col3:
        if st.button("💪 Wrist Roller", use_container_width=True, type="primary" if st.session_state.selected_exercise == "Wrist Roller" else "secondary", key="modal_roller"):
            st.session_state.selected_exercise = "Wrist Roller"
            st.rerun()
    
    exercise = st.session_state.selected_exercise
    
    # Get working max
    current_1rm_L = get_working_max(selected_user, exercise, "L")
    current_1rm_R = get_working_max(selected_user, exercise, "R")
    
    st.markdown("---")
    
    # Get last workout data
    last_workout_L = get_last_workout(selected_user, exercise, "L")
    last_workout_R = get_last_workout(selected_user, exercise, "R")
    
    # Check if endurance workout
    is_endurance = is_endurance_workout(selected_user, exercise)
    
    # Generate suggestions
    suggestion_L = generate_workout_suggestion(last_workout_L, is_endurance)
    suggestion_R = generate_workout_suggestion(last_workout_R, is_endurance)
    
    # Show last workout
    st.markdown("### 📋 Last Workout & Suggestions")
    
    col_info_L, col_info_R = st.columns(2)
    
    with col_info_L:
        if last_workout_L:
            weight_L_kg = last_workout_L['weight']
            rpe_L_val = last_workout_L['rpe']
            emoji_L = suggestion_L['emoji']
            sugg_title_L = suggestion_L['suggestion']
            sugg_msg_L = suggestion_L['message']
            
            html_content = f'<div style="background: linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%); padding: 20px; border-radius: 12px;"><div style="font-size: 16px; color: white; font-weight: 700; margin-bottom: 12px;">💪 Left Arm</div><div style="background: rgba(0,0,0,0.2); padding: 14px; border-radius: 8px; margin-bottom: 12px;"><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;"><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase;">WEIGHT</div><div style="font-size: 24px; color: white; font-weight: 700;">{weight_L_kg:.1f} kg</div></div><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase;">RPE</div><div style="font-size: 24px; color: white; font-weight: 700;">{rpe_L_val}/10</div></div></div></div><div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px;"><div style="font-size: 24px;">{emoji_L}</div><div><div style="font-size: 14px; font-weight: 700; color: white; margin-bottom: 3px;">{sugg_title_L}</div><div style="font-size: 11px; color: rgba(255,255,255,0.95);">{sugg_msg_L}</div></div></div></div>'
            st.markdown(html_content, unsafe_allow_html=True)
        else:
            emoji_L = suggestion_L['emoji']
            sugg_msg_L = suggestion_L['message']
            html_content = f'<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 24px; border-radius: 12px; text-align: center;"><div style="font-size: 16px; color: white; font-weight: 700; margin-bottom: 12px;">💪 Left Arm</div><div style="font-size: 40px; margin: 16px 0;">{emoji_L}</div><div style="font-size: 13px; color: white; font-weight: 600;">{sugg_msg_L}</div></div>'
            st.markdown(html_content, unsafe_allow_html=True)
    
    with col_info_R:
        if last_workout_R:
            weight_R_kg = last_workout_R['weight']
            rpe_R_val = last_workout_R['rpe']
            emoji_R = suggestion_R['emoji']
            sugg_title_R = suggestion_R['suggestion']
            sugg_msg_R = suggestion_R['message']
            
            html_content = f'<div style="background: linear-gradient(135deg, #d946b5 0%, #e23670 100%); padding: 20px; border-radius: 12px;"><div style="font-size: 16px; color: white; font-weight: 700; margin-bottom: 12px;">💪 Right Arm</div><div style="background: rgba(0,0,0,0.2); padding: 14px; border-radius: 8px; margin-bottom: 12px;"><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;"><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase;">WEIGHT</div><div style="font-size: 24px; color: white; font-weight: 700;">{weight_R_kg:.1f} kg</div></div><div><div style="font-size: 11px; color: rgba(255,255,255,0.85); text-transform: uppercase;">RPE</div><div style="font-size: 24px; color: white; font-weight: 700;">{rpe_R_val}/10</div></div></div></div><div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px;"><div style="font-size: 24px;">{emoji_R}</div><div><div style="font-size: 14px; font-weight: 700; color: white; margin-bottom: 3px;">{sugg_title_R}</div><div style="font-size: 11px; color: rgba(255,255,255,0.95);">{sugg_msg_R}</div></div></div></div>'
            st.markdown(html_content, unsafe_allow_html=True)
        else:
            emoji_R = suggestion_R['emoji']
            sugg_msg_R = suggestion_R['message']
            html_content = f'<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 24px; border-radius: 12px; text-align: center;"><div style="font-size: 16px; color: white; font-weight: 700; margin-bottom: 12px;">💪 Right Arm</div><div style="font-size: 40px; margin: 16px 0;">{emoji_R}</div><div style="font-size: 13px; color: white; font-weight: 600;">{sugg_msg_R}</div></div>'
            st.markdown(html_content, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show endurance banner if applicable
    if is_endurance:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
            padding: 16px; border-radius: 10px; margin-bottom: 16px; border: 2px solid rgba(255,255,255,0.2);'>
                <div style='text-align: center;'>
                    <div style='font-size: 28px; margin-bottom: 6px;'>🏃</div>
                    <div style='font-size: 18px; color: white; font-weight: 700; margin-bottom: 6px;'>
                        ENDURANCE SESSION - REPEATERS
                    </div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.95);'>
                        55% max load • 7s on, 3s off • 6 lifts per set
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Set target percentage
    if is_endurance:
        target_pct = 55
        suggested_load_L_kg = current_1rm_L * 0.55
        suggested_load_R_kg = current_1rm_R * 0.55
    else:
        target_pct = 80
        if last_workout_L and suggestion_L.get('weight_change', 0) != 0:
            suggested_load_L_kg = last_workout_L['weight'] + suggestion_L['weight_change']
        else:
            suggested_load_L_kg = current_1rm_L * 0.8
        
        if last_workout_R and suggestion_R.get('weight_change', 0) != 0:
            suggested_load_R_kg = last_workout_R['weight'] + suggestion_R['weight_change']
        else:
            suggested_load_R_kg = current_1rm_R * 0.8
    
    # Weight input
    st.markdown("### ⚖️ Actual Weight Lifted (kg)")
    use_same_weight = st.checkbox("Same workout for both arms", value=True, key="modal_same_weight")
    
    if use_same_weight:
        actual_load_both = st.number_input(
            "Weight (kg) - Both Arms:",
            min_value=0.0,
            max_value=200.0,
            value=(suggested_load_L_kg + suggested_load_R_kg) / 2,
            step=0.25,
            key="modal_load_both"
        )
        actual_load_L = actual_load_both
        actual_load_R = actual_load_both
    else:
        col_L, col_R = st.columns(2)
        with col_L:
            actual_load_L = st.number_input(
                "Left (kg):",
                min_value=0.0,
                max_value=200.0,
                value=suggested_load_L_kg,
                step=0.25,
                key="modal_load_L"
            )
        with col_R:
            actual_load_R = st.number_input(
                "Right (kg):",
                min_value=0.0,
                max_value=200.0,
                value=suggested_load_R_kg,
                step=0.25,
                key="modal_load_R"
            )
    
    st.markdown("---")
    
    # Workout details
    st.markdown("### 📊 Workout Details")
    
    # Get defaults
    if is_endurance:
        default_reps_L = 6
        default_reps_R = 6
        default_sets_L = 3
        default_sets_R = 3
        default_rpe_L = 7
        default_rpe_R = 7
    else:
        default_reps_L = last_workout_L['reps'] if last_workout_L else 5
        default_reps_R = last_workout_R['reps'] if last_workout_R else 5
        default_sets_L = last_workout_L['sets'] if last_workout_L else 3
        default_sets_R = last_workout_R['sets'] if last_workout_R else 3
        default_rpe_L = last_workout_L['rpe'] if last_workout_L else 7
        default_rpe_R = last_workout_R['rpe'] if last_workout_R else 7
    
    if use_same_weight:
        col_reps, col_sets, col_rpe = st.columns(3)
        
        with col_reps:
            max_reps = 20 if is_endurance else 15
            reps_per_set = st.number_input("Reps per Set", min_value=1, max_value=max_reps, value=default_reps_L, step=1, key="modal_reps")
            reps_per_set_L = reps_per_set
            reps_per_set_R = reps_per_set
        
        with col_sets:
            sets_completed = st.number_input("Sets", min_value=1, max_value=10, value=default_sets_L, step=1, key="modal_sets")
            sets_completed_L = sets_completed
            sets_completed_R = sets_completed
        
        with col_rpe:
            rpe = st.slider("RPE (1-10)", min_value=1, max_value=10, value=default_rpe_L, step=1, key="modal_rpe")
            rpe_L = rpe
            rpe_R = rpe
    else:
        st.markdown("#### Left Arm")
        col_reps_L, col_sets_L, col_rpe_L = st.columns(3)
        
        with col_reps_L:
            max_reps_L = 20 if is_endurance else 15
            reps_per_set_L = st.number_input("Reps", min_value=1, max_value=max_reps_L, value=default_reps_L, step=1, key="modal_reps_L")
        
        with col_sets_L:
            sets_completed_L = st.number_input("Sets", min_value=1, max_value=10, value=default_sets_L, step=1, key="modal_sets_L")
        
        with col_rpe_L:
            rpe_L = st.slider("RPE", min_value=1, max_value=10, value=default_rpe_L, step=1, key="modal_rpe_L")
        
        st.markdown("#### Right Arm")
        col_reps_R, col_sets_R, col_rpe_R = st.columns(3)
        
        with col_reps_R:
            max_reps_R = 20 if is_endurance else 15
            reps_per_set_R = st.number_input("Reps", min_value=1, max_value=max_reps_R, value=default_reps_R, step=1, key="modal_reps_R")
        
        with col_sets_R:
            sets_completed_R = st.number_input("Sets", min_value=1, max_value=10, value=default_sets_R, step=1, key="modal_sets_R")
        
        with col_rpe_R:
            rpe_R = st.slider("RPE", min_value=1, max_value=10, value=default_rpe_R, step=1, key="modal_rpe_R")
    
    st.markdown("---")
    
    # Notes
    st.markdown("### 📝 Session Notes")
    notes = st.text_area(
        "How did it feel?",
        placeholder="e.g., Felt strong today...",
        key="modal_notes"
    )
    
    # Quick tags
    if 'modal_quick_note' not in st.session_state:
        st.session_state.modal_quick_note = ""
    
    st.markdown("**Quick Tags:**")
    quick_cols = st.columns(len(QUICK_NOTES))
    for idx, (emoji_label, note_text) in enumerate(QUICK_NOTES.items()):
        if quick_cols[idx].button(emoji_label, key=f"modal_quick_{note_text}"):
            if st.session_state.modal_quick_note:
                st.session_state.modal_quick_note += f" {note_text}"
            else:
                st.session_state.modal_quick_note = note_text
            st.rerun()
    
    final_notes = (notes + " " + st.session_state.modal_quick_note).strip() if st.session_state.modal_quick_note else notes
    
    # Add endurance marker to notes if it's an endurance session
    if is_endurance:
        if final_notes:
            final_notes = f"[ENDURANCE] {final_notes}"
        else:
            final_notes = "[ENDURANCE]"
    
    if st.session_state.modal_quick_note or is_endurance:
        st.info(f"📌 {final_notes}")
        if st.button("🗑️ Clear tags", key="modal_clear_tags"):
            st.session_state.modal_quick_note = ""
            st.rerun()
    
    st.markdown("---")
    
    # Submit button
    col_cancel, col_submit = st.columns([1, 2])
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_standard_modal = False
            st.session_state.modal_quick_note = ""
            st.rerun()
    
    with col_submit:
        if st.button("✅ Log Workout", type="primary", use_container_width=True, key="modal_submit"):
            workout_data_L = {
                "User": selected_user,
                "Date": workout_date.strftime("%Y-%m-%d"),
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
                "Date": workout_date.strftime("%Y-%m-%d"),
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
            
            success_L = save_workout_to_sheets( workout_data_L)
            success_R = save_workout_to_sheets( workout_data_R)
            
            if success_L and success_R:
                if get_endurance_training_enabled(selected_user):
                    increment_workout_count(selected_user, exercise)
                
                st.session_state.modal_quick_note = ""
                
                st.success("✅ Workout logged successfully!")
                st.balloons()
                time.sleep(1.5)
                st.session_state.show_standard_modal = False
                st.rerun()
            else:
                st.error("❌ Failed to save workout. Please try again.")

# ==================== MODAL: CUSTOM WORKOUT ====================
@st.dialog("✨ Log Custom Workout", width="large")
def show_custom_workout_modal():
    # Date picker
    workout_date = st.date_input(
        "📅 Workout Date:",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        help="Select a past date if you forgot to log a workout",
        key="modal_custom_date"
    )
    
    # Load user's custom workouts
    user_workouts = get_user_custom_workouts(selected_user)
    
    if user_workouts.empty:
        st.warning("You haven't created any custom workouts yet!")
        st.info("Go to the Custom Workouts page to create your first workout template.")
        if st.button("🏋️ Go to Custom Workouts", use_container_width=True):
            st.session_state.show_custom_modal = False
            st.switch_page("pages/6_Custom_Workouts.py")
        if st.button("❌ Close", use_container_width=True):
            st.session_state.show_custom_modal = False
            st.rerun()
        return
    
    # Dropdown to select workout
    workout_names = user_workouts['WorkoutName'].tolist()
    selected_workout_name = st.selectbox(
        "Choose a workout:",
        workout_names,
        key="modal_custom_workout_select"
    )
    
    # Get workout details
    workout_details = user_workouts[user_workouts['WorkoutName'] == selected_workout_name].iloc[0]
    
    # Display workout info
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 18px; border-radius: 10px; margin: 16px 0;'>
            <div style='font-size: 18px; font-weight: 700; color: white; margin-bottom: 6px;'>
                🏋️ {selected_workout_name}
            </div>
            <div style='font-size: 13px; color: rgba(255,255,255,0.9);'>
                Type: {workout_details['WorkoutType']} | {workout_details.get('Description', '')}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 Enter Workout Data")
    
    # Create dynamic form
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
                key="modal_custom_weight"
            )
        
        if workout_details.get('TracksSets', False):
            workout_sets = st.number_input(
                "Sets",
                min_value=1,
                max_value=20,
                value=3,
                step=1,
                key="modal_custom_sets"
            )
    
    with col2:
        if workout_details.get('TracksReps', False):
            workout_reps = st.number_input(
                "Reps",
                min_value=1,
                max_value=100,
                value=10,
                step=1,
                key="modal_custom_reps"
            )
        
        if workout_details.get('TracksDuration', False):
            workout_duration = st.number_input(
                "Duration (min)",
                min_value=1,
                max_value=600,
                value=30,
                step=1,
                key="modal_custom_duration"
            )
    
    with col3:
        if workout_details.get('TracksDistance', False):
            workout_distance = st.number_input(
                "Distance (km)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="modal_custom_distance"
            )
        
        if workout_details.get('TracksRPE', False):
            workout_rpe = st.slider(
                "RPE (1-10)",
                min_value=1,
                max_value=10,
                value=7,
                step=1,
                key="modal_custom_rpe"
            )
    
    st.markdown("---")
    
    # Notes
    custom_notes = st.text_area(
        "Session notes (optional):",
        placeholder="How did it feel?",
        key="modal_custom_notes"
    )
    
    st.markdown("---")
    
    # Submit buttons
    col_cancel, col_submit = st.columns([1, 2])
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True, key="modal_custom_cancel"):
            st.session_state.show_custom_modal = False
            st.rerun()
    
    with col_submit:
        if st.button("✅ Log Custom Workout", type="primary", use_container_width=True, key="modal_custom_submit"):
            success = log_custom_workout(
                user=selected_user,
                workout_id=workout_details['WorkoutID'],
                workout_name=selected_workout_name,
                date=datetime.combine(workout_date, datetime.min.time()),
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
                time.sleep(1.5)
                st.session_state.show_custom_modal = False
                st.rerun()
            else:
                st.error("❌ Failed to log workout. Please try again.")

# ==================== MODAL: OTHER ACTIVITIES ====================
@st.dialog("🗓️ Log Activity", width="large")
def show_activity_modal():
    # Date picker
    workout_date = st.date_input(
        "📅 Workout Date:",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        help="Select a past date if you forgot to log a workout",
        key="modal_activity_date"
    )
    
    st.markdown("### Choose Activity Type")
    
    col1, col2, col3 = st.columns(3)
    
    if 'selected_activity_type' not in st.session_state:
        st.session_state.selected_activity_type = "Climbing"
    
    with col1:
        if st.button("🧗 Climbing", use_container_width=True, type="primary" if st.session_state.selected_activity_type == "Climbing" else "secondary", key="modal_act_climb"):
            st.session_state.selected_activity_type = "Climbing"
            st.rerun()
    
    with col2:
        if st.button("🎯 Board", use_container_width=True, type="primary" if st.session_state.selected_activity_type == "Board" else "secondary", key="modal_act_board"):
            st.session_state.selected_activity_type = "Board"
            st.rerun()
    
    with col3:
        if st.button("💪 Work Pullups", use_container_width=True, type="primary" if st.session_state.selected_activity_type == "Work" else "secondary", key="modal_act_work"):
            st.session_state.selected_activity_type = "Work"
            st.rerun()
    
    st.markdown("---")
    
    activity_type = st.session_state.selected_activity_type
    
    # Use workout_date from the date picker above
    activity_date = workout_date
    
    # Duration (except for work pullups)
    activity_duration = None
    if activity_type != "Work":
        default_duration = 90 if activity_type == "Board" else 60
        activity_duration = st.number_input(
            "Duration (minutes):",
            min_value=5,
            max_value=480,
            value=default_duration,
            step=5,
            key="modal_activity_duration"
        )
    
    # Notes
    activity_notes = st.text_area(
        "Session notes (optional):",
        placeholder=f"e.g., {'Kilter board projecting' if activity_type == 'Board' else 'Felt strong today'}...",
        key="modal_activity_notes"
    )
    
    st.markdown("---")
    
    # Submit buttons
    col_cancel, col_submit = st.columns([1, 2])
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True, key="modal_activity_cancel"):
            st.session_state.show_activity_modal = False
            st.rerun()
    
    with col_submit:
        if st.button(f"✅ Log {activity_type}", type="primary", use_container_width=True, key="modal_activity_submit"):
            if log_activity_to_sheets(selected_user, activity_type, activity_duration, activity_notes, activity_date):
                duration_text = f" ({activity_duration} min)" if activity_duration else ""
                st.success(f"✅ {activity_type} session logged for {activity_date.strftime('%Y-%m-%d')}!{duration_text}")
                st.balloons()
                time.sleep(1.5)
                st.session_state.show_activity_modal = False
                st.rerun()
            else:
                st.error(f"❌ Failed to log {activity_type} session.")

# ==================== MODAL: 1RM UPDATE ====================
@st.dialog("🏆 Update 1RM", width="large")
def show_1rm_modal():
    # Date picker
    workout_date = st.date_input(
        "📅 Test Date:",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        help="Select a past date if you forgot to log a test",
        key="modal_1rm_date"
    )
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
        padding: 18px; border-radius: 10px; text-align: center; margin-bottom: 16px;'>
            <div style='font-size: 28px; margin-bottom: 8px;'>🏆</div>
            <div style='font-size: 20px; font-weight: bold; color: white;'>Update Your 1RM</div>
            <div style='font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 4px;'>
                Test your max strength and update your training targets
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Select Exercise to Test")
    test_exercise = st.selectbox(
        "",
        ["20mm Edge", "Pinch", "Wrist Roller"],
        key="modal_test_exercise_select",
        label_visibility="collapsed"
    )
    
    current_1rm_L_test = get_user_1rm(selected_user, test_exercise, "L")
    current_1rm_R_test = get_user_1rm(selected_user, test_exercise, "R")
    
    st.markdown("---")
    st.markdown("### 📊 Current 1RMs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
            padding: 20px; border-radius: 10px; text-align: center;'>
                <div style='font-size: 14px; color: #555; margin-bottom: 6px;'>Left Arm (Current)</div>
                <div style='font-size: 32px; font-weight: bold; color: #333;'>{current_1rm_L_test:.1f} kg</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
            padding: 20px; border-radius: 10px; text-align: center;'>
                <div style='font-size: 14px; color: #555; margin-bottom: 6px;'>Right Arm (Current)</div>
                <div style='font-size: 32px; font-weight: bold; color: #333;'>{current_1rm_R_test:.1f} kg</div>
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
            key="modal_new_1rm_L"
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
            key="modal_new_1rm_R"
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
        key="modal_test_notes"
    )
    
    st.markdown("---")
    
    # Submit buttons
    col_cancel, col_submit = st.columns([1, 2])
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True, key="modal_1rm_cancel"):
            st.session_state.show_1rm_modal = False
            st.rerun()
    
    with col_submit:
        if st.button("🏆 Update 1RMs", type="primary", use_container_width=True, key="modal_1rm_submit"):
            # Update 1RMs in Supabase via set_user_1rm
            success_L = set_user_1rm(selected_user, test_exercise, "L", new_1rm_L)
            success_R = set_user_1rm(selected_user, test_exercise, "R", new_1rm_R)
            
            if not success_L or not success_R:
                failed_arms = []
                if not success_L:
                    failed_arms.append("Left")
                if not success_R:
                    failed_arms.append("Right")
                st.error(f"❌ Failed to update 1RM for {' and '.join(failed_arms)} arm(s). Check the terminal for details.")
            elif success_L and success_R:
                if log_test_as_workout:
                    workout_data_L = {
                        "User": selected_user,
                        "Date": workout_date.strftime("%Y-%m-%d"),
                        "Exercise": f"1RM Test - {test_exercise}",
                        "Arm": "L",
                        "Actual_Load_kg": new_1rm_L,
                        "Reps_Per_Set": 1,
                        "Sets_Completed": 1,
                        "Notes": test_notes if test_notes else ""
                    }
                    
                    workout_data_R = {
                        "User": selected_user,
                        "Date": workout_date.strftime("%Y-%m-%d"),
                        "Exercise": f"1RM Test - {test_exercise}",
                        "Arm": "R",
                        "Actual_Load_kg": new_1rm_R,
                        "Reps_Per_Set": 1,
                        "Sets_Completed": 1,
                        "Notes": test_notes if test_notes else ""
                    }
                    
                    workout_success_L = save_workout_to_sheets(workout_data_L)
                    workout_success_R = save_workout_to_sheets(workout_data_R)
                    
                    if not workout_success_L or not workout_success_R:
                        st.warning("⚠️ 1RMs updated but failed to log as workout. Check terminal for details.")
                
                st.success("✅ 1RMs updated successfully!")
                st.balloons()
                time.sleep(1.5)
                st.session_state.show_1rm_modal = False
                st.rerun()

# Show appropriate modal (only one at a time)
if st.session_state.show_standard_modal:
    show_standard_workout_modal()
elif st.session_state.show_custom_modal:
    show_custom_workout_modal()
elif st.session_state.show_activity_modal:
    show_activity_modal()
elif st.session_state.show_1rm_modal:
    show_1rm_modal()

# ==================== WEIGHT RECOMMENDATIONS ====================
st.markdown("---")
st.markdown("## 💡 Recommended Weights for Next Session")

# Check if endurance mode is enabled and determine next workout type
endurance_enabled = get_endurance_training_enabled(selected_user)
workout_count_edge = get_workout_count(selected_user, "20mm Edge")
is_next_endurance = endurance_enabled and (workout_count_edge % 3) == 2

# Display info banner
if endurance_enabled and is_next_endurance:
    st.info("🏃 **Next Edge session is Endurance** - Use 55% of max (repeaters protocol)")
elif endurance_enabled:
    st.info(f"💪 **Next Edge session is Strength** - Use 80% of max (session {(workout_count_edge % 3) + 1}/3)")

# Load recent workout data for the user
df_recent = load_data_from_sheets(None, selected_user)

# Determine which accessory exercise is next (Pinch or Wrist Roller alternate)
next_accessory = "Pinch"  # Default
if not df_recent.empty:
    df_accessory = df_recent[df_recent['Exercise'].isin(["Pinch", "Wrist Roller"])].copy()
    if len(df_accessory) > 0:
        df_accessory['Date'] = pd.to_datetime(df_accessory['Date'], errors='coerce')
        last_accessory_row = df_accessory.sort_values('Date').iloc[-1]
        last_accessory = last_accessory_row['Exercise']
        next_accessory = "Wrist Roller" if last_accessory == "Pinch" else "Pinch"

if not df_recent.empty:
    # Filter for standard exercises only (not 1RM tests)
    df_recent = df_recent[~df_recent['Exercise'].str.contains('1RM Test', na=False)]
    
    # Reorganize exercises: Pinch, Edge (middle), Wrist Roller
    exercises_to_check = ["Pinch", "20mm Edge", "Wrist Roller"]
    
    # Create columns for each exercise
    cols = st.columns(len(exercises_to_check))
    
    for idx, exercise in enumerate(exercises_to_check):
        with cols[idx]:
            # Determine if this card should be lifted (for next accessory)
            is_next = exercise == next_accessory
            is_edge = exercise == "20mm Edge"
            
            # Add top margin to lower non-next accessories, Edge stays at top level
            if is_edge or is_next:
                top_margin = "0px"
                scale = "1.0"
                shadow = "0 8px 32px rgba(0,0,0,0.4)"
            else:
                top_margin = "40px"
                scale = "0.95"
                shadow = "0 4px 15px rgba(0,0,0,0.2)"
            
            # Get workouts for this exercise
            df_ex = df_recent[df_recent['Exercise'] == exercise].copy()
            
            if not df_ex.empty:
                df_ex['Date'] = pd.to_datetime(df_ex['Date'], errors='coerce')
                
                # Determine if this is the exercise affected by endurance mode
                is_edge_exercise = exercise == "20mm Edge"
                show_endurance_weights = is_edge_exercise and is_next_endurance
                
                # Filter to get the right type of workout (strength or endurance)
                if is_edge_exercise and 'Notes' in df_ex.columns:
                    df_ex['is_endurance'] = df_ex['Notes'].fillna('').astype(str).str.lower().str.contains('endurance|repeater')
                    
                    if show_endurance_weights:
                        # Next is endurance, find last endurance session
                        df_filtered = df_ex[df_ex['is_endurance']].copy()
                        if df_filtered.empty:
                            # No endurance sessions yet, calculate from last strength session
                            df_filtered = df_ex[~df_ex['is_endurance']].copy()
                            use_multiplier = True
                        else:
                            use_multiplier = False
                    else:
                        # Next is strength, find last strength session
                        df_filtered = df_ex[~df_ex['is_endurance']].copy()
                        use_multiplier = False
                else:
                    df_filtered = df_ex.copy()
                    use_multiplier = False
                
                if not df_filtered.empty:
                    df_filtered = df_filtered.sort_values('Date', ascending=False)
                    
                    # Get most recent load and notes for each arm
                    df_L = df_filtered[df_filtered['Arm'] == 'L']
                    df_R = df_filtered[df_filtered['Arm'] == 'R']
                    
                    recent_L = df_L['Actual_Load_kg'].iloc[0] if not df_L.empty else 0
                    recent_R = df_R['Actual_Load_kg'].iloc[0] if not df_R.empty else 0
                    
                    # Get notes from the most recent workout (use whichever arm has the most recent entry)
                    last_notes = ""
                    last_rpe = None
                    if not df_filtered.empty and 'Notes' in df_filtered.columns:
                        last_notes_raw = df_filtered['Notes'].iloc[0]
                        if pd.notna(last_notes_raw) and last_notes_raw:
                            # Clean up the notes (remove [ENDURANCE] marker if present)
                            last_notes = str(last_notes_raw).strip()
                            last_notes = last_notes.replace('[ENDURANCE]', '').replace('[endurance]', '').strip()
                    
                    # Get RPE from the most recent workout
                    if not df_filtered.empty and 'RPE' in df_filtered.columns:
                        last_rpe_raw = df_filtered['RPE'].iloc[0]
                        if pd.notna(last_rpe_raw):
                            last_rpe = last_rpe_raw
                    
                    # Calculate weights to display
                    if use_multiplier:
                        # Calculate endurance from strength weight
                        endurance_multiplier = 55.0 / 80.0
                        display_L = recent_L * endurance_multiplier if recent_L > 0 else 0
                        display_R = recent_R * endurance_multiplier if recent_R > 0 else 0
                    else:
                        display_L = recent_L
                        display_R = recent_R
                else:
                    display_L = 0
                    display_R = 0
                    recent_L = 0
                    recent_R = 0
                
                # Choose styling based on exercise and workout type
                if exercise == "20mm Edge":
                    if show_endurance_weights:
                        gradient = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                        icon = "🏃"
                        workout_label = "Endurance"
                    else:
                        gradient = "linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%)"
                        icon = "💪"
                        workout_label = "Strength"
                elif exercise == "Pinch":
                    # Highlight if this is the next accessory exercise
                    if exercise == next_accessory:
                        gradient = "linear-gradient(135deg, #e1306c 0%, #f77737 100%)"
                        icon = "✊"
                        workout_label = "← Next"
                    else:
                        gradient = "linear-gradient(135deg, rgba(225,48,108,0.4) 0%, rgba(247,87,119,0.4) 100%)"
                        icon = "✊"
                        workout_label = ""
                else:  # Wrist Roller
                    # Highlight if this is the next accessory exercise
                    if exercise == next_accessory:
                        gradient = "linear-gradient(135deg, #a8e063 0%, #56ab2f 100%)"
                        icon = "🌀"
                        workout_label = "← Next"
                    else:
                        gradient = "linear-gradient(135deg, rgba(168,224,99,0.4) 0%, rgba(86,171,47,0.4) 100%)"
                        icon = "🌀"
                        workout_label = ""
                
                # Display card with cleaner design
                if display_L > 0 or display_R > 0:
                    # Build RPE section (shown inline with weights)
                    rpe_section = ""
                    if last_rpe is not None:
                        rpe_section = (
                            f"<div style='display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.2);'>" +
                            f"<span style='color: rgba(255,255,255,0.9); font-size: 14px; font-weight: 600;'>💪 RPE</span>" +
                            f"<span style='color: white; font-weight: 700; font-size: 24px;'>{last_rpe}/10</span>" +
                            f"</div>"
                        )
                    
                    # Build notes section (separate from RPE)
                    notes_section = ""
                    if last_notes:
                        notes_section = (
                            f"<div style='margin-top: 12px; padding: 10px 12px; background: rgba(255,255,255,0.15); "
                            f"border-radius: 8px; border-left: 3px solid rgba(255,255,255,0.5);'>" +
                            f"<div style='font-size: 11px; color: rgba(255,255,255,0.8); margin-bottom: 4px; "
                            f"font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Last Note</div>" +
                            f"<div style='font-size: 13px; color: white; font-style: italic;'>\"{last_notes}\"</div>" +
                            f"</div>"
                        )
                    else:
                        # Show "no note left" if there are no notes
                        notes_section = (
                            f"<div style='margin-top: 12px; padding: 8px 12px; background: rgba(255,255,255,0.08); "
                            f"border-radius: 8px;'>" +
                            f"<div style='font-size: 11px; color: rgba(255,255,255,0.6); text-align: center; "
                            f"font-style: italic;'>No note left</div>" +
                            f"</div>"
                        )
                    
                    st.markdown(
                        f"<div style='background: {gradient}; padding: 24px 20px; border-radius: 16px; "
                        f"box-shadow: {shadow}; border: 1px solid rgba(255,255,255,0.1); "
                        f"margin-top: {top_margin}; transform: scale({scale}); transition: all 0.3s ease;'>" +
                        f"<div style='text-align: center; margin-bottom: 16px;'>" +
                        f"<div style='font-size: 32px; margin-bottom: 8px;'>{icon}</div>" +
                        f"<div style='font-size: 18px; color: white; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.3);'>{exercise}</div>" +
                        (f"<div style='font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 4px;'>{workout_label}</div>" if workout_label else "") +
                        f"</div>" +
                        f"<div style='background: rgba(0,0,0,0.25); padding: 16px; border-radius: 12px;'>" +
                        f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>" +
                        f"<span style='color: rgba(255,255,255,0.9); font-size: 14px; font-weight: 600;'>👈 Left</span>" +
                        f"<span style='color: white; font-weight: 700; font-size: 24px;'>{display_L:.1f} kg</span>" +
                        f"</div>" +
                        f"<div style='display: flex; justify-content: space-between; align-items: center;'>" +
                        f"<span style='color: rgba(255,255,255,0.9); font-size: 14px; font-weight: 600;'>👉 Right</span>" +
                        f"<span style='color: white; font-weight: 700; font-size: 24px;'>{display_R:.1f} kg</span>" +
                        f"</div>" +
                        rpe_section +
                        f"</div>" +
                        notes_section +
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                # No data for this exercise yet
                gradient = "linear-gradient(135deg, #4a5568 0%, #2d3748 100%)"
                st.markdown(f"""
                    <div style='background: {gradient}; 
                    padding: 20px; border-radius: 12px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255,255,255,0.1);'>
                        <div style='font-size: 16px; color: white; font-weight: 700; 
                        text-align: center; margin-bottom: 12px; text-shadow: 0 1px 3px rgba(0,0,0,0.3);'>
                            {exercise}
                        </div>
                        <div style='background: rgba(0,0,0,0.2); padding: 20px; border-radius: 8px; text-align: center;'>
                            <span style='color: rgba(255,255,255,0.6); font-size: 13px;'>
                                No data yet
                            </span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Add explanation
    if is_next_endurance:
        st.info("🏃 **Next session is Endurance**: Use lighter loads (55% of max) for the 20mm Edge repeaters protocol")
    else:
        st.caption("💡 These weights are based on your most recent logged sessions (assuming 80% of 1RM for strength training)")
else:
    st.info("📊 Log your first workout to see weight recommendations!")

