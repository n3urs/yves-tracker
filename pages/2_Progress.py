import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Progress", page_icon="📈", layout="wide")

init_session_state()

st.title("📈 Progress Tracker")

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
    key="user_selector_progress"
)

selected_user = st.session_state.current_user

# Load data
if workout_sheet:
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    if len(df) > 0:
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Filter options
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Filters")
        
        exercises = ["All"] + sorted(df['Exercise'].unique().tolist())
        selected_exercise = st.sidebar.selectbox("Exercise:", exercises)
        
        arms = ["Both"] + sorted(df['Arm'].unique().tolist())
        selected_arm = st.sidebar.selectbox("Arm:", arms)
        
        # Apply filters
        df_filtered = df.copy()
        if selected_exercise != "All":
            df_filtered = df_filtered[df_filtered['Exercise'] == selected_exercise]
        if selected_arm != "Both":
            df_filtered = df_filtered[df_filtered['Arm'] == selected_arm]
        
        # Summary stats
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sessions = len(df_filtered['Date'].unique())
            st.metric("Total Sessions", total_sessions)
        
        with col2:
            avg_rpe = df_filtered['RPE'].mean() if 'RPE' in df_filtered.columns else 0
            st.metric("Average RPE", f"{avg_rpe:.1f}")
        
        with col3:
            total_reps = (pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') * 
                         pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce')).sum()
            st.metric("Total Reps", int(total_reps))
        
        with col4:
            total_volume = (pd.to_numeric(df_filtered['Actual_Load_kg'], errors='coerce') * 
                           pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') * 
                           pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce')).sum()
            st.metric("Total Volume (kg)", f"{total_volume:.0f}")
        
        # Progress charts
        st.markdown("---")
        st.subheader("📊 Load Over Time")
        
        # Group by date and exercise
        df_chart = df_filtered.groupby(['Date', 'Exercise', 'Arm'])['Actual_Load_kg'].mean().reset_index()
        
        fig = px.line(df_chart, x='Date', y='Actual_Load_kg', color='Exercise', 
                     line_dash='Arm', markers=True,
                     labels={'Actual_Load_kg': 'Load (kg)', 'Date': 'Date'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # RPE over time
        st.markdown("---")
        st.subheader("💪 RPE Over Time")
        
        df_rpe = df_filtered.groupby(['Date', 'Exercise'])['RPE'].mean().reset_index()
        
        fig2 = px.line(df_rpe, x='Date', y='RPE', color='Exercise', markers=True)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Recent workouts table
        st.markdown("---")
        st.subheader("📋 Recent Workouts")
        
        recent_df = df_filtered.tail(10).copy()
        recent_df['Date'] = recent_df['Date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            recent_df[['Date', 'Exercise', 'Arm', 'Actual_Load_kg', 'Reps_Per_Set', 'Sets_Completed', 'RPE', 'Notes']],
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.info("📝 No workout data yet. Start logging workouts to see your progress!")
else:
    st.error("⚠️ Could not connect to Google Sheets.")
