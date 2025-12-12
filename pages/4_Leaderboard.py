import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import pandas as pd

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

init_session_state()
inject_global_styles()

# ==================== HEADER ====================
st.markdown("""
    <div class='page-header' style='text-align: center; background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); 
    padding: 32px 24px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 15px 40px rgba(255,215,0,0.5);
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
        <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>🏆 Leaderboard</h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
            See who's crushing it and claim your spot at the top
        </p>
    </div>
""", unsafe_allow_html=True)

# Connect to Google Sheets
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

if workout_sheet:
    df = load_data_from_sheets(workout_sheet)
    
    if len(df) > 0:
        # Filter out 1RM tests
        df = df[~df['Exercise'].str.contains('1RM Test', na=False)]
        
        # Get bodyweights for all users
        user_bodyweights = {}
        if spreadsheet:
            try:
                bodyweights_sheet = spreadsheet.worksheet("Bodyweights")
                bodyweights_data = bodyweights_sheet.get_all_values()
                
                for row in bodyweights_data[1:]:  # Skip header
                    if len(row) >= 2 and row[0]:  # Check username exists
                        username = row[0].strip()
                        try:
                            bodyweight = float(row[1])
                            user_bodyweights[username] = bodyweight
                        except ValueError:
                            user_bodyweights[username] = 78.0  # Default
            except Exception as e:
                # Default bodyweights if sheet not found
                for user in df['User'].unique():
                    user_bodyweights[user] = 78.0
        
        # Helper function to create podium display
        def create_podium(leaderboard_data, title, emoji):
            """Create a visual podium for top 3"""
            st.markdown(f"""
                <div class='section-heading'>
                    <div class='section-dot'></div>
                    <div><h3>{emoji} {title}</h3></div>
                </div>
            """, unsafe_allow_html=True)
            
            if len(leaderboard_data) == 0:
                st.info("No data yet!")
                return
            
            # Podium for top 3
            if len(leaderboard_data) >= 3:
                # Create columns for podium (2nd, 1st, 3rd positions)
                col2, col1, col3 = st.columns([1, 1, 1])
                
                # 1st place (center, tallest)
                with col1:
                    user_1 = leaderboard_data.iloc[0]['User']
                    pct_1 = leaderboard_data.iloc[0]['% of BW']
                    kg_1 = leaderboard_data.iloc[0]['Max Load (kg)']
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                        padding: 32px 22px; border-radius: 18px; margin-bottom: 10px; 
                        box-shadow: 0 15px 40px rgba(255,215,0,0.5);
                        border: 2px solid rgba(255,255,255,0.3);
                        animation: fadeInUp 0.8s ease-out, glow 3s ease-in-out infinite;
                        transition: all 0.4s ease;
                        cursor: pointer;'>
                            <div style='font-size: 64px; margin-bottom: 12px; animation: float 3s ease-in-out infinite;'>🥇</div>
                            <div style='font-size: 26px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>{user_1}</div>
                            <div style='font-size: 36px; font-weight: 800; color: #1a1a2e;'>{pct_1:.1f}%</div>
                            <div style='font-size: 18px; color: #2a2a3e; margin-top: 5px;'>({kg_1:.1f} kg)</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # 2nd place (left, medium height)
                with col2:
                    user_2 = leaderboard_data.iloc[1]['User']
                    pct_2 = leaderboard_data.iloc[1]['% of BW']
                    kg_2 = leaderboard_data.iloc[1]['Max Load (kg)']
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%); 
                        padding: 24px 18px; border-radius: 18px; margin-bottom: 10px; margin-top: 30px; 
                        box-shadow: 0 12px 30px rgba(192,192,192,0.4);
                        border: 2px solid rgba(255,255,255,0.2);
                        animation: fadeInUp 0.8s ease-out 0.1s backwards;
                        transition: all 0.4s ease;
                        cursor: pointer;'>
                            <div style='font-size: 54px; margin-bottom: 10px; animation: float 3s ease-in-out infinite 0.5s;'>🥈</div>
                            <div style='font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 6px; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>{user_2}</div>
                            <div style='font-size: 30px; font-weight: 800; color: #1a1a2e;'>{pct_2:.1f}%</div>
                            <div style='font-size: 16px; color: #2a2a3e; margin-top: 5px;'>({kg_2:.1f} kg)</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # 3rd place (right, shortest)
                with col3:
                    user_3 = leaderboard_data.iloc[2]['User']
                    pct_3 = leaderboard_data.iloc[2]['% of BW']
                    kg_3 = leaderboard_data.iloc[2]['Max Load (kg)']
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #CD7F32 0%, #B8732D 100%); 
                        padding: 18px 15px; border-radius: 18px; margin-bottom: 10px; margin-top: 60px; 
                        box-shadow: 0 10px 25px rgba(205,127,50,0.4);
                        border: 2px solid rgba(255,255,255,0.15);
                        animation: fadeInUp 0.8s ease-out 0.2s backwards;
                        transition: all 0.4s ease;
                        cursor: pointer;'>
                            <div style='font-size: 44px; margin-bottom: 8px; animation: float 3s ease-in-out infinite 1s;'>🥉</div>
                            <div style='font-size: 20px; font-weight: 700; color: #1a1a2e; margin-bottom: 5px; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>{user_3}</div>
                            <div style='font-size: 28px; font-weight: 800; color: #1a1a2e;'>{pct_3:.1f}%</div>
                            <div style='font-size: 14px; color: #2a2a3e; margin-top: 5px;'>({kg_3:.1f} kg)</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif len(leaderboard_data) == 2:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                        padding: 25px; border-radius: 15px; box-shadow: 0 8px 16px rgba(255,215,0,0.3);'>
                            <div style='font-size: 50px;'>🥇</div>
                            <div style='font-size: 20px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['User']}</div>
                            <div style='font-size: 28px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['% of BW']:.1f}%</div>
                            <div style='font-size: 16px; color: #2a2a3e;'>({leaderboard_data.iloc[0]['Max Load (kg)']:.1f} kg)</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div style='text-align: center; background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%); 
                        padding: 25px; border-radius: 15px; box-shadow: 0 6px 12px rgba(192,192,192,0.3);'>
                            <div style='font-size: 50px;'>🥈</div>
                            <div style='font-size: 20px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[1]['User']}</div>
                            <div style='font-size: 28px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[1]['% of BW']:.1f}%</div>
                            <div style='font-size: 16px; color: #2a2a3e;'>({leaderboard_data.iloc[1]['Max Load (kg)']:.1f} kg)</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif len(leaderboard_data) == 1:
                st.markdown(f"""
                    <div style='text-align: center; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                    padding: 30px; border-radius: 15px; box-shadow: 0 8px 16px rgba(255,215,0,0.3); max-width: 400px; margin: 0 auto;'>
                        <div style='font-size: 60px;'>🥇</div>
                        <div style='font-size: 24px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['User']}</div>
                        <div style='font-size: 32px; font-weight: bold; color: #1a1a2e;'>{leaderboard_data.iloc[0]['% of BW']:.1f}%</div>
                        <div style='font-size: 18px; color: #2a2a3e;'>({leaderboard_data.iloc[0]['Max Load (kg)']:.1f} kg)</div>
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
                            <span style='font-size: 24px; font-weight: bold; float: right; color: #4CAF50;'>{row['% of BW']:.1f}%</span>
                            <span style='font-size: 16px; color: #888; float: right; margin-right: 15px;'>({row['Max Load (kg)']:.1f} kg)</span>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Max Lifts Section
        st.markdown("---")
        
        # Info about relative strength ranking
        st.info("⚖️ **Rankings are based on relative strength** - Load as a percentage of bodyweight (excluding 1RM tests). This shows your best working load relative to your bodyweight, ensuring fair comparison between different weight classes!")
        
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
                            leaderboard_left = df_left.groupby('User')['Actual_Load_kg'].max().reset_index()
                            leaderboard_left.columns = ['User', 'Max Load (kg)']
                            
                            # Add bodyweight percentage
                            leaderboard_left['Bodyweight'] = leaderboard_left['User'].map(user_bodyweights)
                            leaderboard_left['% of BW'] = (leaderboard_left['Max Load (kg)'] / leaderboard_left['Bodyweight']) * 100
                            
                            # Sort by percentage
                            leaderboard_left = leaderboard_left.sort_values('% of BW', ascending=False)
                            create_podium(leaderboard_left, "Left Arm", "👈")
                    
                    # Right arm
                    with col2:
                        df_right = df_ex[df_ex['Arm'] == 'R'].copy()
                        df_right['Actual_Load_kg'] = pd.to_numeric(df_right['Actual_Load_kg'], errors='coerce')
                        
                        if len(df_right) > 0:
                            leaderboard_right = df_right.groupby('User')['Actual_Load_kg'].max().reset_index()
                            leaderboard_right.columns = ['User', 'Max Load (kg)']
                            
                            # Add bodyweight percentage
                            leaderboard_right['Bodyweight'] = leaderboard_right['User'].map(user_bodyweights)
                            leaderboard_right['% of BW'] = (leaderboard_right['Max Load (kg)'] / leaderboard_right['Bodyweight']) * 100
                            
                            # Sort by percentage
                            leaderboard_right = leaderboard_right.sort_values('% of BW', ascending=False)
                            create_podium(leaderboard_right, "Right Arm", "👉")
                else:
                    st.info(f"No {exercise} data yet!")
        
        # Total volume leaderboard
        st.markdown("---")
        st.markdown("## 📊 Total Training Volume")
        st.caption("All-time cumulative volume across all exercises")
        
        df['Volume'] = (pd.to_numeric(df['Actual_Load_kg'], errors='coerce') *
                       pd.to_numeric(df['Reps_Per_Set'], errors='coerce') *
                       pd.to_numeric(df['Sets_Completed'], errors='coerce'))

        volume_leaderboard = df.groupby('User')['Volume'].sum().sort_values(ascending=False).reset_index()
        volume_leaderboard.columns = ['User', 'Total Volume']
        volume_leaderboard['Total Volume'] = volume_leaderboard['Total Volume'].round(0).astype(int)
        
        # Display volume leaderboard (no bodyweight percentage for volume)
        st.markdown("""
            <div class='section-heading'>
                <div class='section-dot'></div>
                <div><h3>👑 Volume Kings</h3></div>
            </div>
        """, unsafe_allow_html=True)
        
        if len(volume_leaderboard) > 0:
            for idx, row in volume_leaderboard.iterrows():
                rank = idx + 1
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                color = "#FFD700" if rank == 1 else "#C0C0C0" if rank == 2 else "#CD7F32" if rank == 3 else "#4CAF50"
                
                st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 18px; border-radius: 12px; 
                    margin-bottom: 10px; border-left: 5px solid {color};'>
                        <span style='font-size: 24px; margin-right: 15px;'>{medal}</span>
                        <span style='font-size: 22px; font-weight: bold;'>{row['User']}</span>
                        <span style='font-size: 26px; font-weight: bold; float: right; color: {color};'>{row['Total Volume']:,} kg</span>
                    </div>
                """, unsafe_allow_html=True)
        
    else:
        st.info("📝 No workout data available yet. Start logging workouts to see the leaderboard!")
else:
    st.error("⚠️ Could not connect to Google Sheets.")
