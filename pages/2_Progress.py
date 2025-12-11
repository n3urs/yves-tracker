import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
from utils.helpers import USER_PLACEHOLDER
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Progress", page_icon="📈", layout="wide")

init_session_state()

# ==================== HEADER ====================
st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
    padding: 30px 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(240,147,251,0.4);'>
        <h1 style='color: white; font-size: 42px; margin: 0;'>📈 Progress Tracker</h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 8px;'>
            Watch your gains stack up and crush your goals
        </p>
    </div>
""", unsafe_allow_html=True)

# Connect to Google Sheets
spreadsheet = get_google_sheet()
workout_sheet = spreadsheet.worksheet("Sheet1") if spreadsheet else None

# Load users
if spreadsheet:
    available_users = load_users_from_sheets(spreadsheet)
    user_pins = load_user_pins_from_sheets(spreadsheet)
else:
    available_users = USER_LIST.copy()
    user_pins = {user: "0000" for user in available_users}

# User selector in sidebar
st.sidebar.header("👤 User")
selected_user = user_selectbox_with_pin(
    available_users,
    user_pins,
    selector_key="user_selector_progress",
    label="Select User:"
)
st.session_state.current_user = selected_user

if selected_user == USER_PLACEHOLDER:
    st.info("🔒 Select a profile from the sidebar to view progress charts.")
    st.stop()

# Load data
if workout_sheet:
    df = load_data_from_sheets(workout_sheet, user=selected_user)
    
    if len(df) > 0:
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Filter options in colorful sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎨 Filters")
        
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
        
        # Summary stats in vibrant cards
        st.markdown("### 📊 Your Stats")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sessions = len(df_filtered['Date'].dt.date.unique())
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(102,126,234,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Total Sessions</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{total_sessions}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_rpe = df_filtered['RPE'].mean() if 'RPE' in df_filtered.columns else 0
            rpe_color = "#4ade80" if avg_rpe < 7 else "#fb923c" if avg_rpe < 8.5 else "#ef4444"
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(79,172,254,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Average RPE</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{avg_rpe:.1f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_reps = (pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') * 
                         pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce')).sum()
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(250,112,154,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Total Reps</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{int(total_reps)}</div>
                </div>
            """, unsafe_allow_html=True)
        
            # Total volume (excluding 1RM tests)
        with col4:
            # Filter out 1RM tests
            df_filtered = df[~df['Exercise'].str.contains('1RM Test', na=False)]
            
            total_volume = (pd.to_numeric(df_filtered['Actual_Load_kg'], errors='coerce') *
                           pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') *
                           pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce')).sum()
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
                padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(48,207,208,0.4);'>
                    <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px;'>Total Volume</div>
                    <div style='font-size: 36px; font-weight: bold; color: white;'>{total_volume:.0f} kg</div>
                </div>
            """, unsafe_allow_html=True)

        
        st.markdown("---")
        
        # Progress charts with vibrant styling
        st.markdown("### 💪 Load Over Time - Watch Those Gains!")
        
        # Group by date and exercise
        df_chart = df_filtered.groupby(['Date', 'Exercise', 'Arm'])['Actual_Load_kg'].mean().reset_index()
        
        # Create beautiful plotly chart with custom colors
        fig = go.Figure()
        
        # Define vibrant colors for each combination
        colors = {
            'L': '#4facfe',  # Blue for left
            'R': '#f093fb',  # Pink for right
        }
        
        for exercise in df_chart['Exercise'].unique():
            for arm in df_chart['Arm'].unique():
                df_subset = df_chart[(df_chart['Exercise'] == exercise) & (df_chart['Arm'] == arm)]
                
                if len(df_subset) > 0:
                    fig.add_trace(go.Scatter(
                        x=df_subset['Date'],
                        y=df_subset['Actual_Load_kg'],
                        mode='lines+markers',
                        name=f'{exercise} - {arm}',
                        line=dict(color=colors.get(arm, '#ffffff'), width=3),
                        marker=dict(size=10, color=colors.get(arm, '#ffffff'), 
                                  line=dict(color='white', width=2))
                    ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=14),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='Date',
                title_font=dict(size=16, color='white')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='Load (kg)',
                title_font=dict(size=16, color='white')
            ),
            height=500,
            hovermode='x unified',
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.3)',
                borderwidth=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # RPE over time
        st.markdown("### 😤 RPE Trend - Monitor Your Fatigue")
        
        df_rpe = df_filtered.groupby(['Date', 'Exercise'])['RPE'].mean().reset_index()
        
        fig2 = go.Figure()
        
        # RPE colors - gradient from green to red
        rpe_colors = ['#10b981', '#f59e0b', '#ef4444']
        
        for idx, exercise in enumerate(df_rpe['Exercise'].unique()):
            df_subset = df_rpe[df_rpe['Exercise'] == exercise]
            
            fig2.add_trace(go.Scatter(
                x=df_subset['Date'],
                y=df_subset['RPE'],
                mode='lines+markers',
                name=exercise,
                line=dict(color=rpe_colors[idx % len(rpe_colors)], width=3),
                marker=dict(size=10, color=rpe_colors[idx % len(rpe_colors)],
                          line=dict(color='white', width=2)),
                fill='tozeroy',
                fillcolor=f'rgba({int(rpe_colors[idx % len(rpe_colors)][1:3], 16)}, {int(rpe_colors[idx % len(rpe_colors)][3:5], 16)}, {int(rpe_colors[idx % len(rpe_colors)][5:7], 16)}, 0.2)'
            ))
        
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=14),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='Date',
                title_font=dict(size=16, color='white')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='RPE',
                title_font=dict(size=16, color='white'),
                range=[0, 10]
            ),
            height=400,
            hovermode='x unified',
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.3)',
                borderwidth=1
            )
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Recent workouts table
        st.markdown("---")
        st.markdown("### 📋 Recent Workouts")
        
        recent_df = df_filtered.tail(10).copy()
        recent_df['Date'] = recent_df['Date'].dt.strftime('%Y-%m-%d')
        
        # Style the dataframe
        st.dataframe(
            recent_df[['Date', 'Exercise', 'Arm', 'Actual_Load_kg', 'Reps_Per_Set', 'Sets_Completed', 'RPE', 'Notes']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Date": st.column_config.TextColumn("Date", width="small"),
                "Exercise": st.column_config.TextColumn("Exercise", width="medium"),
                "Arm": st.column_config.TextColumn("Arm", width="small"),
                "Actual_Load_kg": st.column_config.NumberColumn("Load (kg)", format="%.1f kg"),
                "Reps_Per_Set": st.column_config.NumberColumn("Reps", format="%d"),
                "Sets_Completed": st.column_config.NumberColumn("Sets", format="%d"),
                "RPE": st.column_config.NumberColumn("RPE", format="%d"),
                "Notes": st.column_config.TextColumn("Notes", width="large")
            }
        )
        
        # Motivational message based on progress
        st.markdown("---")
        
        # Calculate if improving
        if len(df_filtered) >= 2:
            df_sorted = df_filtered.sort_values('Date')
            recent_avg = df_sorted.tail(3)['Actual_Load_kg'].mean()
            older_avg = df_sorted.head(3)['Actual_Load_kg'].mean()
            
            if recent_avg > older_avg:
                improvement = ((recent_avg - older_avg) / older_avg) * 100
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #4ade80 0%, #10b981 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 6px 20px rgba(74,222,128,0.4);'>
                        <div style='font-size: 32px; margin-bottom: 10px;'>🚀</div>
                        <div style='font-size: 24px; font-weight: bold; color: white;'>You're crushing it!</div>
                        <div style='font-size: 16px; color: rgba(255,255,255,0.9); margin-top: 8px;'>
                            Your loads are up {improvement:.1f}% compared to when you started. Keep going! 💪
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); 
                    padding: 20px; border-radius: 12px; text-align: center;'>
                        <div style='font-size: 32px; margin-bottom: 10px;'>💡</div>
                        <div style='font-size: 20px; font-weight: bold; color: white;'>Keep pushing!</div>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 8px;'>
                            Progress isn't always linear. Stay consistent and the gains will come!
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
    else:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 40px; border-radius: 15px; text-align: center;'>
                <div style='font-size: 64px; margin-bottom: 20px;'>📝</div>
                <div style='font-size: 28px; font-weight: bold; color: white; margin-bottom: 15px;'>
                    No workout data yet!
                </div>
                <div style='font-size: 18px; color: rgba(255,255,255,0.9);'>
                    Head to <strong>Log Workout</strong> to start tracking your progress and watch those gains stack up! 💪
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.error("⚠️ Could not connect to Google Sheets.")
