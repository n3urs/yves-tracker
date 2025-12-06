import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Progress", page_icon="📊", layout="wide")

init_session_state()

st.title("📊 Progress Analytics")

# User selector in sidebar
st.sidebar.header("👤 User")
st.session_state.current_user = st.sidebar.selectbox(
    "Select User:",
    USER_LIST,
    index=USER_LIST.index(st.session_state.current_user),
    key="user_selector_progress"
)

selected_user = st.session_state.current_user

# Connect to sheet
worksheet = get_google_sheet()

# Load data
if worksheet:
    df_fresh = load_data_from_sheets(worksheet, user=selected_user)
    
    if len(df_fresh) > 0:
        exercise_options = [ex for ex in df_fresh["Exercise"].unique().tolist() if not ex.startswith("1RM Test:")]
        
        if len(exercise_options) > 0:
            selected_analysis_exercise = st.selectbox("View progress for:", exercise_options, key="analysis_exercise")
            
            df_filtered = df_fresh[df_fresh["Exercise"] == selected_analysis_exercise].copy()
            
            # Convert data types
            df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
            df_filtered = df_filtered.sort_values("Date").reset_index(drop=True)
            
            numeric_cols = ["1RM_Reference", "Target_Percentage", "Prescribed_Load_kg", 
                           "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE"]
            for col in numeric_cols:
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
            
            df_filtered["Estimated_1RM"] = df_filtered.apply(
                lambda row: row["Actual_Load_kg"] if row["Reps_Per_Set"] == 1 
                else estimate_1rm_epley(row["Actual_Load_kg"], row["Reps_Per_Set"]),
                axis=1
            )
            
            df_left = df_filtered[df_filtered["Arm"] == "L"].copy()
            df_right = df_filtered[df_filtered["Arm"] == "R"].copy()
            
            # ==================== PROGRESSION SUGGESTIONS ====================
            if len(df_filtered) >= 3:
                st.markdown("---")
                st.subheader("🎯 Training Recommendations")
                
                suggestions = analyze_progression(df_filtered, selected_analysis_exercise)
                
                if suggestions:
                    for suggestion in suggestions:
                        if suggestion["type"] == "increase":
                            st.success(suggestion["message"])
                        elif suggestion["type"] == "caution":
                            st.warning(suggestion["message"])
                        else:
                            st.info(suggestion["message"])
                else:
                    st.info("Keep training! Need at least 3 sessions for recommendations.")
                
                st.markdown("---")
            
            # Get 1RM test data
            test_exercise_name = f"1RM Test: {selected_analysis_exercise}"
            df_tests = df_fresh[df_fresh["Exercise"] == test_exercise_name].copy()
            
            # Metrics
            col_metrics, col_1rm_ref = st.columns([3, 1])
            
            with col_metrics:
                if len(df_left) > 0 or len(df_right) > 0:
                    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                    with col_metric1:
                        best_L = df_left['Actual_Load_kg'].max() if len(df_left) > 0 else 0
                        st.metric("Best Load (L)", f"{best_L:.1f} kg")
                    with col_metric2:
                        best_R = df_right['Actual_Load_kg'].max() if len(df_right) > 0 else 0
                        st.metric("Best Load (R)", f"{best_R:.1f} kg")
                    with col_metric3:
                        vol_L = (df_left["Actual_Load_kg"] * df_left["Reps_Per_Set"] * df_left["Sets_Completed"]).sum() if len(df_left) > 0 else 0
                        vol_R = (df_right["Actual_Load_kg"] * df_right["Reps_Per_Set"] * df_right["Sets_Completed"]).sum() if len(df_right) > 0 else 0
                        st.metric("Volume (L)", f"{vol_L:.0f} kg")
                        st.caption(f"R: {vol_R:.0f} kg")
                    with col_metric4:
                        unique_sessions = df_filtered["Date"].nunique()
                        st.metric("Sessions", f"{unique_sessions}")
            
            with col_1rm_ref:
                st.markdown("#### 🎯 Latest 1RM Tests")
                if len(df_tests) > 0:
                    df_tests["Date"] = pd.to_datetime(df_tests["Date"])
                    df_tests["Actual_Load_kg"] = pd.to_numeric(df_tests["Actual_Load_kg"], errors='coerce')
                    
                    df_tests_sorted = df_tests.sort_values("Date", ascending=False)
                    latest_L = df_tests_sorted[df_tests_sorted["Arm"] == "L"].head(1)
                    latest_R = df_tests_sorted[df_tests_sorted["Arm"] == "R"].head(1)
                    
                    if len(latest_L) > 0:
                        st.write(f"**L:** {latest_L.iloc[0]['Actual_Load_kg']:.1f} kg")
                        st.caption(f"{latest_L.iloc[0]['Date'].strftime('%Y-%m-%d')}")
                    else:
                        st.write("**L:** No test yet")
                    
                    if len(latest_R) > 0:
                        st.write(f"**R:** {latest_R.iloc[0]['Actual_Load_kg']:.1f} kg")
                        st.caption(f"{latest_R.iloc[0]['Date'].strftime('%Y-%m-%d')}")
                    else:
                        st.write("**R:** No test yet")
                else:
                    st.caption("No 1RM tests logged yet")
            
            # Charts
            st.subheader("Load Over Time (Both Arms)")
            fig, ax = plt.subplots(figsize=(12, 4))
            
            if len(df_left) > 0:
                ax.plot(df_left["Date"], df_left["Actual_Load_kg"], 
                        marker="o", label="Left - Actual Load", linewidth=2, markersize=10, 
                        color="blue", alpha=0.8, markeredgewidth=2, markeredgecolor='darkblue')
                ax.plot(df_left["Date"], df_left["Estimated_1RM"], 
                        marker="s", label="Left - Estimated 1RM", linewidth=2, markersize=7, 
                        linestyle="--", color="lightblue", alpha=0.7)
            
            if len(df_right) > 0:
                ax.plot(df_right["Date"], df_right["Actual_Load_kg"], 
                        marker="^", label="Right - Actual Load", linewidth=2, markersize=10, 
                        color="green", alpha=0.8, markeredgewidth=2, markeredgecolor='darkgreen')
                ax.plot(df_right["Date"], df_right["Estimated_1RM"], 
                        marker="s", label="Right - Estimated 1RM", linewidth=2, markersize=7, 
                        linestyle="--", color="lightgreen", alpha=0.7)
            
            ax.set_xlabel("Date")
            ax.set_ylabel("Load (kg)")
            ax.set_title(f"{selected_analysis_exercise} Progress (L vs R)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
            # RPE Trend
            st.subheader("RPE Trend (Both Arms)")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            if len(df_left) > 0:
                ax2.plot(df_left["Date"], df_left["RPE"], marker="o", color="blue", linewidth=2, markersize=8, label="Left Arm", alpha=0.8)
            if len(df_right) > 0:
                ax2.plot(df_right["Date"], df_right["RPE"], marker="^", color="green", linewidth=2, markersize=8, label="Right Arm", alpha=0.8)
            ax2.set_xlabel("Date")
            ax2.set_ylabel("RPE")
            ax2.set_ylim([0, 10])
            ax2.set_title(f"Perceived Effort Over Time")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
            
            # Data table
            st.subheader("Workout Log")
            display_cols = ["Date", "Arm", "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE", "Notes"]
            st.dataframe(df_filtered[display_cols].sort_values(["Date", "Arm"], ascending=[False, True]), use_container_width=True, hide_index=True)
        else:
            st.info(f"No training workouts logged yet for {selected_user}. Only 1RM tests found.")
    else:
        st.info(f"No workouts logged yet for {selected_user}. Start by logging your first session!")
        st.page_link("pages/1_📝_Log_Workout.py", label="📝 Log Your First Workout →", use_container_width=True)
else:
    st.error("Could not connect to Google Sheets. Check your configuration.")

