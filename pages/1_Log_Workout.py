import streamlit as st
import sys
sys.path.append('.')
from utils.helpers import *
from datetime import datetime

st.set_page_config(page_title="Log Workout", page_icon="📝", layout="wide")

init_session_state()

# ==================== HEADER ====================
st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    padding: 30px 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(102,126,234,0.4);'>
        <h1 style='color: white; font-size: 42px; margin: 0;'>📝 Log Workout</h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 8px;'>
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
else:
    available_users = USER_LIST.copy()

# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    available_users,
    index=available_users.index(st.session_state.current_user) if st.session_state.current_user in available_users else 0,
    key="user_selector_log"
)

selected_user = st.session_state.current_user

# Bodyweight input
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Bodyweight")
current_bw = get_bodyweight(spreadsheet, selected_user) if spreadsheet else 78.0
new_bw = st.sidebar.number_input(
    "Your bodyweight (kg):",
    min_value=40.0,
    max_value=150.0,
    value=current_bw,
    step=0.5,
    key="bodyweight_input"
)

if new_bw != current_bw and spreadsheet:
    set_bodyweight(spreadsheet, selected_user, new_bw)
    st.sidebar.success(f"✅ Bodyweight updated to {new_bw}kg")

# Check if connected before showing tabs
if not spreadsheet:
    st.error("❌ Could not connect to Google Sheets. Please check your configuration.")
else:
    # TABS FOR WORKOUT vs 1RM TEST
    tab1, tab2 = st.tabs(["💪 Log Training Session", "🏆 Update 1RM"])
    
    # ==================== TAB 1: REGULAR WORKOUT ====================
    with tab1:
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
        
        # Get stored baseline for comparison
        stored_1rm_L = get_user_1rm(spreadsheet, selected_user, exercise, "L")
        stored_1rm_R = get_user_1rm(spreadsheet, selected_user, exercise, "R")
        
        st.markdown("---")
        
        # Show working max with indicator
        st.markdown("### 💪 Your Current Strength")
        st.caption("📊 Auto-updated based on recent performance (last 8 weeks)")
        
        col_info_L, col_info_R = st.columns(2)
        
        with col_info_L:
            # Indicator if estimated > stored
            if current_1rm_L > stored_1rm_L + 1:
                indicator = f'<div style="font-size: 11px; color: #4ade80; margin-top: 3px;">📈 +{current_1rm_L - stored_1rm_L:.1f}kg from baseline</div>'
            else:
                indicator = f'<div style="font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 3px;">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(79,172,254,0.3);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>💪 Left Arm</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{current_1rm_L:.1f} kg</div>
                    {indicator}
                </div>
            """, unsafe_allow_html=True)
        
        with col_info_R:
            # Indicator if estimated > stored
            if current_1rm_R > stored_1rm_R + 1:
                indicator = f'<div style="font-size: 11px; color: #4ade80; margin-top: 3px;">📈 +{current_1rm_R - stored_1rm_R:.1f}kg from baseline</div>'
            else:
                indicator = f'<div style="font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 3px;">✓ From test</div>'
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(240,147,251,0.3);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>💪 Right Arm</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{current_1rm_R:.1f} kg</div>
                    {indicator}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Training Intensity
        st.markdown("### 🎚️ Training Intensity")
        target_pct = st.slider(
            "Target % of 1RM:",
            min_value=50,
            max_value=100,
            value=80,
            step=5,
            key="target_pct_slider",
            help="Lower % = more reps, higher % = heavier weight"
        )
        
        # Intensity indicator
        if target_pct >= 90:
            intensity_color = "#ef4444"
            intensity_label = "MAX EFFORT"
        elif target_pct >= 80:
            intensity_color = "#f59e0b"
            intensity_label = "HEAVY"
        elif target_pct >= 70:
            intensity_color = "#10b981"
            intensity_label = "MODERATE"
        else:
            intensity_color = "#3b82f6"
            intensity_label = "LIGHT"
        
        st.markdown(f"""
            <div style='background: {intensity_color}; padding: 10px 20px; border-radius: 8px; 
            text-align: center; color: white; font-weight: bold; margin-bottom: 15px;'>
                {intensity_label} - {target_pct}% Intensity
            </div>
        """, unsafe_allow_html=True)
        
        # Prescribed loads
        prescribed_load_L = current_1rm_L * (target_pct / 100)
        prescribed_load_R = current_1rm_R * (target_pct / 100)
        
        st.markdown("### 🎯 Prescribed Loads")
        col_prescribed_L, col_prescribed_R = st.columns(2)
        
        with col_prescribed_L:
            st.markdown(f"""
                <div style='background: rgba(79,172,254,0.15); border-left: 4px solid #4facfe; padding: 15px; border-radius: 8px;'>
                    <div style='font-size: 12px; color: #888; margin-bottom: 5px;'>Left (Prescribed)</div>
                    <div style='font-size: 28px; font-weight: bold; color: #4facfe;'>{prescribed_load_L:.1f} kg</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_prescribed_R:
            st.markdown(f"""
                <div style='background: rgba(240,147,251,0.15); border-left: 4px solid #f093fb; padding: 15px; border-radius: 8px;'>
                    <div style='font-size: 12px; color: #888; margin-bottom: 5px;'>Right (Prescribed)</div>
                    <div style='font-size: 28px; font-weight: bold; color: #f093fb;'>{prescribed_load_R:.1f} kg</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Actual Weight Lifted
        st.markdown("### ⚖️ Actual Weight Lifted")
        use_same_weight = st.checkbox("Use same weight for both arms", value=True, key="same_weight_toggle")
        
        if use_same_weight:
            actual_load = st.number_input(
                "Weight Lifted (kg) - Both Arms:",
                min_value=0.0,
                max_value=200.0,
                value=(prescribed_load_L + prescribed_load_R) / 2,
                step=0.25,
                key="actual_load_both",
                help="Enter the weight you actually lifted"
            )
            actual_load_L = actual_load
            actual_load_R = actual_load
        else:
            col_L, col_R = st.columns(2)
            with col_L:
                actual_load_L = st.number_input(
                    "Left Arm Weight (kg):",
                    min_value=0.0,
                    max_value=200.0,
                    value=prescribed_load_L,
                    step=0.25,
                    key="actual_load_L"
                )
            with col_R:
                actual_load_R = st.number_input(
                    "Right Arm Weight (kg):",
                    min_value=0.0,
                    max_value=200.0,
                    value=prescribed_load_R,
                    step=0.25,
                    key="actual_load_R"
                )
        
        st.markdown("---")
        
        # Workout Details
        st.markdown("### 📊 Workout Details")
        col_reps, col_sets, col_rpe = st.columns(3)
        
        with col_reps:
            st.markdown("""
                <div style='text-align: center; padding: 10px; background: rgba(103,126,234,0.1); border-radius: 8px; margin-bottom: 10px;'>
                    <div style='font-size: 24px;'>🔢</div>
                    <div style='font-size: 12px; color: #888;'>Reps per Set</div>
                </div>
            """, unsafe_allow_html=True)
            reps_per_set = st.number_input("", min_value=1, max_value=20, value=5, step=1, key="reps_input", label_visibility="collapsed")
        
        with col_sets:
            st.markdown("""
                <div style='text-align: center; padding: 10px; background: rgba(240,147,251,0.1); border-radius: 8px; margin-bottom: 10px;'>
                    <div style='font-size: 24px;'>📚</div>
                    <div style='font-size: 12px; color: #888;'>Sets Completed</div>
                </div>
            """, unsafe_allow_html=True)
            sets_completed = st.number_input("", min_value=1, max_value=10, value=3, step=1, key="sets_input", label_visibility="collapsed")
        
        with col_rpe:
            st.markdown("""
                <div style='text-align: center; padding: 10px; background: rgba(250,112,154,0.1); border-radius: 8px; margin-bottom: 10px;'>
                    <div style='font-size: 24px;'>💥</div>
                    <div style='font-size: 12px; color: #888;'>RPE (1-10)</div>
                </div>
            """, unsafe_allow_html=True)
            rpe = st.slider("", min_value=1, max_value=10, value=7, step=1, key="rpe_slider", label_visibility="collapsed")
        
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
                "Prescribed_Load_kg": prescribed_load_L,
                "Actual_Load_kg": actual_load_L,
                "Reps_Per_Set": reps_per_set,
                "Sets_Completed": sets_completed,
                "RPE": rpe,
                "Notes": final_notes
            }
            
            workout_data_R = {
                "User": selected_user,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Exercise": exercise,
                "Arm": "R",
                "1RM_Reference": current_1rm_R,
                "Target_Percentage": target_pct,
                "Prescribed_Load_kg": prescribed_load_R,
                "Actual_Load_kg": actual_load_R,
                "Reps_Per_Set": reps_per_set,
                "Sets_Completed": sets_completed,
                "RPE": rpe,
                "Notes": final_notes
            }
            
            success_L = save_workout_to_sheets(workout_sheet, workout_data_L)
            success_R = save_workout_to_sheets(workout_sheet, workout_data_R)
            
            if success_L and success_R:
                st.session_state.quick_note_append = ""
                st.success("✅ Workout logged successfully for both arms!")
                st.balloons()
            else:
                st.error("❌ Failed to save workout. Please try again.")
    
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
                    <div style='font-size: 40px; font-weight: bold; color: #333;'>{current_1rm_L_test} kg</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                padding: 25px; border-radius: 12px; text-align: center;'>
                    <div style='font-size: 16px; color: #555; margin-bottom: 8px;'>Right Arm (Current)</div>
                    <div style='font-size: 40px; font-weight: bold; color: #333;'>{current_1rm_R_test} kg</div>
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
                st.success(f"🎉 New PR! +{new_1rm_L - current_1rm_L_test:.2f} kg")
            elif new_1rm_L < current_1rm_L_test:
                st.warning(f"⚠️ Lower than current (-{current_1rm_L_test - new_1rm_L:.2f} kg)")
        
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
                st.success(f"🎉 New PR! +{new_1rm_R - current_1rm_R_test:.2f} kg")
            elif new_1rm_R < current_1rm_R_test:
                st.warning(f"⚠️ Lower than current (-{current_1rm_R_test - new_1rm_R:.2f} kg)")
        
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
st.info("📌 Track climbing sessions and work pullups to see your full training calendar!")

tab_climb, tab_work = st.tabs(["🧗 Log Climbing Session", "💪 Log Work Pullups"])

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
