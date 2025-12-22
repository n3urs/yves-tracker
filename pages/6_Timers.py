import streamlit as st
import time

st.set_page_config(page_title="Rest Timer", page_icon="⏱️")

# Initialize session state
if 'timer_mode' not in st.session_state:
    st.session_state.timer_mode = 'Rest Timer'
if 'timer_state' not in st.session_state:
    st.session_state.timer_state = 'idle'
if 'time_remaining' not in st.session_state:
    st.session_state.time_remaining = 180
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
# Repeater-specific state
if 'repeater_phase' not in st.session_state:
    st.session_state.repeater_phase = 'ready'  # ready, right_on, right_off, switch, left_on, left_off, complete
if 'repeater_round' not in st.session_state:
    st.session_state.repeater_round = 0
if 'repeater_hand' not in st.session_state:
    st.session_state.repeater_hand = 'right'

st.title("⏱️ Workout Timer")

# Timer mode selector
timer_mode = st.selectbox(
    "Select Timer Mode:",
    ["Rest Timer", "Repeaters"],
    key="timer_mode_selector"
)

# Reset state if mode changes
if timer_mode != st.session_state.timer_mode:
    st.session_state.timer_mode = timer_mode
    st.session_state.timer_state = 'idle'
    st.session_state.time_remaining = 180 if timer_mode == 'Rest Timer' else 10
    st.session_state.start_time = None
    st.session_state.repeater_phase = 'ready'
    st.session_state.repeater_round = 0
    st.session_state.repeater_hand = 'right'
    st.rerun()

st.markdown("---")

# ==================== REST TIMER ====================
if timer_mode == 'Rest Timer':
    minutes = st.session_state.time_remaining // 60
    seconds = st.session_state.time_remaining % 60
    
    if st.session_state.timer_state == 'flashing':
        flash_color = "red" if int(time.time() * 2) % 2 == 0 else "white"
        st.markdown(f"""
            <div style='text-align: center; padding: 50px;'>
                <h1 style='font-size: 120px; color: {flash_color}; font-weight: bold;'>
                    {minutes:02d}:{seconds:02d}
                </h1>
                <p style='font-size: 24px; color: {flash_color};'>TIME'S UP! Click to reset</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Reset Timer", key="reset_flash", use_container_width=True):
            st.session_state.timer_state = 'idle'
            st.session_state.time_remaining = 180
            st.session_state.start_time = None
            st.rerun()
        
        time.sleep(0.5)
        st.rerun()
    else:
        st.markdown(f"""
            <div style='text-align: center; padding: 50px;'>
                <h1 style='font-size: 120px; color: white; font-weight: bold;'>
                    {minutes:02d}:{seconds:02d}
                </h1>
            </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.timer_state == 'idle':
            if st.button("▶️ Start Timer", key="start", use_container_width=True, type="primary"):
                st.session_state.timer_state = 'running'
                st.session_state.start_time = time.time()
                st.rerun()
        elif st.session_state.timer_state == 'running':
            if st.button("⏸️ Pause", key="pause", use_container_width=True):
                st.session_state.timer_state = 'idle'
                st.session_state.start_time = None
                st.rerun()
            if st.button("🔄 Reset", key="reset", use_container_width=True):
                st.session_state.timer_state = 'idle'
                st.session_state.time_remaining = 180
                st.session_state.start_time = None
                st.rerun()
    
    if st.session_state.timer_state == 'running':
        elapsed = time.time() - st.session_state.start_time
        st.session_state.time_remaining = max(0, 180 - int(elapsed))
        
        if st.session_state.time_remaining == 0:
            st.session_state.timer_state = 'flashing'
            st.session_state.start_time = None
        
        time.sleep(0.1)
        st.rerun()

# ==================== REPEATERS TIMER ====================
else:
    phase = st.session_state.repeater_phase
    round_num = st.session_state.repeater_round
    hand = st.session_state.repeater_hand
    
    # Determine current phase details
    phase_config = {
        'ready': {'duration': 10, 'label': '🟡 GET READY', 'color': 'yellow'},
        'right_on': {'duration': 7, 'label': '🟢 LIFT - RIGHT HAND', 'color': '#00ff00'},
        'right_off': {'duration': 3, 'label': '🔴 REST', 'color': 'red'},
        'switch': {'duration': 10, 'label': '🔄 SWITCH HANDS', 'color': 'orange'},
        'left_on': {'duration': 7, 'label': '🟢 LIFT - LEFT HAND', 'color': '#00ff00'},
        'left_off': {'duration': 3, 'label': '🔴 REST', 'color': 'red'},
        'complete': {'duration': 0, 'label': '✅ COMPLETE!', 'color': 'green'}
    }
    
    current_config = phase_config.get(phase, phase_config['ready'])
    
    if phase == 'complete':
        flash_color = "green" if int(time.time() * 2) % 2 == 0 else "white"
        st.markdown(f"""
            <div style='text-align: center; padding: 50px;'>
                <h1 style='font-size: 100px; color: {flash_color}; font-weight: bold;'>
                    ✅ COMPLETE!
                </h1>
                <p style='font-size: 24px; color: {flash_color};'>Great work! Click to reset</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Reset Timer", key="reset_complete", use_container_width=True):
            st.session_state.timer_state = 'idle'
            st.session_state.repeater_phase = 'ready'
            st.session_state.repeater_round = 0
            st.session_state.repeater_hand = 'right'
            st.session_state.time_remaining = 10
            st.session_state.start_time = None
            st.rerun()
        
        time.sleep(0.5)
        st.rerun()
    else:
        # Display current round info
        if phase in ['right_on', 'right_off']:
            hand_display = 'RIGHT HAND'
            round_display = round_num + 1
        elif phase in ['left_on', 'left_off']:
            hand_display = 'LEFT HAND'
            round_display = round_num + 1
        else:
            hand_display = ''
            round_display = ''
        
        if hand_display:
            # Check if this is the last rep
            is_last_rep = round_display == 6
            last_rep_banner = ""
            if is_last_rep and phase in ['right_on', 'left_on']:
                last_rep_banner = """
                    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 12px; border-radius: 8px; margin-bottom: 15px; 
                    box-shadow: 0 4px 12px rgba(240,147,251,0.5);'>
                        <div style='color: white; font-size: 18px; font-weight: 700; text-align: center;'>
                            🔥 LAST REP OF THIS HAND! 🔥
                        </div>
                    </div>
                """
            
            st.markdown(f"""
                <div style='text-align: center; margin-bottom: 20px;'>
                    {last_rep_banner}
                    <h2 style='color: #888; font-size: 24px;'>{hand_display} - Round {round_display}/6</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Display timer
        st.markdown(f"""
            <div style='text-align: center; padding: 30px;'>
                <h3 style='font-size: 40px; color: {current_config['color']}; font-weight: bold; margin-bottom: 20px;'>
                    {current_config['label']}
                </h3>
                <h1 style='font-size: 150px; color: white; font-weight: bold;'>
                    {st.session_state.time_remaining}
                </h1>
            </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.timer_state == 'idle' and phase != 'complete':
            if st.button("▶️ Start Repeaters", key="start_rep", use_container_width=True, type="primary"):
                st.session_state.timer_state = 'running'
                st.session_state.start_time = time.time()
                st.session_state.time_remaining = current_config['duration']
                st.rerun()
        elif st.session_state.timer_state == 'running':
            if st.button("🔄 Reset", key="reset_rep", use_container_width=True):
                st.session_state.timer_state = 'idle'
                st.session_state.repeater_phase = 'ready'
                st.session_state.repeater_round = 0
                st.session_state.repeater_hand = 'right'
                st.session_state.time_remaining = 10
                st.session_state.start_time = None
                st.rerun()
    
    # Update repeater timer logic
    if st.session_state.timer_state == 'running' and phase != 'complete':
        elapsed = time.time() - st.session_state.start_time
        st.session_state.time_remaining = max(0, current_config['duration'] - int(elapsed))
        
        # Phase transitions
        if st.session_state.time_remaining == 0:
            if phase == 'ready':
                st.session_state.repeater_phase = 'right_on'
                st.session_state.repeater_round = 0
            elif phase == 'right_on':
                st.session_state.repeater_phase = 'right_off'
            elif phase == 'right_off':
                st.session_state.repeater_round += 1
                if st.session_state.repeater_round < 6:
                    st.session_state.repeater_phase = 'right_on'
                else:
                    st.session_state.repeater_phase = 'switch'
                    st.session_state.repeater_round = 0
            elif phase == 'switch':
                st.session_state.repeater_phase = 'left_on'
            elif phase == 'left_on':
                st.session_state.repeater_phase = 'left_off'
            elif phase == 'left_off':
                st.session_state.repeater_round += 1
                if st.session_state.repeater_round < 6:
                    st.session_state.repeater_phase = 'left_on'
                else:
                    st.session_state.repeater_phase = 'complete'
                    st.session_state.timer_state = 'idle'
            
            st.session_state.start_time = time.time()
        
        time.sleep(0.1)
        st.rerun()
