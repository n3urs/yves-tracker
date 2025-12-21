import streamlit as st
import pandas as pd
import json
from supabase import create_client
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image, ImageDraw, ImageFont
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
@st.cache_resource
def get_supabase_client():
    """Connect to Supabase - returns the client object"""
    try:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

# Legacy alias for compatibility
# Google Sheets has been fully replaced by Supabase
# All data operations now go directly to Supabase

@st.cache_data(ttl=120)  # Cache for 2 minutes
def _load_table_data(table_name):
    """Internal cached function to load data from a specific table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        return []

# Alias for backwards compatibility
_load_sheet_data = _load_table_data

def load_data_from_sheets(worksheet, user=None):
    """Load all data from workouts table, optionally filtered by user"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        query = supabase.table("workouts").select("*")
        if user:
            query = query.eq("username", user)
        
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename columns to match old Google Sheets format expected by pages
            column_map = {
                'id': 'ID',
                'username': 'User',
                'date': 'Date',
                'exercise': 'Exercise',
                'arm': 'Arm',
                'sets': 'Sets_Completed',
                'reps': 'Reps_Per_Set',
                'weight': 'Actual_Load_kg',
                'rpe': 'RPE',
                'notes': 'Notes',
                'timestamp': 'Timestamp'
            }
            df = df.rename(columns=column_map)
            
            # Add missing columns that the app expects
            if 'Planned_Load_kg' not in df.columns:
                df['Planned_Load_kg'] = df['Actual_Load_kg']
            if 'Sets' not in df.columns:
                df['Sets'] = df['Sets_Completed']
            if 'Reps' not in df.columns:
                df['Reps'] = df['Reps_Per_Set']
            if 'Weight' not in df.columns:
                df['Weight'] = df['Actual_Load_kg']
                
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def save_workout_to_sheets(row_data):
    """Save a new workout to the workouts table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Map old column names to new schema
        workout_data = {
            "username": row_data.get("User"),
            "date": row_data.get("Date"),
            "exercise": row_data.get("Exercise"),
            "arm": row_data.get("Arm"),
            "sets": row_data.get("Sets_Completed") or row_data.get("Sets"),
            "reps": row_data.get("Reps_Per_Set") or row_data.get("Reps"),
            "weight": row_data.get("Actual_Load_kg") or row_data.get("Weight"),
            "notes": row_data.get("Notes", "")
        }
        
        supabase.table("workouts").insert(workout_data).execute()
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving workout: {e}")
        return False

def get_last_workout(user, exercise, arm):
    """Get the most recent workout for a specific user, exercise, and arm"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # Get workouts from Supabase
        response = supabase.table("workouts").select("*").eq("username", user).eq("exercise", exercise).eq("arm", arm).order("date", desc=True).limit(1).execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        last_workout = response.data[0]
        
        return {
            'date': last_workout.get('date', 'Unknown'),
            'weight': float(last_workout.get('weight', 0.0)),
            'reps': int(last_workout.get('reps', 0)),
            'sets': int(last_workout.get('sets', 0)),
            'rpe': int(last_workout.get('rpe', 0)),
            'notes': str(last_workout.get('notes', ''))
        }
    except Exception as e:
        return None

def generate_workout_suggestion(last_workout_data, is_endurance=False):
    """Generate a suggestion based on previous workout performance"""
    if not last_workout_data:
        if is_endurance:
            return {
                'suggestion': 'Endurance Session',
                'weight_change': 0.0,
                'message': 'First endurance session! Repeaters: 7s on, 3s off, 6 reps at 50-60% max.',
                'emoji': '🏃',
                'color': '#10b981',
                'is_endurance': True
            }
        return {
            'suggestion': 'No Previous Data',
            'weight_change': 0.0,
            'message': 'This is your first session! Start with a comfortable weight.',
            'emoji': '🎯',
            'color': '#6b8cff',
            'is_endurance': False
        }
    
    # If this is an endurance workout, return endurance-specific suggestions
    if is_endurance:
        return {
            'suggestion': 'Endurance Focus',
            'weight_change': 0.0,  # Weight will be calculated separately
            'message': 'Repeaters protocol: 7s on, 3s off, 6 reps. Sport climbing stamina!',
            'emoji': '🏃',
            'color': '#10b981',
            'is_endurance': True
        }
    
    rpe = last_workout_data['rpe']
    weight = last_workout_data['weight']
    
    # RPE-based suggestions for normal strength training
    if rpe <= 4:
        # Too easy - increase significantly
        return {
            'suggestion': 'Increase Weight',
            'weight_change': weight * 0.05,  # +5%
            'message': 'Last time was too easy. Increase by about 5 percent!',
            'emoji': '📈',
            'color': '#4ade80',
            'is_endurance': False
        }
    elif rpe <= 6:
        # A bit easy - small increase
        return {
            'suggestion': 'Slight Increase',
            'weight_change': weight * 0.025,  # +2.5%
            'message': 'Good session. Try a small increase of 2-3 percent.',
            'emoji': '⬆️',
            'color': '#10b981',
            'is_endurance': False
        }
    elif rpe <= 8:
        # Perfect intensity - maintain
        return {
            'suggestion': 'Maintain Weight',
            'weight_change': 0.0,
            'message': 'Perfect intensity. Keep the same weight!',
            'emoji': '✅',
            'color': '#f59e0b',
            'is_endurance': False
        }
    else:
        # Too hard - decrease
        return {
            'suggestion': 'Decrease Weight',
            'weight_change': -weight * 0.05,  # -5%
            'message': 'Last time was very hard. Reduce by about 5 percent.',
            'emoji': '📉',
            'color': '#ef4444',
            'is_endurance': False
        }

def load_users_from_sheets():
    """Load unique users from users table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return USER_LIST.copy()
        
        response = supabase.table("users").select("username").execute()
        if response.data:
            users = [user["username"] for user in response.data]
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

def load_user_pins_from_sheets():
    """Return a dict mapping usernames to their 4-digit PINs."""
    pins = {user: None for user in USER_LIST}
    pins[USER_PLACEHOLDER] = None
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pins
            
        response = supabase.table("users").select("username, pin").execute()
        for user in response.data:
            username = user.get("username")
            if username:
                pins[username] = _normalize_pin_value(user.get("pin"))
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
        
        # Use a form to enable Enter key submission
        with st.sidebar.form(key=f"{selector_key}_pin_form"):
            pin_value = st.text_input(
                "Enter 4-digit PIN to switch",
                type="password",
                max_chars=PIN_LENGTH,
                key=pin_key
            )
            submit_button = st.form_submit_button("Switch Profile")
            
            if submit_button:
                stored_pin = user_pins.get(selected_candidate)
                if not stored_pin:
                    st.error("No PIN found for this user. Add a PIN in the Users sheet (PIN column).")
                elif not pin_value or len(pin_value) != PIN_LENGTH or not pin_value.isdigit():
                    st.error("PIN must be exactly 4 digits.")
                elif pin_value == stored_pin:
                    st.session_state.current_user = selected_candidate
                    st.success(f"Switched to {selected_candidate}")
                    st.rerun()
                else:
                    st.error("Incorrect PIN. Try again.")

    return st.session_state.current_user

def calculate_training_streak(unique_dates):
    """Return streak length allowing <=7 days between logged sessions."""
    if not unique_dates:
        return 0
    streak = 1
    for idx in range(len(unique_dates) - 1, 0, -1):
        if (unique_dates[idx] - unique_dates[idx - 1]).days <= 7:
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

def get_bodyweight(user):
    """Get user's bodyweight from bodyweights table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 78.0
        
        response = supabase.table("bodyweights").select("bodyweight_kg").eq("username", user).execute()
        if response.data and len(response.data) > 0:
            return float(response.data[0]["bodyweight_kg"])
        return 78.0
    except:
        return 78.0

def get_bodyweight_history(user):
    """Get user's bodyweight history over time"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        response = supabase.table("bodyweight_history").select("date, bodyweight_kg").eq("username", user).order("date").execute()
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        if len(df) > 0:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['bodyweight_kg'] = pd.to_numeric(df['bodyweight_kg'], errors='coerce')
            df = df.rename(columns={'date': 'Date', 'bodyweight_kg': 'Bodyweight_kg'})
            return df[['Date', 'Bodyweight_kg']]
        
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def set_bodyweight(user, bodyweight):
    """Update user's bodyweight in bodyweights table and log history"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Update current bodyweight (upsert)
        supabase.table("bodyweights").upsert({
            "username": user,
            "bodyweight_kg": float(bodyweight)
        }).execute()
        
        # Log bodyweight history
        today = datetime.now().strftime("%Y-%m-%d")
        supabase.table("bodyweight_history").insert({
            "username": user,
            "date": today,
            "bodyweight_kg": float(bodyweight)
        }).execute()
        
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating bodyweight: {e}")
        return False

def get_user_1rms(user, exercise, arm):
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

def get_user_1rm(user, exercise, arm):
    """Get user's 1RM - first try user_profile table, then fall back to workout history"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0.0
        
        # First try user_profile table
        response = supabase.table("user_profile").select("*").eq("username", user).execute()
        if response.data:
            profile = response.data[0]
            # Map exercise name to profile column
            key_map = {
                '20mm Edge': ('20mm', arm.lower()),
                '14mm Edge': ('14mm', arm.lower()),
                'Pinch': ('pinch', arm.lower()),
                'Wrist Roller': ('wrist_roller', arm.lower()),
            }
            if exercise in key_map and key_map[exercise]:
                edge_size, side = key_map[exercise]
                col_name = f"{side}_{edge_size}_current"
                value = profile.get(col_name)
                if value and value > 0:
                    return float(value)
    except:
        pass
    
    try:
        # Fall back to workout history - find max weight for this exercise/arm
        # Look for both exact matches and "1RM Test - " prefixed exercises
        response = supabase.table("workouts").select("exercise", "weight").eq("username", user).eq("arm", arm).execute()
        
        if response.data:
            # Filter for exercises matching exactly or containing the exercise name
            weights = []
            for w in response.data:
                if w.get('weight') is not None and w.get('weight') > 0:
                    # Match exact or "1RM Test - Exercise" or just contains exercise name
                    if w['exercise'] == exercise or w['exercise'] == f"1RM Test - {exercise}" or exercise in w['exercise']:
                        weights.append(w['weight'])
            
            if weights:
                max_weight = max(weights)
                return float(max_weight)
    except:
        pass
    
    return 0.0

def set_user_1rm(user, exercise, arm, new_1rm):
    """Update user's 1RM in user_profile table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            print(f"ERROR: Failed to get Supabase client")
            return False
        
        # Map exercise name to profile column
        key_map = {
            '20mm Edge': ('20mm', arm.lower()),
            '14mm Edge': ('14mm', arm.lower()),
            'Pinch': ('pinch', arm.lower()),
            'Wrist Roller': ('wrist_roller', arm.lower()),
        }
        
        if exercise not in key_map:
            print(f"ERROR: Exercise '{exercise}' not in key_map. Available: {list(key_map.keys())}")
            return False
        
        edge_size, side = key_map[exercise]
        col_name = f"{side}_{edge_size}_current"
        
        print(f"DEBUG: Updating {col_name} for user {user} with value {new_1rm}")
        
        # Upsert to user_profile table
        result = supabase.table("user_profile").upsert({
            "username": user,
            col_name: float(new_1rm)
        }, on_conflict="username").execute()
        
        print(f"DEBUG: Update successful for {col_name}")
        return True
    except Exception as e:
        print(f"ERROR in set_user_1rm: {str(e)}")
        return False

def get_working_max(user, exercise, arm, weeks=8):
    """
    Calculate working max based on recent best performance.
    Returns the higher of: stored 1RM or estimated from recent lifts (last 8 weeks).
    """
    # Get stored 1RM (baseline from tests)
    stored_1rm = get_user_1rm(user, exercise, arm)
    
    # Get best recent lift and estimate 1RM from it
    try:
        supabase = get_supabase_client()
        if not supabase:
            return stored_1rm
        
        cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        
        # Query workouts table for recent sets
        response = supabase.table("workouts").select("*").eq("username", user).eq("arm", arm).gte("date", cutoff_date).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Filter for this exercise and exclude 1RM tests
            df_filtered = df[
                (df['exercise'].str.contains(exercise, na=False)) &
                (~df['exercise'].str.contains('1RM Test', na=False))
            ]
            
            if len(df_filtered) > 0:
                # Convert to numeric - use Supabase column names
                df_filtered['weight'] = pd.to_numeric(df_filtered['weight'], errors='coerce')
                df_filtered['reps'] = pd.to_numeric(df_filtered['reps'], errors='coerce')
                
                # Calculate estimated 1RM for each set using Epley formula
                df_filtered['Estimated_1RM'] = df_filtered.apply(
                    lambda row: estimate_1rm_epley(row['weight'], row['reps']) 
                    if pd.notna(row['weight']) and pd.notna(row['reps']) else 0,
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

# ==================== OBSOLETE GOOGLE SHEETS FUNCTIONS ====================
# These functions are no longer used after Supabase migration

# def update_user_1rm(user, exercise, arm, new_1rm):
#     """OBSOLETE: Update user's 1RM in UserProfile sheet"""
#     pass

def add_new_user(username, bodyweight=78.0, pin=None):
    """Add a new user with required PIN to Supabase."""
    created_tables = []
    try:
        supabase = get_supabase_client()
        
        # Check if user already exists
        existing = supabase.table('users').select('username').eq('username', username).execute()
        if existing.data:
            return False, f"User '{username}' already exists"
        
        # Insert user
        supabase.table('users').insert({
            'username': username,
            'pin': pin
        }).execute()
        created_tables.append('users')
        
        # Insert initial bodyweight
        supabase.table('bodyweights').insert({
            'username': username,
            'bodyweight_kg': bodyweight
        }).execute()
        created_tables.append('bodyweights')
        
        # Initialize user profile with default values for edge/pinch exercises
        supabase.table('user_profile').insert({
            'username': username,
            'bodyweight_kg': bodyweight,
            'left_20mm_current': 0.0,
            'right_20mm_current': 0.0,
            'left_14mm_current': 0.0,
            'right_14mm_current': 0.0,
            'left_20mm_goal': 0.0,
            'right_20mm_goal': 0.0,
            'left_14mm_goal': 0.0,
            'right_14mm_goal': 0.0,
            'l_pinch_current': 0.0,
            'r_pinch_current': 0.0,
            'l_wrist_roller_current': 0.0,
            'r_wrist_roller_current': 0.0
        }).execute()
        created_tables.append('user_profile')
        
        # Initialize user settings (using key-value structure)
        supabase.table('user_settings').insert({
            'username': username,
            'setting_key': 'endurance_training_enabled',
            'setting_value': 'False'
        }).execute()
        created_tables.append('user_settings')
        
        return True, f"User '{username}' created successfully! ✅ Profile added to: {', '.join(created_tables)}"
    except Exception as e:
        # Clean up any tables that were created
        for table in created_tables:
            try:
                supabase.table(table).delete().eq('username', username).execute()
            except:
                pass
        return False, f"Error creating user: {str(e)}"

def delete_user(username):
    """Delete a user from all Supabase tables"""
    deleted_from = []
    try:
        supabase = get_supabase_client()
        
        # Delete from all tables (track which ones had data)
        tables = [
            'workouts',
            'bodyweight_history',
            'bodyweights',
            'goals',
            'user_profile',
            'user_settings',
            'custom_workout_logs',
            'custom_workout_templates',
            'activity_log',
            'users'
        ]
        
        for table in tables:
            try:
                result = supabase.table(table).delete().eq('username', username).execute()
                if result.data and len(result.data) > 0:
                    deleted_from.append(f"{table} ({len(result.data)} rows)")
                elif hasattr(result, 'count') and result.count > 0:
                    deleted_from.append(f"{table}")
            except Exception as table_error:
                # Continue even if a table doesn't exist or has no data
                pass
        
        if deleted_from:
            return True, f"User '{username}' deleted successfully! 🗑️ Removed from: {', '.join(deleted_from)}"
        else:
            return True, f"User '{username}' deleted (no data found in tables)"
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"

# ==================== USER SETTINGS FOR ENDURANCE TRAINING ====================

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

# ==================== OBSOLETE GOOGLE SHEETS FUNCTIONS ====================
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
def log_activity_to_sheets(user, activity_type, duration_min=None, notes="", session_date=None):
    """
    Log a simple activity (Climbing, Board, Work Pullups, or Gym) to activity_log table.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        if session_date is None:
            session_date = datetime.now().date()
        
        date_str = session_date.strftime("%Y-%m-%d")
        
        activity_data = {
            "username": user,
            "date": date_str,
            "activity_type": activity_type,
            "duration_min": duration_min,
            "notes": notes or ""
        }
        
        supabase.table("activity_log").insert(activity_data).execute()
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error logging activity: {e}")
        return False



def load_activity_log(user=None):
    """Load activity log from activity_log table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        query = supabase.table("activity_log").select("*")
        if user:
            query = query.eq("username", user)
        
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns={
                'username': 'User',
                'date': 'Date',
                'activity_type': 'ActivityType',
                'duration_min': 'DurationMin',
                'notes': 'Notes'
            })
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def load_custom_workout_templates():
    """Load all custom workout templates from custom_workout_templates table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        response = supabase.table("custom_workout_templates").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename columns to match expected format in the page
            column_map = {
                'id': 'WorkoutID',
                'username': 'CreatedBy',
                'workout_name': 'WorkoutName',
                'workout_type': 'WorkoutType',
                'description': 'Description',
                'tracks_weight': 'TracksWeight',
                'tracks_sets': 'TracksSets',
                'tracks_reps': 'TracksReps',
                'tracks_duration': 'TracksDuration',
                'tracks_distance': 'TracksDistance',
                'tracks_rpe': 'TracksRPE',
                'created_at': 'CreatedDate'
            }
            df = df.rename(columns=column_map)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def load_custom_workout_logs(user, workout_id=None):
    """Load custom workout logs for a user from custom_workout_logs table"""
    # Define empty DataFrame with proper columns
    empty_df = pd.DataFrame(columns=['User', 'Date', 'WorkoutID', 'WorkoutName', 'Weight', 'Sets', 'Reps', 'Duration', 'Distance', 'RPE', 'Notes'])
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return empty_df
        
        query = supabase.table("custom_workout_logs").select("*").eq("username", user)
        if workout_id:
            query = query.eq("workout_id", workout_id)
        
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename columns to match old format
            column_map = {
                'username': 'User',
                'date': 'Date',
                'workout_id': 'WorkoutID',
                'workout_name': 'WorkoutName',
                'weight_kg': 'Weight',
                'sets': 'Sets',
                'reps': 'Reps',
                'duration_min': 'Duration',
                'distance_km': 'Distance',
                'rpe': 'RPE',
                'notes': 'Notes'
            }
            df = df.rename(columns=column_map)
            
            if len(df) > 0 and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            return df
        return empty_df
    except:
        return empty_df

def get_user_custom_workouts(user):
    """Get custom workouts for a specific user"""
    df_templates = load_custom_workout_templates()
    if df_templates.empty:
        return pd.DataFrame()
    return df_templates[df_templates['CreatedBy'] == user]

def load_goals(user=None):
    """Load goals from Supabase goals table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        query = supabase.table("goals").select("*")
        if user:
            query = query.eq("username", user)
        
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename columns to match old format but keep id
            column_map = {
                'username': 'User',
                'exercise': 'Exercise',
                'arm': 'Arm',
                'target_weight': 'Target_Weight',
                'completed': 'Completed',
                'date_set': 'Date_Set',
                'date_completed': 'Date_Completed'
            }
            # Only rename columns that exist
            df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading goals: {e}")
        return pd.DataFrame()

def save_goal(user, exercise, arm, target_weight):
    """Save a new goal to Supabase goals table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        supabase.table("goals").insert({
            "username": user,
            "exercise": exercise,
            "arm": arm,
            "target_weight": float(target_weight),
            "completed": False,
            "date_set": today
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error saving goal: {e}")
        return False

def complete_goal(goal_id):
    """Mark a goal as completed in Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        supabase.table("goals").update({
            "completed": True,
            "date_completed": today
        }).eq("id", goal_id).execute()
        
        return True
    except Exception as e:
        st.error(f"Error completing goal: {e}")
        return False

def delete_goal(goal_id):
    """Delete a goal from Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        supabase.table("goals").delete().eq("id", goal_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting goal: {e}")
        return False

def delete_workout_entry(workout_id):
    """Delete a workout entry from Supabase by ID"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        supabase.table("workouts").delete().eq("id", workout_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting workout: {e}")
        return False

def delete_custom_workout_log(log_id):
    """Delete a custom workout log entry from Supabase by ID"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        supabase.table("custom_workout_logs").delete().eq("id", log_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting custom workout log: {e}")
        return False

def delete_activity_log(log_id):
    """Delete an activity log entry from Supabase by ID"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        supabase.table("activity_log").delete().eq("id", log_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting activity log: {e}")
        return False

def log_custom_workout(user, workout_id, workout_name, date, 
                       weight=None, sets=None, reps=None, duration=None, 
                       distance=None, rpe=None, notes=""):
    """Log a custom workout session"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Generate unique log ID
        log_id = f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        # Insert log entry into custom_workout_logs table
        log_data = {
            "log_id": log_id,
            "username": user,
            "workout_id": int(workout_id) if workout_id else None,
            "workout_name": str(workout_name),
            "date": date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(date, datetime) else date,
            "weight_kg": float(weight) if weight else None,
            "sets": int(sets) if sets else None,
            "reps": int(reps) if reps else None,
            "duration_min": float(duration) if duration else None,
            "distance_km": float(distance) if distance else None,
            "rpe": int(rpe) if rpe else None,
            "notes": str(notes) if notes else ""
        }
        
        supabase.table("custom_workout_logs").insert(log_data).execute()
        
        # Update activity log
        activity_data = {
            "username": user,
            "date": date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(date, datetime) else date,
            "activity_type": "Custom Workout",
            "notes": workout_name
        }
        supabase.table("activity_log").insert(activity_data).execute()
        
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error logging custom workout: {e}")
        return False

# ==================== USER SETTINGS FOR ENDURANCE TRAINING ====================

def get_user_setting(user, setting_key, default_value=None):
    """Get a user setting value from user_settings table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return default_value
        
        response = supabase.table("user_settings").select("setting_value").eq("username", user).eq("setting_key", setting_key).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["setting_value"]
        return default_value
    except:
        return default_value

def set_user_setting(user, setting_key, setting_value):
    """Set a user setting value in user_settings table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        supabase.table("user_settings").upsert({
            "username": user,
            "setting_key": setting_key,
            "setting_value": str(setting_value)
        }, on_conflict="username,setting_key").execute()
        
        _load_table_data.clear()
        return True
    except Exception as e:
        st.error(f"Error setting user setting: {e}")
        return False

def get_endurance_training_enabled(user):
    """Check if endurance training is enabled for user"""
    return get_user_setting(user, "endurance_training_enabled", False)

def set_endurance_training_enabled(user, enabled):
    """Enable or disable endurance training for user"""
    return set_user_setting(user, "endurance_training_enabled", enabled)

def get_workout_count(user, exercise):
    """Get the workout count for tracking endurance cycles (resets every 3)"""
    count = get_user_setting(user, f"workout_count_{exercise}", 0)
    try:
        return int(count)
    except:
        return 0

def increment_workout_count(user, exercise):
    """Increment workout count and return new count (cycles 1, 2, 0)"""
    current_count = get_workout_count(user, exercise)
    new_count = (current_count + 1) % 3
    set_user_setting(user, f"workout_count_{exercise}", new_count)
    return new_count

def is_endurance_workout(user, exercise):
    """Determine if the next workout should be an endurance workout"""
    if not get_endurance_training_enabled(user):
        return False
    
    # Only apply to 20mm Edge exercise
    if exercise != "20mm Edge":
        return False
    
    # Check if we're at the 3rd workout (count == 2, since we count 0,1,2)
    count = get_workout_count(user, exercise)
    return count == 2

def get_weight_units(user):
    """Get user's preferred weight units (kg or lbs)"""
    units = get_user_setting(user, "weight_units", "kg")
    return units if units in ["kg", "lbs"] else "kg"

def set_weight_units(user, units):
    """Set user's preferred weight units"""
    if units in ["kg", "lbs"]:
        return set_user_setting(user, "weight_units", units)
    return False

def kg_to_lbs(kg):
    """Convert kilograms to pounds"""
    return kg * 2.20462

def lbs_to_kg(lbs):
    """Convert pounds to kilograms"""
    return lbs / 2.20462

def convert_weight_for_display(user, weight_kg):
    """Convert weight from kg (storage) to user's preferred units for display"""
    units = get_weight_units(user)
    if units == "lbs":
        return kg_to_lbs(weight_kg)
    return weight_kg

def convert_weight_for_storage(user, weight_display):
    """Convert weight from user's preferred units to kg for storage"""
    units = get_weight_units(user)
    if units == "lbs":
        return lbs_to_kg(weight_display)
    return weight_display

def get_weight_unit_label(user):
    """Get the weight unit label for display (kg or lbs)"""
    return get_weight_units(user)

def change_user_pin(user, old_pin, new_pin):
    """Change user's PIN"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Database connection error"
        
        # Verify old PIN first
        response = supabase.table("users").select("*").eq("username", user).execute()
        
        if not response.data:
            return False, "User not found"
        
        user_data = response.data[0]
        stored_pin = str(user_data.get("pin", "")).strip()
        
        if stored_pin != old_pin:
            return False, "Incorrect current PIN"
        
        # Validate new PIN
        if len(new_pin) != PIN_LENGTH or not new_pin.isdigit():
            return False, f"New PIN must be exactly {PIN_LENGTH} digits"
        
        # Update PIN
        supabase.table("users").update({"pin": new_pin}).eq("username", user).execute()
        _load_table_data.clear()
        return True, "PIN changed successfully"
        
    except Exception as e:
        return False, f"Error changing PIN: {e}"

def send_bug_report_email(user_name, message):
    """Send bug report email to oscar@sullivanltd.co.uk"""
    try:
        # Get email credentials from Streamlit secrets
        try:
            smtp_server = st.secrets.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
            smtp_port = st.secrets.get("EMAIL_SMTP_PORT", 587)
            sender_email = st.secrets.get("EMAIL_SENDER")
            sender_password = st.secrets.get("EMAIL_PASSWORD")
        except:
            return False, "Email not configured yet. Contact the admin to enable bug reporting."
        
        # Check if credentials are still the placeholder values
        if not sender_email or not sender_password or \
           sender_email == "your-email@gmail.com" or \
           sender_password == "your-app-password":
            return False, "Email not configured yet. Contact the admin to enable bug reporting."
        
        # Create message
        recipient_email = "oscar@sullivanltd.co.uk"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Yves Tracker - Report from {user_name}"
        
        # Email body
        body = f"""
New report from Yves Tracker:

User: {user_name}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

---
Sent from Yves Tracker Bug Report & Feature Request System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, "Bug report sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def render_bug_report_form():
    """Render a bug report form in the sidebar"""
    with st.sidebar.expander("🐛 Bug Reports & Requests", expanded=False):
        st.markdown("Found a bug or have a feature request? Let Oscar know!")
        
        # Get current user for context
        current_user = st.session_state.get('current_user', 'Unknown')
        
        bug_message = st.text_area(
            "Describe the issue or request:",
            placeholder="What went wrong? What feature would you like to see?",
            key="bug_report_message",
            height=100
        )
        
        if st.button("Send Report", key="send_bug_report"):
            if not bug_message or len(bug_message.strip()) < 10:
                st.error("Please provide more details (at least 10 characters)")
            else:
                success, message = send_bug_report_email(current_user, bug_message)
                if success:
                    st.success(message)
                    st.info("💡 Refresh the page to submit another report")
                else:
                    st.error(message)

def save_custom_workout_template(username, workout_name, workout_type, description, track_weight, track_sets, track_reps, track_duration, track_distance, track_rpe):
    """Save a custom workout template to Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Create workout template data
        template_data = {
            "username": username,
            "workout_name": workout_name,
            "workout_type": workout_type,
            "description": description or "",
            "tracks_weight": track_weight,
            "tracks_sets": track_sets,
            "tracks_reps": track_reps,
            "tracks_duration": track_duration,
            "tracks_distance": track_distance,
            "tracks_rpe": track_rpe
        }
        
        supabase.table("custom_workout_templates").insert(template_data).execute()
        _load_table_data.clear()
        return True
    except Exception as e:
        error_msg = str(e)
        if "duplicate key" in error_msg or "23505" in error_msg:
            st.error(f"❌ A workout named '{workout_name}' already exists! Please use a different name.")
        else:
            st.error(f"Error saving workout template: {e}")
        return False
