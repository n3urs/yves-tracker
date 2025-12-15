import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image, ImageDraw, ImageFont

PLATE_SIZES = [20, 15, 10, 5, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.25]

QUICK_NOTES = {"💪 Strong": "Strong", "😴 Tired": "Tired", "🤕 Hand pain": "Hand pain", "😤 Hard": "Hard", "✨ Great": "Great"}
USER_LIST = ["Oscar", "Ian"]
PIN_LENGTH = 4
USER_PLACEHOLDER = "🔒 Select a profile"
INACTIVITY_THRESHOLD_DAYS = 5
STYLE_VERSION = "2024-12-11-v2"

def inject_global_styles():
    """Apply shared typography, layout, and glass styles once per session."""
    if st.session_state.get("_global_style_token") == STYLE_VERSION:
        return
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
        
        /* CSS Variables */
        :root {
            --bg-primary: #050B1C;
            --glass: rgba(12, 18, 35, 0.78);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --glow-primary: rgba(107, 140, 255, 0.6);
            --glow-secondary: rgba(168, 85, 247, 0.6);
        }
        
        /* Keyframe Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.7;
            }
        }
        
        @keyframes glow {
            0%, 100% {
                box-shadow: 0 0 20px var(--glow-primary), 0 0 40px var(--glow-primary);
            }
            50% {
                box-shadow: 0 0 30px var(--glow-secondary), 0 0 60px var(--glow-secondary);
            }
        }
        
        @keyframes gradientShift {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }
        
        @keyframes float {
            0%, 100% {
                transform: translateY(0px);
            }
            50% {
                transform: translateY(-10px);
            }
        }
        
        @keyframes shimmer {
            0% {
                background-position: -1000px 0;
            }
            100% {
                background-position: 1000px 0;
            }
        }
        
        /* Base Styles */
        html, body, [class*="css"]  {
            font-family: 'Space Grotesk', sans-serif !important;
            color: #F5F7FF;
        }
        
        body {
            background: var(--bg-primary);
            animation: fadeIn 0.6s ease-in;
        }
        
        .main .block-container {
            padding: 2.5rem 4rem 4rem;
            max-width: 1200px;
            animation: fadeInUp 0.8s ease-out;
        }
        
        /* Sidebar Styles */
        [data-testid="stSidebar"] > div:first-child {
            background: rgba(8, 12, 28, 0.95);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255,255,255,0.05);
            animation: slideInRight 0.6s ease-out;
        }
        
        /* Section Headings */
        .section-heading {
            display: flex;
            align-items: center;
            gap: 14px;
            margin: 40px 0 18px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        .section-heading:first-child {
            margin-top: 10px;
        }
        
        .section-heading .section-dot {
            width: 12px;
            height: 12px;
            border-radius: 10px;
            background: linear-gradient(135deg, #6b8cff, #a855f7);
            box-shadow: 0 0 18px rgba(130, 155, 255, 0.8);
            animation: pulse 2s ease-in-out infinite;
        }
        
        .section-heading h3 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
        }
        
        .section-heading p {
            margin: 2px 0 0;
            color: rgba(255,255,255,0.65);
            font-size: 15px;
        }
        
        /* Hero Card */
        .hero-card {
            background: linear-gradient(120deg, rgba(103,118,255,0.25), rgba(209,118,255,0.1));
            border-radius: 28px;
            padding: 28px 36px;
            display: flex;
            justify-content: space-between;
            gap: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 25px 60px rgba(3,9,30,0.5);
            margin: 16px 0 28px;
            animation: fadeInUp 0.8s ease-out;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .hero-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 80px rgba(103, 118, 255, 0.4);
            border-color: rgba(107, 140, 255, 0.3);
        }
        
        .hero-card .hero-left .eyebrow {
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 12px;
            color: rgba(255,255,255,0.65);
            margin: 0;
        }
        
        .hero-card .hero-left h2 {
            margin: 6px 0 8px;
            font-size: 36px;
        }
        
        .hero-card .hero-left p {
            margin: 0;
            color: rgba(255,255,255,0.8);
        }
        
        .hero-card .hero-right {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: flex-end;
            text-align: right;
        }
        
        .hero-card .hero-right span {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: rgba(255,255,255,0.7);
        }
        
        .hero-card .hero-right strong {
            font-size: 30px;
            margin: 6px 0;
        }
        
        .hero-card .hero-right small {
            color: rgba(255,255,255,0.6);
        }
        
        /* Glass Panel */
        .glass-panel {
            background: var(--glass);
            border: 1px solid var(--border-subtle);
            border-radius: 22px;
            padding: 24px 28px;
            box-shadow: 0 30px 60px rgba(2, 3, 15, 0.5);
            backdrop-filter: blur(18px);
            animation: fadeInUp 0.7s ease-out;
            transition: all 0.3s ease;
        }
        
        .glass-panel:hover {
            transform: translateY(-3px);
            box-shadow: 0 35px 70px rgba(2, 3, 15, 0.7);
        }
        
        /* Stat Grid & Cards */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
        }
        
        .stat-card {
            border-radius: 16px;
            padding: 18px;
            background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.08);
            min-height: 120px;
            animation: fadeInUp 0.6s ease-out backwards;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stat-card:nth-child(1) { animation-delay: 0.1s; }
        .stat-card:nth-child(2) { animation-delay: 0.2s; }
        .stat-card:nth-child(3) { animation-delay: 0.3s; }
        .stat-card:nth-child(4) { animation-delay: 0.4s; }
        .stat-card:nth-child(5) { animation-delay: 0.5s; }
        
        .stat-card:hover {
            transform: translateY(-5px) scale(1.02);
            background: linear-gradient(135deg, rgba(107, 140, 255, 0.15), rgba(168, 85, 247, 0.1));
            border-color: rgba(107, 140, 255, 0.3);
            box-shadow: 0 10px 30px rgba(107, 140, 255, 0.3);
        }
        
        .stat-card strong {
            display: block;
            font-size: 32px;
            margin-bottom: 6px;
            transition: color 0.3s ease;
        }
        
        .stat-card:hover strong {
            color: #6b8cff;
        }
        
        .stat-card small {
            font-size: 12px;
            color: rgba(255,255,255,0.65);
            letter-spacing: 0.3px;
        }
        
        .stat-card span {
            font-size: 13px;
            color: rgba(255,255,255,0.7);
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        
        /* Quick Grid & Cards */
        .quick-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
        }
        
        .quick-card {
            display: block;
            padding: 22px;
            border-radius: 18px;
            background: rgba(17,25,50,0.85);
            text-decoration: none;
            border: 1px solid rgba(255,255,255,0.08);
            color: #F5F7FF;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.6s ease-out backwards;
            position: relative;
            overflow: hidden;
        }
        
        .quick-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.5s ease;
        }
        
        .quick-card:hover::before {
            left: 100%;
        }
        
        .quick-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: #7F9FFF;
            box-shadow: 0 15px 40px rgba(127, 159, 255, 0.4);
            background: rgba(25,35,70,0.95);
        }
        
        .quick-card .icon {
            font-size: 36px;
            margin-bottom: 8px;
            animation: float 3s ease-in-out infinite;
        }
        
        .quick-card .title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .quick-card p {
            margin: 0;
            font-size: 14px;
            color: rgba(255,255,255,0.75);
        }
        
        /* Page Headers */
        .page-header {
            animation: fadeInUp 0.6s ease-out;
            transition: all 0.3s ease;
        }
        
        .page-header:hover {
            transform: scale(1.02);
        }
        
        /* Buttons */
        .stButton > button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 12px;
            font-weight: 500;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(107, 140, 255, 0.4);
        }
        
        /* Section Divider */
        .section-divider {
            height: 1px;
            width: 100%;
            margin: 40px 0;
            background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.25), rgba(255,255,255,0));
            animation: fadeIn 1s ease-in;
        }
        
        /* Streamlit specific animations */
        [data-testid="stMetricValue"] {
            animation: fadeInUp 0.5s ease-out;
        }
        
        [data-testid="stMarkdownContainer"] {
            animation: fadeIn 0.6s ease-out;
        }
        
        /* Tab animations */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            transition: all 0.3s ease;
            border-radius: 10px;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-2px);
        }
        
        /* Input focus effects */
        input:focus, select:focus, textarea:focus {
            border-color: #6b8cff !important;
            box-shadow: 0 0 0 2px rgba(107, 140, 255, 0.2) !important;
            transition: all 0.3s ease;
        }
        
        /* Animated gradient backgrounds */
        .gradient-animate {
            background: linear-gradient(270deg, #667eea, #764ba2, #f093fb, #4facfe);
            background-size: 800% 800%;
            animation: gradientShift 8s ease infinite;
        }
        
        /* Loading skeleton */
        .skeleton {
            background: linear-gradient(90deg, 
                rgba(255,255,255,0.05) 25%, 
                rgba(255,255,255,0.1) 50%, 
                rgba(255,255,255,0.05) 75%);
            background-size: 200% 100%;
            animation: shimmer 2s infinite;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_global_style_token"] = STYLE_VERSION

BADGE_RULES = [
    {
        "id": "active_weeks",
        "name": "Consistency Roots",
        "description": "Weeks with at least one logged workout.",
        "emoji": "🌱",
        "metric": "active_weeks",
        "comparison": ">=",
        "levels": [1, 2, 4, 8, 16, 32, 52],
        "unit": "weeks",
    },
    {
        "id": "ten_sessions",
        "name": "Log Machine",
        "description": "Total workouts completed over time.",
        "emoji": "💯",
        "metric": "total_sessions",
        "comparison": ">=",
        "levels": [10, 20, 50, 100, 150, 250, 400],
        "unit": "sessions",
    },
    {
        "id": "streak_five",
        "name": "Consistency Champ",
        "description": "Training streak milestones.",
        "emoji": "🔥",
        "metric": "current_streak",
        "comparison": ">=",
        "levels": [5, 10, 20, 30, 50],
        "unit": "sessions",
    },
    {
        "id": "weekly_warrior",
        "name": "Weekly Warrior",
        "description": "Sessions completed this week.",
        "emoji": "📅",
        "metric": "sessions_this_week",
        "comparison": ">=",
        "levels": [3, 5, 8, 12, 16],
        "unit": "sessions",
    },
    {
        "id": "volume_beast",
        "name": "Volume Beast",
        "description": "Total training volume moved.",
        "emoji": "🚀",
        "metric": "total_volume",
        "comparison": ">=",
        "levels": [25000, 50000, 100000, 200000, 400000, 800000],
        "unit": "kg",
    },
    {
        "id": "fresh_session",
        "name": "Fresh Session",
        "description": "Keep workouts recent.",
        "emoji": "⚡️",
        "metric": "days_since_last",
        "comparison": "<=",
        "levels": [4, 3, 2, 1],
        "unit": "days",
    },
]

EXERCISE_PLAN = {
    "20mm Edge": {
        "Schedule": "Monday & Thursday",
        "Frequency": "2x per week",
        "Sets": "3-4 sets",
        "Reps": "3-5 reps per set",
        "Rest": "3-5 min between sets",
        "Intensity": "80-85% 1RM",
        "Technique": [
            "• Grip: Thumb over, fingers on edge (crimp grip)",
            "• Dead hang first 2-3 seconds before pulling",
            "• Keep shoulders packed (avoid shrugging)",
            "• Pull elbows down and back (don't just hang)",
            "• Focus on controlled descent (eccentric)",
            "• Avoid twisting or swinging the body"
        ]
    },
    "Pinch": {
        "Schedule": "Tuesday & Saturday",
        "Frequency": "2x per week",
        "Sets": "3-4 sets",
        "Reps": "5-8 reps per set",
        "Rest": "2-3 min between sets",
        "Intensity": "75-80% 1RM",
        "Technique": [
            "• Grip: Thumb against fingers (pinch hold)",
            "• Hold weight plate between thumb and fingers",
            "• Keep arm straight (don't bend elbow)",
            "• Squeeze hard at the top for 2-3 seconds",
            "• Lower slowly and controlled",
            "• Start with lighter weight to build grip endurance"
        ]
    },
    "Wrist Roller": {
        "Schedule": "Wednesday & Sunday",
        "Frequency": "2x per week",
        "Sets": "2-3 sets",
        "Reps": "Full ROM (up and down)",
        "Rest": "2 min between sets",
        "Intensity": "50-60% 1RM",
        "Technique": [
            "• Hold roller with arms extended at shoulder height",
            "• Roll wrist forward to wrap rope around roller",
            "• Then roll backward to unwrap",
            "• Keep movement slow and controlled",
            "• Full range of motion (flex to extension)",
            "• Can be used for warm-up or conditioning"
        ]
    }
}

# ==================== SESSION STATE ====================
def init_session_state():
    """Initialize session state variables if they don't exist"""
    if "current_user" not in st.session_state:
        st.session_state.current_user = USER_PLACEHOLDER
    if "bodyweights" not in st.session_state:
        st.session_state.bodyweights = {user: 78.0 for user in USER_LIST}
    if "saved_1rms" not in st.session_state:
        st.session_state.saved_1rms = {}
    if "goals" not in st.session_state:
        st.session_state.goals = {}

# ==================== GOOGLE SHEETS ====================
@st.cache_resource(ttl=600)
def get_google_sheet():
    """Connect to Google Sheets - returns the spreadsheet object"""
    try:
        credentials_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        sheet_url = st.secrets["SHEET_URL"]
        return client.open_by_url(sheet_url)
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

@st.cache_data(ttl=120)  # Cache for 2 minutes
def _load_sheet_data(sheet_name):
    """Internal cached function to load data from a specific sheet"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return []
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()
    except:
        return []

def load_data_from_sheets(worksheet, user=None):
    """Load all data from workout log sheet (Sheet1), optionally filtered by user"""
    try:
        data = _load_sheet_data("Sheet1")
        if data:
            df = pd.DataFrame(data)
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            return df
        else:
            return pd.DataFrame(columns=[
                "User", "Date", "Exercise", "Arm", "1RM_Reference", "Target_Percentage",
                "Prescribed_Load_kg", "Actual_Load_kg", "Reps_Per_Set",
                "Sets_Completed", "RPE", "Notes"
            ])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def save_workout_to_sheets(worksheet, row_data):
    """Append a new workout to the Sheet1"""
    try:
        clean_data = {}
        for key, value in row_data.items():
            if isinstance(value, (np.integer, np.int64)):
                clean_data[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                clean_data[key] = float(value)
            else:
                clean_data[key] = value
        worksheet.append_row(list(clean_data.values()))
        
        # Clear the cache after saving
        _load_sheet_data.clear()
        
        return True
    except Exception as e:
        st.error(f"Error saving workout: {e}")
        return False

def get_last_workout(spreadsheet, user, exercise, arm):
    """Get the most recent workout for a specific user, exercise, and arm"""
    try:
        df = load_data_from_sheets(spreadsheet, user)
        if df.empty:
            return None
        
        # Filter by exercise and arm
        filtered = df[(df['Exercise'] == exercise) & (df['Arm'] == arm)]
        if filtered.empty:
            return None
        
        # Get the most recent entry
        filtered['Date'] = pd.to_datetime(filtered['Date'], errors='coerce')
        filtered = filtered.sort_values('Date', ascending=False)
        last_workout = filtered.iloc[0]
        
        return {
            'date': last_workout['Date'].strftime('%Y-%m-%d') if pd.notna(last_workout['Date']) else 'Unknown',
            'weight': float(last_workout['Actual_Load_kg']) if pd.notna(last_workout['Actual_Load_kg']) else 0.0,
            'reps': int(last_workout['Reps_Per_Set']) if pd.notna(last_workout['Reps_Per_Set']) else 0,
            'sets': int(last_workout['Sets_Completed']) if pd.notna(last_workout['Sets_Completed']) else 0,
            'rpe': int(last_workout['RPE']) if pd.notna(last_workout['RPE']) else 0,
            'notes': str(last_workout['Notes']) if pd.notna(last_workout['Notes']) else ''
        }
    except Exception as e:
        return None

def generate_workout_suggestion(last_workout_data):
    """Generate a suggestion based on previous workout performance"""
    if not last_workout_data:
        return {
            'suggestion': 'No Previous Data',
            'weight_change': 0.0,
            'message': 'This is your first session! Start with a comfortable weight.',
            'emoji': '🎯',
            'color': '#6b8cff'
        }
    
    rpe = last_workout_data['rpe']
    weight = last_workout_data['weight']
    
    # RPE-based suggestions
    if rpe <= 4:
        # Too easy - increase significantly
        return {
            'suggestion': 'Increase Weight',
            'weight_change': weight * 0.05,  # +5%
            'message': 'Last time was too easy. Increase by about 5 percent!',
            'emoji': '📈',
            'color': '#4ade80'
        }
    elif rpe <= 6:
        # A bit easy - small increase
        return {
            'suggestion': 'Slight Increase',
            'weight_change': weight * 0.025,  # +2.5%
            'message': 'Good session. Try a small increase of 2-3 percent.',
            'emoji': '⬆️',
            'color': '#10b981'
        }
    elif rpe <= 8:
        # Perfect intensity - maintain
        return {
            'suggestion': 'Maintain Weight',
            'weight_change': 0.0,
            'message': 'Perfect intensity. Keep the same weight!',
            'emoji': '✅',
            'color': '#f59e0b'
        }
    else:
        # Too hard - decrease
        return {
            'suggestion': 'Decrease Weight',
            'weight_change': -weight * 0.05,  # -5%
            'message': 'Last time was very hard. Reduce by about 5 percent.',
            'emoji': '📉',
            'color': '#ef4444'
        }

def load_users_from_sheets(spreadsheet):
    """Load unique users from Users sheet"""
    try:
        data = _load_sheet_data("Users")
        if data:
            df = pd.DataFrame(data)
            if "Username" in df.columns:
                users = df["Username"].tolist()
                return users if users else USER_LIST.copy()
        return USER_LIST.copy()
    except Exception as e:
        return USER_LIST.copy()

def _normalize_pin_value(pin_value):
    """Convert sheet value to a cleaned 4-digit PIN string or None."""
    if pin_value is None:
        return None
    try:
        pin_str = str(pin_value).strip()
    except Exception:
        return None
    if not pin_str:
        return None
    if pin_str.endswith('.0') and pin_str.replace('.', '', 1).isdigit():
        pin_str = pin_str[:-2]
    pin_str = pin_str.replace(' ', '')
    if pin_str.isdigit():
        # Preserve leading zeros if the sheet stores the pin as an int
        return pin_str.zfill(PIN_LENGTH)
    return None

def load_user_pins_from_sheets(spreadsheet):
    """Return a dict mapping usernames to their 4-digit PINs."""
    pins = {user: None for user in USER_LIST}
    pins[USER_PLACEHOLDER] = None
    if not spreadsheet:
        return pins
    try:
        data = _load_sheet_data("Users")
        for record in data:
            username = record.get("Username")
            if username:
                pins[username] = _normalize_pin_value(record.get("PIN"))
        return pins
    except Exception:
        return pins

def user_selectbox_with_pin(available_users, user_pins, selector_key, label="Select User:"):
    """Render a sidebar selectbox that requires a PIN before switching profiles."""
    options = [USER_PLACEHOLDER] + available_users

    # Ensure session defaults exist before widgets render
    if "current_user" not in st.session_state or st.session_state.current_user not in options:
        st.session_state.current_user = USER_PLACEHOLDER
    
    if selector_key not in st.session_state or st.session_state[selector_key] not in options:
        st.session_state[selector_key] = st.session_state.current_user

    active_user = st.session_state.current_user
    selected_candidate = st.sidebar.selectbox(label, options, key=selector_key)

    display_active = "🔒 Locked" if active_user == USER_PLACEHOLDER else active_user
    st.sidebar.caption(f"Active profile: {display_active}")

    if selected_candidate == USER_PLACEHOLDER:
        if active_user != USER_PLACEHOLDER:
            st.session_state.current_user = USER_PLACEHOLDER
        st.sidebar.info("Select a profile and enter its PIN to view data.")
        return USER_PLACEHOLDER

    if selected_candidate != active_user:
        pin_key = f"{selector_key}_pin"
        pin_value = st.sidebar.text_input(
            "Enter 4-digit PIN to switch",
            type="password",
            max_chars=PIN_LENGTH,
            key=pin_key
        )
        if st.sidebar.button("Switch Profile", key=f"{selector_key}_switch"):
            stored_pin = user_pins.get(selected_candidate)
            if not stored_pin:
                st.sidebar.error("No PIN found for this user. Add a PIN in the Users sheet (PIN column).")
            elif not pin_value or len(pin_value) != PIN_LENGTH or not pin_value.isdigit():
                st.sidebar.error("PIN must be exactly 4 digits.")
            elif pin_value == stored_pin:
                st.session_state.current_user = selected_candidate
                st.sidebar.success(f"Switched to {selected_candidate}")
                st.rerun()
            else:
                st.sidebar.error("Incorrect PIN. Try again.")

    return st.session_state.current_user

def calculate_training_streak(unique_dates):
    """Return streak length allowing <=3 days between logged sessions."""
    if not unique_dates:
        return 0
    streak = 1
    for idx in range(len(unique_dates) - 1, 0, -1):
        if (unique_dates[idx] - unique_dates[idx - 1]).days <= 3:
            streak += 1
        else:
            break
    return streak

def evaluate_badges(stats):
    """Determine which performance badges are earned based on stats dict."""
    evaluated = []
    for rule in BADGE_RULES:
        value = stats.get(rule["metric"])
        comparison = rule.get("comparison", ">=")
        levels = rule.get("levels")
        if not levels:
            target = rule.get("target")
            levels = [target] if target is not None else []
        if comparison == "<=":
            levels = sorted(levels, reverse=True)
        else:
            levels = sorted(levels)
        total_levels = len(levels)
        current_level = 0
        if value is not None and total_levels > 0:
            if comparison == ">=":
                for threshold in levels:
                    if value >= threshold:
                        current_level += 1
                    else:
                        break
            elif comparison == "<=":
                for threshold in levels:
                    if value <= threshold:
                        current_level += 1
                    else:
                        break
        earned_any = current_level > 0
        maxed_out = total_levels > 0 and current_level >= total_levels
        next_target = levels[current_level] if current_level < total_levels else None
        current_target = levels[current_level - 1] if current_level > 0 else None
        progress_ratio = None
        if comparison == ">=" and next_target and value is not None and next_target > 0:
            progress_ratio = value / next_target
        evaluated.append({
            "id": rule["id"],
            "name": rule["name"],
            "description": rule["description"],
            "emoji": rule["emoji"],
            "comparison": comparison,
            "unit": rule.get("unit", ""),
            "earned": earned_any,
            "maxed_out": maxed_out,
            "current_level": current_level,
            "total_levels": total_levels,
            "current_target": current_target,
            "next_target": next_target,
            "progress_ratio": progress_ratio,
            "progress_value": value
        })
    return evaluated

def get_bodyweight(spreadsheet, user):
    """Get user's bodyweight from Bodyweights sheet"""
    try:
        records = _load_sheet_data("Bodyweights")
        for record in records:
            if record.get("User") == user:
                return float(record.get("Bodyweight_kg", 78.0))
        return 78.0
    except:
        return 78.0

def get_bodyweight_history(spreadsheet, user):
    """Get user's bodyweight history over time"""
    try:
        records = _load_sheet_data("BodyweightHistory")
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        if "User" in df.columns:
            df = df[df["User"] == user]
        
        if len(df) > 0 and "Date" in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Bodyweight_kg'] = pd.to_numeric(df['Bodyweight_kg'], errors='coerce')
            df = df.sort_values('Date')
            return df[['Date', 'Bodyweight_kg']]
        
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def set_bodyweight(spreadsheet, user, bodyweight):
    """Update user's bodyweight in Bodyweights sheet and log history"""
    try:
        # Update current bodyweight
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        records = bw_sheet.get_all_records()
        user_exists = False
        for idx, record in enumerate(records):
            if record.get("User") == user:
                bw_sheet.update_cell(idx + 2, 2, float(bodyweight))
                user_exists = True
                break
        if not user_exists:
            bw_sheet.append_row([user, float(bodyweight)])
        
        # Log bodyweight history with timestamp
        try:
            bw_history_sheet = spreadsheet.worksheet("BodyweightHistory")
        except:
            # Create sheet if it doesn't exist
            bw_history_sheet = spreadsheet.add_worksheet(title="BodyweightHistory", rows=1000, cols=3)
            bw_history_sheet.append_row(["User", "Date", "Bodyweight_kg"])
        
        # Append new bodyweight record with current date
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        bw_history_sheet.append_row([user, today, float(bodyweight)])
        
        _load_sheet_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating bodyweight: {e}")
        return False

def get_user_1rms(spreadsheet, user, exercise, arm):
    """Get user's 1RM from UserProfile sheet"""
    try:
        records = _load_sheet_data("UserProfile")
        for record in records:
            if record.get("User") == user:
                key = f"{exercise}_{arm}_1RM"
                value = record.get(key, None)
                if value and value > 0:
                    return float(value)
    except:
        pass
    return float(105 if "Edge" in exercise else 85 if "Pinch" in exercise else 75)

def get_user_1rm(spreadsheet, user, exercise, arm):
    """Get user's 1RM - first try UserProfile sheet, then fall back to workout history"""
    try:
        records = _load_sheet_data("UserProfile")
        for record in records:
            if record.get("User") == user:
                key = f"{exercise}_{arm}_1RM"
                value = record.get(key, None)
                if value and value > 0:
                    return float(value)
    except:
        pass
    
    try:
        data = _load_sheet_data("Sheet1")
        if data:
            df = pd.DataFrame(data)
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            
            if len(df) > 0:
                df_filtered = df[
                    (df['Exercise'].str.contains(exercise, na=False)) &
                    (df['Arm'] == arm)
                ]
                if len(df_filtered) > 0:
                    df_filtered['Actual_Load_kg'] = pd.to_numeric(df_filtered['Actual_Load_kg'], errors='coerce')
                    max_weight = df_filtered['Actual_Load_kg'].max()
                    if pd.notna(max_weight) and max_weight > 0:
                        return float(max_weight)
    except:
        pass
    
    return 0.0

def update_user_1rm(spreadsheet, user, exercise, arm, new_1rm):
    """Update user's 1RM in UserProfile sheet"""
    try:
        profile_sheet = spreadsheet.worksheet("UserProfile")
        records = profile_sheet.get_all_records()
        for idx, record in enumerate(records):
            if record.get("User") == user:
                key = f"{exercise}_{arm}_1RM"
                headers = list(record.keys())
                if key in headers:
                    col_idx = headers.index(key) + 1
                    profile_sheet.update_cell(idx + 2, col_idx, float(new_1rm))
                    _load_sheet_data.clear()
                    return True
        
        headers = profile_sheet.row_values(1)
        new_row = [user, 78.0, 105, 105, 85, 85, 75, 75]
        key = f"{exercise}_{arm}_1RM"
        if key in headers:
            col_idx = headers.index(key)
            new_row[col_idx] = float(new_1rm)
        profile_sheet.append_row(new_row)
        _load_sheet_data.clear()
        return True
    except Exception as e:
        return False

def add_new_user(spreadsheet, username, bodyweight=78.0, pin=None):
    """Add a new user with required PIN to all necessary sheets."""
    try:
        if not pin or len(str(pin)) != PIN_LENGTH or not str(pin).isdigit():
            return False, "PIN must be a 4-digit number."
        cleaned_pin = str(pin).zfill(PIN_LENGTH)
        users_sheet = spreadsheet.worksheet("Users")
        users_sheet.append_row([username, cleaned_pin])
        
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        bw_sheet.append_row([username, float(bodyweight)])
        
        profile_sheet = spreadsheet.worksheet("UserProfile")
        profile_sheet.append_row([username, float(bodyweight), 105, 105, 85, 85, 75, 75])
        
        _load_sheet_data.clear()
        
        return True, "User created successfully!"
    except Exception as e:
        return False, f"Error creating user: {e}"

# ==================== HELPER FUNCTIONS ====================
def calculate_plates(target_kg, pin_kg=1):
    """Find nearest achievable load with exact plate breakdown."""
    load_per_side = (target_kg - pin_kg) / 2
    best_diff = float('inf')
    best_load = target_kg
    best_plates = []
    
    for multiplier in range(int(load_per_side * 4) - 5, int(load_per_side * 4) + 10):
        test_per_side = multiplier / 4
        test_total = test_per_side * 2 + pin_kg
        
        if test_total > target_kg + 3 or test_total < target_kg - 3:
            continue
        
        plates = []
        remaining = test_per_side
        for plate in PLATE_SIZES:
            while remaining >= plate - 0.001:
                plates.append(plate)
                remaining -= plate
        
        if remaining < 0.001:
            diff = abs(test_total - target_kg)
            if diff < best_diff:
                best_diff = diff
                best_load = test_total
                best_plates = sorted(plates, reverse=True)
    
    if best_plates:
        plates_str = f"{' + '.join(map(str, best_plates))} kg per side"
        if abs(best_load - target_kg) < 0.1:
            return plates_str, best_load
        else:
            return f"{plates_str} (actual: {best_load}kg)", best_load
    
    return "No exact combo found", target_kg

def estimate_1rm_epley(load_kg, reps):
    """Epley formula: 1RM = weight * (1 + reps/30)"""
    if reps == 1:
        return load_kg
    return load_kg * (1 + reps / 30)

def calculate_relative_strength(avg_load, bodyweight):
    """Calculate relative strength: load / bodyweight"""
    if bodyweight is not None and bodyweight > 0:
        return avg_load / bodyweight
    return 0

def create_heatmap(df):
    """Create training consistency heatmap data"""
    try:
        if len(df) == 0:
            return None
        
        df_copy = df.copy()
        df_copy['Date'] = pd.to_datetime(df_copy['Date'])
        
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=12)
        df_filtered = df_copy[(df_copy['Date'] >= start_date) & (df_copy['Date'] <= end_date)]
        
        if len(df_filtered) == 0:
            return None
        
        heatmap_data = np.zeros((7, 12))
        for _, row in df_filtered.iterrows():
            date = row['Date']
            week = min((end_date - date).days // 7, 11)
            day_of_week = date.weekday()
            if week < 12 and day_of_week < 7:
                heatmap_data[day_of_week, 11 - week] += 1
        
        return heatmap_data, (start_date, end_date)
    except Exception as e:
        return None

def delete_user(spreadsheet, username):
    """Delete a user from all sheets"""
    try:
        # Delete from Users sheet
        users_sheet = spreadsheet.worksheet("Users")
        users_data = users_sheet.get_all_values()
        for idx, row in enumerate(users_data):
            if len(row) > 0 and row[0] == username:
                users_sheet.delete_rows(idx + 1)
                break
        
        # Delete from Bodyweights sheet
        bw_sheet = spreadsheet.worksheet("Bodyweights")
        bw_data = bw_sheet.get_all_values()
        for idx, row in enumerate(bw_data):
            if len(row) > 0 and row[0] == username:
                bw_sheet.delete_rows(idx + 1)
                break
        
        # Delete from UserProfile sheet
        profile_sheet = spreadsheet.worksheet("UserProfile")
        profile_data = profile_sheet.get_all_values()
        for idx, row in enumerate(profile_data):
            if len(row) > 0 and row[0] == username:
                profile_sheet.delete_rows(idx + 1)
                break
        
        # Delete workout data from Sheet1
        workout_sheet = spreadsheet.worksheet("Sheet1")
        workout_data = workout_sheet.get_all_values()
        rows_to_delete = []
        for idx, row in enumerate(workout_data):
            if len(row) > 0 and row[0] == username:  # Assuming User is first column
                rows_to_delete.append(idx + 1)
        
        # Delete rows in reverse order to avoid index shifting
        for row_idx in sorted(rows_to_delete, reverse=True):
            workout_sheet.delete_rows(row_idx)
        
        _load_sheet_data.clear()
        
        return True, f"User '{username}' deleted successfully!"
    except Exception as e:
        return False, f"Error deleting user: {e}"

# ==================== ACTIVITY LOGGING ====================
def log_activity_to_sheets(spreadsheet, user, activity_type, duration_min=None, notes="", session_date=None):
    """
    Log a simple activity (Climbing, Board, Work Pullups, or Gym) to ActivityLog sheet.
    activity_type: "Gym", "Climbing", "Board", "Work"
    session_date: datetime.date object (defaults to today)
    """
    try:
        # Get or create ActivityLog sheet
        all_sheets = [ws.title for ws in spreadsheet.worksheets()]
        if "ActivityLog" in all_sheets:
            activity_sheet = spreadsheet.worksheet("ActivityLog")
        else:
            activity_sheet = spreadsheet.add_worksheet(title="ActivityLog", rows=1000, cols=6)
            activity_sheet.append_row(["User", "Date", "ActivityType", "DurationMin", "Notes", "Timestamp"])
        
        # Use provided date or default to today
        if session_date is None:
            session_date = datetime.now().date()
        
        # Prepare row
        row_data = [
            user,
            session_date.strftime("%Y-%m-%d"),
            activity_type,
            duration_min if duration_min else "",
            notes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        activity_sheet.append_row(row_data)
        _load_sheet_data.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Error logging activity: {e}")
        return False



def load_activity_log(spreadsheet, user=None):
    """Load activity log from ActivityLog sheet, optionally filtered by user."""
    try:
        data = _load_sheet_data("ActivityLog")
        if data:
            df = pd.DataFrame(data)
            if user and "User" in df.columns:
                df = df[df["User"] == user]
            return df
        else:
            return pd.DataFrame(columns=["User", "Date", "ActivityType", "DurationMin", "Notes", "Timestamp"])
    except Exception as e:
        return pd.DataFrame(columns=["User", "Date", "ActivityType", "DurationMin", "Notes", "Timestamp"])

def get_working_max(spreadsheet, user, exercise, arm, weeks=8):
    """
    Calculate working max based on recent best performance.
    Returns the higher of: stored 1RM or estimated from recent lifts (last 8 weeks).
    """
    # Get stored 1RM (baseline from tests)
    stored_1rm = get_user_1rm(spreadsheet, user, exercise, arm)
    
    # Get best recent lift and estimate 1RM from it
    try:
        data = _load_sheet_data("Sheet1")
        if data:
            df = pd.DataFrame(data)
            cutoff_date = datetime.now() - timedelta(weeks=weeks)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Filter for this exercise, arm, recent dates, and exclude 1RM tests
            df_filtered = df[
                (df['User'] == user) &
                (df['Exercise'].str.contains(exercise, na=False)) &
                (df['Arm'] == arm) &
                (df['Date'] >= cutoff_date) &
                (~df['Exercise'].str.contains('1RM Test', na=False))
            ]
            
            if len(df_filtered) > 0:
                # Convert to numeric
                df_filtered['Actual_Load_kg'] = pd.to_numeric(df_filtered['Actual_Load_kg'], errors='coerce')
                df_filtered['Reps_Per_Set'] = pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce')
                
                # Calculate estimated 1RM for each set using Epley formula
                df_filtered['Estimated_1RM'] = df_filtered.apply(
                    lambda row: estimate_1rm_epley(row['Actual_Load_kg'], row['Reps_Per_Set']) 
                    if pd.notna(row['Actual_Load_kg']) and pd.notna(row['Reps_Per_Set']) else 0,
                    axis=1
                )
                
                best_estimated = df_filtered['Estimated_1RM'].max()
                
                if pd.notna(best_estimated) and best_estimated > 0:
                    # Return the higher of stored or estimated
                    return max(stored_1rm, best_estimated)
    except:
        pass
    
    return stored_1rm

def generate_instagram_story(user, stats_dict):
    """
    Generate an Instagram Story image (1080x1920) with user stats
    
    Args:
        user: Username
        stats_dict: Dict with keys: total_sessions, total_volume, current_streak, days_training
    
    Returns:
        PIL Image object
    """
    # Instagram Story dimensions
    width, height = 1080, 1920
    
    # Create gradient background
    img = Image.new('RGB', (width, height), color='#050B1C')
    draw = ImageDraw.Draw(img)
    
    # Create smooth gradient background (dark blue to purple)
    for i in range(height):
        progress = i / height
        r = int(5 + progress * 45)
        g = int(11 + progress * 25)
        b = int(28 + progress * 72)
        draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
    
    # Add semi-transparent overlays
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Top gradient accent
    for i in range(300):
        alpha = int(50 * (1 - i/300))
        overlay_draw.rectangle([(0, i), (width, i+1)], 
                              fill=(107, 140, 255, alpha))
    
    # Bottom gradient accent
    for i in range(400):
        alpha = int(40 * (i/400))
        overlay_draw.rectangle([(0, height-400+i), (width, height-399+i)], 
                              fill=(168, 85, 247, alpha))
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to load system fonts
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 90)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 55)
        big_stat_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 110)
        label_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 38)
    except:
        # Fallback
        title_font = subtitle_font = big_stat_font = label_font = small_font = ImageFont.load_default()
    
    # Header section
    title_text = "YVES TRACKER"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, 120), title_text, 
             fill=(255, 255, 255), font=title_font)
    
    # Username
    user_text = f"{user}'s Progress"
    user_bbox = draw.textbbox((0, 0), user_text, font=subtitle_font)
    user_width = user_bbox[2] - user_bbox[0]
    draw.text(((width - user_width) // 2, 240), user_text, 
             fill=(180, 190, 255), font=subtitle_font)
    
    # Divider line
    draw.rectangle([(width//2 - 150, 330), (width//2 + 150, 335)], 
                  fill=(107, 140, 255))
    
    # Stats cards
    stats_data = [
        (stats_dict.get('total_sessions', 0), "SESSIONS", (79, 172, 254)),
        (stats_dict.get('current_streak', 0), "DAY STREAK", (240, 147, 251)),
        (f"{stats_dict.get('total_volume', 0):,.0f}", "VOLUME (KG)", (250, 112, 154)),
        (stats_dict.get('days_training', 0), "TRAINING DAYS", (48, 207, 208)),
    ]
    
    card_y = 420
    card_height = 280
    card_padding = 40
    
    for idx, (value, label, color) in enumerate(stats_data):
        # Card background
        margin_x = 100
        card_top = card_y + (idx * (card_height + card_padding))
        
        # Semi-transparent card
        overlay2 = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay2_draw = ImageDraw.Draw(overlay2)
        
        # Rounded rectangle simulation
        overlay2_draw.rectangle(
            [(margin_x, card_top), (width - margin_x, card_top + card_height)],
            fill=(30, 40, 70, 180)
        )
        
        # Left accent bar
        overlay2_draw.rectangle(
            [(margin_x, card_top), (margin_x + 8, card_top + card_height)],
            fill=color
        )
        
        img = Image.alpha_composite(img.convert('RGBA'), overlay2).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Value (large)
        value_str = str(value)
        value_bbox = draw.textbbox((0, 0), value_str, font=big_stat_font)
        value_width = value_bbox[2] - value_bbox[0]
        value_x = (width - value_width) // 2
        draw.text((value_x, card_top + 60), value_str, 
                 fill=(255, 255, 255), font=big_stat_font)
        
        # Label (small, uppercase)
        label_bbox = draw.textbbox((0, 0), label, font=label_font)
        label_width = label_bbox[2] - label_bbox[0]
        label_x = (width - label_width) // 2
        draw.text((label_x, card_top + 190), label, 
                 fill=(150, 160, 200), font=label_font)
    
    # Footer
    footer_text = "BUILD UNBREAKABLE FINGER STRENGTH"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(((width - footer_width) // 2, height - 140), footer_text, 
             fill=(130, 140, 180), font=small_font)
    
    # Small tagline
    tagline = "@yvestracker"
    tagline_bbox = draw.textbbox((0, 0), tagline, font=small_font)
    tagline_width = tagline_bbox[2] - tagline_bbox[0]
    draw.text(((width - tagline_width) // 2, height - 90), tagline, 
             fill=(100, 110, 150), font=small_font)
    
    return img
