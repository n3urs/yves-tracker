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
        # Filter out 1RM tests
        df = df[~df['Exercise'].str.contains('1RM Test', na=False)]
        
      

        
        # Helper function to create podium display
        def create_podium(leaderboard_data, title, emoji):
            """Create a visual podium for top 3"""
            st.markdown(f"### {emoji} {title}")
            
            if len(leaderboard_data) == 0:
                st.info("No data yet!")
                return
            
            # Podium for top 3
            if len(df) > 0:
               

                # Create columns for podium (2nd, 1st, 3rd positions)
                col2, col1, col3 = st.columns([1, 1, 1])
                
                # 1st place (center, tallest)
                with col1:
                    st.markdown("""
                        <div style='text-align: center; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                        padding: 30px 20px; border-radius: 15px; margin-bottom: 10px; box-shadow: 0 8px 16px rgba(255,215,0,0.3);'>
                            <div style='font-size: 60px; margin-bottom: 10px;'>🥇</div>
                            <div style='font-size: 24px; font-weight: bold; color: #1a1a2e; margin-bottom: 5px;'>{}</div>
                            <div style='font-size: 32px; font-weight: bold; color: #1a1a2e;'>{} kg</div>
                        </div>
                    """.format(leaderboard_data.iloc[0]['User'], leaderboard_data.iloc[0]['Max Load (kg)']), unsafe_allow_html=True)
                
                # 2nd place (left, medium height)
                with col2:
                    st.markdown("""
                        <div style='text-align: center; background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%); 
                        padding: 20px 15px; border-radius: 15px; margin-bottom: 10px; margin-top: 30px; box-shadow: 0 6px 12px rgba(192,192,192,0.3);'>
                            <div style='font-size: 50px; margin-bottom: 8px;'>🥈</div>
                            <div style='font-size: 20px; font-weight: bold; color: #1a1a2e; margin-bottom: 5px;'>{}</div>
                            <div style='font-size: 26px; font-weight: bold; color: #1a1a2e;'>{} kg</div>
                        </div>
                    """.format(leaderboard_data.iloc[1]['User'], leaderboard_data.iloc[1]['Max Load (kg)']), unsafe_allow_html=True)
                
                # 3rd place (right, shortest)
                with col3:
                    st.markdown("""
                        <div style='text-align: center; background: linear-gradient(135deg, #CD7F32 0%, #B8732D 100%); 
                        padding: 15px 12px; border-radius: 15px; margin-bottom: 10px; margin-top: 60px; box-shadow: 0 4px 8px rgba(205,127,50,0.3);'>
                            <div style='font-size: 40px; margin-bottom: 6px;'>🥉</div>
                            <div style='font-size: 18px; font-weight: bold; color: #1a1a2e; margin-bottom: 5px;'>{}</div>
                            <div style='font-size: 24px; font-weight: bold; color: #1a1a2e;'>{} kg</div>
                        </div>
                    """.format(leaderboard_data.iloc[2]['User'], leaderboard_data.iloc[2]['Max Load (kg)']), unsafe_allow_html=True)
            
            elif len(leaderboard_data) == 2:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                        padding: 25px; border-radius: 15px; box-shadow: 0 8px 16px rgba(255,215,0,0.3);'>
                            <div style='font-size: 50px;'>🥇</div>
                            <div style='font-size: 20px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['User']}</div>
                            <div style='font-size: 28px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['Max Load (kg)']} kg</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%); 
                        padding: 25px; border-radius: 15px; box-shadow: 0 6px 12px rgba(192,192,192,0.3);'>
                            <div style='font-size: 50px;'>🥈</div>
                            <div style='font-size: 20px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[1]['User']}</div>
                            <div style='font-size: 28px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[1]['Max Load (kg)']} kg</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif len(leaderboard_data) == 1:
                st.markdown(f"""
                    <div style='text-align: center; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                    padding: 30px; border-radius: 15px; box-shadow: 0 8px 16px rgba(255,215,0,0.3); max-width: 400px; margin: 0 auto;'>
                        <div style='font-size: 60px;'>🥇</div>
                        <div style='font-size: 24px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['User']}</div>
                        <div style='font-size: 32px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['Max Load (kg)']} kg</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Rest of participants (4th onwards)
            if len(leaderboard_data) > 3:
                st.markdown("#### 🎖️ Other Rankings")
                for idx in range(3, len(leaderboard_data)):
                    row = leaderboard_data.iloc[idx]
                    st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; 
                        margin-bottom: 8px; border-left: 4px solid #4CAF50;'>
                            <span style='font-size: 20px; font-weight: bold; color: #888;'>#{idx + 1}</span>
                            <span style='font-size: 20px; font-weight: bold; margin-left: 15px;'>{row['User']}</span>
                            <span style='font-size: 24px; font-weight: bold; float: right; color: #4CAF50;'>{row['Max Load (kg)']} kg</span>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Max Lifts Section
        st.markdown("---")
        st.markdown("## 💪 Max Lifts by Exercise")
        
        exercises = ["20mm Edge", "Pinch", "Wrist Roller"]
        
        for exercise in exercises:
            with st.expander(f"🏋️ {exercise}", expanded=True):
                df_ex = df[df['Exercise'].str.contains(exercise, na=False)]
                
                if len(df_ex) > 0:
                    col1, col2 = st.columns(2)
                    
                    # Left arm
                    with col1:
                        df_left = df_ex[df_ex['Arm'] == 'L'].copy()
                        df_left['Actual_Load_kg'] = pd.to_numeric(df_left['Actual_Load_kg'], errors='coerce')
                        
                        if len(df_left) > 0:
                            leaderboard_left = df_left.groupby('User')['Actual_Load_kg'].max().sort_values(ascending=False).reset_index()
                            leaderboard_left.columns = ['User', 'Max Load (kg)']
                            create_podium(leaderboard_left, "Left Arm", "👈")
                    
                    # Right arm
                    with col2:
                        df_right = df_ex[df_ex['Arm'] == 'R'].copy()
                        df_right['Actual_Load_kg'] = pd.to_numeric(df_right['Actual_Load_kg'], errors='coerce')
                        
                        if len(df_right) > 0:
                            leaderboard_right = df_right.groupby('User')['Actual_Load_kg'].max().sort_values(ascending=False).reset_index()
                            leaderboard_right.columns = ['User', 'Max Load (kg)']
                            create_podium(leaderboard_right, "Right Arm", "👉")
                else:
                    st.info(f"No {exercise} data yet!")
        
        # Total volume leaderboard
        st.markdown("---")
        st.markdown("## 📊 Total Training Volume")
        st.caption("All-time cumulative volume across all exercises")
        
               # Filter out 1RM tests
    df_filtered = df[~df['Exercise'].str.contains('1RM Test', na=False)]
    
    df_filtered['Volume'] = (pd.to_numeric(df_filtered['Actual_Load_kg'], errors='coerce') *
                             pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') *
                             pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce'))

    volume_leaderboard = df_filtered.groupby('User')['Volume'].sum().sort_values(ascending=False).reset_index()
    volume_leaderboard.columns = ['User', 'Max Load (kg)']  # Rename for compatibility
    volume_leaderboard['Max Load (kg)'] = volume_leaderboard['Max Load (kg)'].round(0).astype(int)

    create_podium(volume_leaderboard, "Volume Kings", "👑")

        
    else:
        st.info("📝 No workout data available yet. Start logging workouts to see the leaderboard!")
else:
    st.error("⚠️ Could not connect to Google Sheets.")
