import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import pandas as pd

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

init_session_state()

st.title("🏆 Leaderboard")
st.markdown("### Compete with your climbing crew!")

# Connect to sheet
worksheet = get_google_sheet()

if worksheet:
    # Load ALL users data (not filtered)
    df_all = load_data_from_sheets(worksheet, user=None)
    
    if len(df_all) > 0:
        # Convert data types
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        df_all["Actual_Load_kg"] = pd.to_numeric(df_all["Actual_Load_kg"], errors='coerce')
        
        # Filter out 1RM tests for training leaderboards
        df_training = df_all[~df_all["Exercise"].str.startswith("1RM Test", na=False)].copy()
        
        # Exercise selector
        exercise_options = df_training["Exercise"].unique().tolist()
        
        if len(exercise_options) > 0:
            selected_lb_exercise = st.selectbox("Select Exercise:", exercise_options, key="lb_exercise")
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["🏋️ Absolute Strength", "⚖️ Relative Strength (Bodyweight)", "📊 Volume Leaders"])
            
            # ==================== TAB 1: ABSOLUTE STRENGTH ====================
            with tab1:
                st.subheader(f"🏆 {selected_lb_exercise} - Absolute Strength")
                
                df_exercise = df_training[df_training["Exercise"] == selected_lb_exercise].copy()
                
                if len(df_exercise) > 0:
                    # Get max for each user and arm
                    leaderboard_data = []
                    
                    for user in df_exercise["User"].unique():
                        df_user = df_exercise[df_exercise["User"] == user]
                        
                        # Left arm
                        df_left = df_user[df_user["Arm"] == "L"]
                        if len(df_left) > 0:
                            max_left = df_left["Actual_Load_kg"].max()
                            date_left = df_left[df_left["Actual_Load_kg"] == max_left]["Date"].max()
                            leaderboard_data.append({
                                "User": user,
                                "Arm": "Left",
                                "Max Load (kg)": max_left,
                                "Date": date_left.strftime("%Y-%m-%d") if pd.notna(date_left) else "N/A"
                            })
                        
                        # Right arm
                        df_right = df_user[df_user["Arm"] == "R"]
                        if len(df_right) > 0:
                            max_right = df_right["Actual_Load_kg"].max()
                            date_right = df_right[df_right["Actual_Load_kg"] == max_right]["Date"].max()
                            leaderboard_data.append({
                                "User": user,
                                "Arm": "Right",
                                "Max Load (kg)": max_right,
                                "Date": date_right.strftime("%Y-%m-%d") if pd.notna(date_right) else "N/A"
                            })
                    
                    if leaderboard_data:
                        df_lb = pd.DataFrame(leaderboard_data)
                        df_lb = df_lb.sort_values("Max Load (kg)", ascending=False).reset_index(drop=True)
                        df_lb.index = df_lb.index + 1  # Start ranking from 1
                        
                        # Add medals
                        def add_medal(rank):
                            if rank == 1:
                                return "🥇"
                            elif rank == 2:
                                return "🥈"
                            elif rank == 3:
                                return "🥉"
                            else:
                                return f"{rank}"
                        
                        df_lb.insert(0, "Rank", df_lb.index.map(add_medal))
                        
                        st.dataframe(df_lb, use_container_width=True, hide_index=True)
                    else:
                        st.info("No data yet for this exercise.")
                else:
                    st.info("No data yet for this exercise.")
            
            # ==================== TAB 2: RELATIVE STRENGTH ====================
            with tab2:
                st.subheader(f"⚖️ {selected_lb_exercise} - Relative Strength (Load / Bodyweight)")
                st.caption("Who's strongest relative to their bodyweight?")
                
                df_exercise = df_training[df_training["Exercise"] == selected_lb_exercise].copy()
                
                if len(df_exercise) > 0:
                    leaderboard_relative = []
                    
                    for user in df_exercise["User"].unique():
                        bodyweight = get_bodyweight(user)
                        df_user = df_exercise[df_exercise["User"] == user]
                        
                        # Left arm
                        df_left = df_user[df_user["Arm"] == "L"]
                        if len(df_left) > 0:
                            max_left = df_left["Actual_Load_kg"].max()
                            relative_left = calculate_relative_strength(max_left, bodyweight)
                            leaderboard_relative.append({
                                "User": user,
                                "Arm": "Left",
                                "Max Load (kg)": max_left,
                                "Bodyweight (kg)": bodyweight,
                                "Relative Strength": relative_left,
                                "Ratio": f"{relative_left:.2f}x BW"
                            })
                        
                        # Right arm
                        df_right = df_user[df_user["Arm"] == "R"]
                        if len(df_right) > 0:
                            max_right = df_right["Actual_Load_kg"].max()
                            relative_right = calculate_relative_strength(max_right, bodyweight)
                            leaderboard_relative.append({
                                "User": user,
                                "Arm": "Right",
                                "Max Load (kg)": max_right,
                                "Bodyweight (kg)": bodyweight,
                                "Relative Strength": relative_right,
                                "Ratio": f"{relative_right:.2f}x BW"
                            })
                    
                    if leaderboard_relative:
                        df_lb_rel = pd.DataFrame(leaderboard_relative)
                        df_lb_rel = df_lb_rel.sort_values("Relative Strength", ascending=False).reset_index(drop=True)
                        df_lb_rel.index = df_lb_rel.index + 1
                        
                        def add_medal(rank):
                            if rank == 1:
                                return "🥇"
                            elif rank == 2:
                                return "🥈"
                            elif rank == 3:
                                return "🥉"
                            else:
                                return f"{rank}"
                        
                        df_lb_rel.insert(0, "Rank", df_lb_rel.index.map(add_medal))
                        
                        st.dataframe(df_lb_rel, use_container_width=True, hide_index=True)
                        
                        st.info("💡 **Tip:** Lighter climbers often have higher relative strength ratios!")
                    else:
                        st.info("No data yet for this exercise.")
                else:
                    st.info("No data yet for this exercise.")
            
            # ==================== TAB 3: VOLUME LEADERS ====================
            with tab3:
                st.subheader(f"📊 {selected_lb_exercise} - Total Volume Leaders (All Time)")
                st.caption("Total Volume = Load × Reps × Sets (summed across all sessions)")
                
                df_exercise = df_training[df_training["Exercise"] == selected_lb_exercise].copy()
                
                if len(df_exercise) > 0:
                    # Calculate volume
                    df_exercise["Reps_Per_Set"] = pd.to_numeric(df_exercise["Reps_Per_Set"], errors='coerce')
                    df_exercise["Sets_Completed"] = pd.to_numeric(df_exercise["Sets_Completed"], errors='coerce')
                    df_exercise["Volume"] = df_exercise["Actual_Load_kg"] * df_exercise["Reps_Per_Set"] * df_exercise["Sets_Completed"]
                    
                    volume_leaders = []
                    
                    for user in df_exercise["User"].unique():
                        df_user = df_exercise[df_exercise["User"] == user]
                        total_volume = df_user["Volume"].sum()
                        total_sessions = df_user["Date"].nunique()
                        
                        volume_leaders.append({
                            "User": user,
                            "Total Volume (kg)": total_volume,
                            "Sessions": total_sessions,
                            "Avg Volume/Session (kg)": total_volume / total_sessions if total_sessions > 0 else 0
                        })
                    
                    if volume_leaders:
                        df_vol = pd.DataFrame(volume_leaders)
                        df_vol = df_vol.sort_values("Total Volume (kg)", ascending=False).reset_index(drop=True)
                        df_vol.index = df_vol.index + 1
                        
                        def add_medal(rank):
                            if rank == 1:
                                return "🥇"
                            elif rank == 2:
                                return "🥈"
                            elif rank == 3:
                                return "🥉"
                            else:
                                return f"{rank}"
                        
                        df_vol.insert(0, "Rank", df_vol.index.map(add_medal))
                        
                        # Format numbers
                        df_vol["Total Volume (kg)"] = df_vol["Total Volume (kg)"].apply(lambda x: f"{x:.0f}")
                        df_vol["Avg Volume/Session (kg)"] = df_vol["Avg Volume/Session (kg)"].apply(lambda x: f"{x:.0f}")
                        
                        st.dataframe(df_vol, use_container_width=True, hide_index=True)
                        
                        st.info("💡 **Volume = consistency!** High volume = more training sessions.")
                    else:
                        st.info("No data yet for this exercise.")
                else:
                    st.info("No data yet for this exercise.")
        else:
            st.info("No exercises logged yet. Start training to see leaderboards!")
    else:
        st.info("No data yet. Log some workouts to compete!")
        st.page_link("pages/1_Log_Workout.py", label="📝 Log Your First Workout →", use_container_width=True)
else:
    st.error("Could not connect to Google Sheets.")

st.markdown("---")
st.caption("🏆 Train hard, compete harder! May the best climber win!")

