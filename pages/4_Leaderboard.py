import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import pandas as pd

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

init_session_state()

st.title("🏆 Leaderboard")

# Connect to Google Sheets
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

if workout_sheet:
    df = load_data_from_sheets(workout_sheet)
    
    if len(df) > 0:
        st.markdown("---")
        st.subheader("💪 Max Lifts by Exercise")
        
        # Get max loads for each exercise
        exercises = ["20mm Edge", "Pinch", "Wrist Roller"]
        
        for exercise in exercises:
            st.markdown(f"### {exercise}")
            
            df_ex = df[df['Exercise'].str.contains(exercise, na=False)]
            
            if len(df_ex) > 0:
                # Left arm
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Left Arm**")
                    df_left = df_ex[df_ex['Arm'] == 'L'].copy()
                    df_left['Actual_Load_kg'] = pd.to_numeric(df_left['Actual_Load_kg'], errors='coerce')
                    
                    if len(df_left) > 0:
                        leaderboard_left = df_left.groupby('User')['Actual_Load_kg'].max().sort_values(ascending=False).reset_index()
                        leaderboard_left.columns = ['User', 'Max Load (kg)']
                        
                        for idx, row in leaderboard_left.iterrows():
                            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "  "
                            st.write(f"{medal} {row['User']}: **{row['Max Load (kg)']} kg**")
                
                with col2:
                    st.markdown("**Right Arm**")
                    df_right = df_ex[df_ex['Arm'] == 'R'].copy()
                    df_right['Actual_Load_kg'] = pd.to_numeric(df_right['Actual_Load_kg'], errors='coerce')
                    
                    if len(df_right) > 0:
                        leaderboard_right = df_right.groupby('User')['Actual_Load_kg'].max().sort_values(ascending=False).reset_index()
                        leaderboard_right.columns = ['User', 'Max Load (kg)']
                        
                        for idx, row in leaderboard_right.iterrows():
                            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "  "
                            st.write(f"{medal} {row['User']}: **{row['Max Load (kg)']} kg**")
            
            st.markdown("---")
        
        # Total volume leaderboard
        st.subheader("📊 Total Training Volume (All Time)")
        
        df['Volume'] = (pd.to_numeric(df['Actual_Load_kg'], errors='coerce') * 
                       pd.to_numeric(df['Reps_Per_Set'], errors='coerce') * 
                       pd.to_numeric(df['Sets_Completed'], errors='coerce'))
        
        volume_leaderboard = df.groupby('User')['Volume'].sum().sort_values(ascending=False).reset_index()
        volume_leaderboard.columns = ['User', 'Total Volume (kg)']
        
        for idx, row in volume_leaderboard.iterrows():
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "  "
            st.write(f"{medal} {row['User']}: **{row['Total Volume (kg)']:,.0f} kg**")
        
    else:
        st.info("No workout data available yet. Start logging workouts!")
else:
    st.error("⚠️ Could not connect to Google Sheets.")
