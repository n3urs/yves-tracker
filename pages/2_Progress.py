import streamlit as st
import sys
sys.path.append('..')
from utils.helpers import *
from utils.helpers import USER_PLACEHOLDER, generate_instagram_story, get_bodyweight_history
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

st.set_page_config(page_title="Progress", page_icon="📈", layout="wide")

init_session_state()
inject_global_styles()

# ==================== HEADER ====================
st.markdown("""
    <div class='page-header' style='text-align: center; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
    padding: 32px 24px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 15px 40px rgba(240,147,251,0.5);
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
        <h1 style='color: white; font-size: 44px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);'>📈 Progress Tracker</h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 17px; margin-top: 10px; font-weight: 400;'>
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
        st.markdown("""
            <div class='section-heading'>
                <div class='section-dot'></div>
                <div><h3>📊 Your Stats</h3></div>
            </div>
        """, unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sessions = len(df_filtered['Date'].dt.date.unique())
            st.markdown(f"""
                <div class='stat-card' style='background: linear-gradient(135deg, #5651e5 0%, #6b3fa0 100%); 
                padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 8px 25px rgba(102,126,234,0.5);
                border: 1px solid rgba(255,255,255,0.15); animation: fadeInUp 0.6s ease-out 0.1s backwards;'>
                    <div style='font-size: 13px; color: rgba(255,255,255,0.95); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Total Sessions</div>
                    <div style='font-size: 40px; font-weight: 800; color: white; text-shadow: 0 2px 8px rgba(0,0,0,0.3);'>{total_sessions}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_rpe = df_filtered['RPE'].mean() if 'RPE' in df_filtered.columns else 0
            rpe_color = "#4ade80" if avg_rpe < 7 else "#fb923c" if avg_rpe < 8.5 else "#ef4444"
            st.markdown(f"""
                <div class='stat-card' style='background: linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%); 
                padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 8px 25px rgba(79,172,254,0.5);
                border: 1px solid rgba(255,255,255,0.15); animation: fadeInUp 0.6s ease-out 0.2s backwards;'>
                    <div style='font-size: 13px; color: rgba(255,255,255,0.95); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Average RPE</div>
                    <div style='font-size: 40px; font-weight: 800; color: white; text-shadow: 0 2px 8px rgba(0,0,0,0.3);'>{avg_rpe:.1f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_reps = (pd.to_numeric(df_filtered['Reps_Per_Set'], errors='coerce') * 
                         pd.to_numeric(df_filtered['Sets_Completed'], errors='coerce')).sum()
            st.markdown(f"""
                <div class='stat-card' style='background: linear-gradient(135deg, #e1306c 0%, #f77737 100%); 
                padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 8px 25px rgba(250,112,154,0.5);
                border: 1px solid rgba(255,255,255,0.15); animation: fadeInUp 0.6s ease-out 0.3s backwards;'>
                    <div style='font-size: 13px; color: rgba(255,255,255,0.95); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Total Reps</div>
                    <div style='font-size: 40px; font-weight: 800; color: white; text-shadow: 0 2px 8px rgba(0,0,0,0.3);'>{int(total_reps)}</div>
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
                <div class='stat-card' style='background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
                padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 8px 25px rgba(48,207,208,0.5);
                border: 1px solid rgba(255,255,255,0.15); animation: fadeInUp 0.6s ease-out 0.4s backwards;'>
                    <div style='font-size: 13px; color: rgba(255,255,255,0.95); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;'>Total Volume</div>
                    <div style='font-size: 40px; font-weight: 800; color: white; text-shadow: 0 2px 8px rgba(0,0,0,0.3);'>{total_volume:.0f} kg</div>
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
        
        st.markdown("---")
        
        # Relative Strength (Strength-to-Weight Ratio)
        st.markdown("### ⚖️ Relative Strength - The Climber's Edge")
        st.caption("💡 Your strength divided by bodyweight. Higher = better climbing performance!")
        
        # Get bodyweight history
        bw_history = get_bodyweight_history(spreadsheet, selected_user)
        
        if not bw_history.empty and len(df_filtered) > 0:
            # Create a merged dataframe with workout loads and bodyweight
            df_strength = df_filtered[['Date', 'Exercise', 'Arm', 'Actual_Load_kg']].copy()
            
            # For each workout date, find the most recent bodyweight
            df_strength['Bodyweight_kg'] = df_strength['Date'].apply(
                lambda x: bw_history[bw_history['Date'] <= x]['Bodyweight_kg'].iloc[-1] 
                if len(bw_history[bw_history['Date'] <= x]) > 0 
                else get_bodyweight(spreadsheet, selected_user)
            )
            
            # Calculate relative strength (load / bodyweight)
            df_strength['Relative_Strength'] = df_strength['Actual_Load_kg'] / df_strength['Bodyweight_kg']
            
            # Group by date, exercise, and arm
            df_rel = df_strength.groupby(['Date', 'Exercise', 'Arm']).agg({
                'Relative_Strength': 'mean',
                'Bodyweight_kg': 'first'
            }).reset_index()
            
            # Create figure with two y-axes
            fig3 = go.Figure()
            
            # Add relative strength traces
            colors = {'L': '#4facfe', 'R': '#f093fb'}
            
            for exercise in df_rel['Exercise'].unique():
                for arm in df_rel['Arm'].unique():
                    df_subset = df_rel[(df_rel['Exercise'] == exercise) & (df_rel['Arm'] == arm)]
                    
                    if len(df_subset) > 0:
                        fig3.add_trace(go.Scatter(
                            x=df_subset['Date'],
                            y=df_subset['Relative_Strength'],
                            mode='lines+markers',
                            name=f'{exercise} - {arm} (Relative)',
                            line=dict(color=colors.get(arm, '#ffffff'), width=3),
                            marker=dict(size=10, color=colors.get(arm, '#ffffff'),
                                      line=dict(color='white', width=2)),
                            yaxis='y'
                        ))
            
            # Add bodyweight trace on secondary y-axis
            if len(bw_history) > 1:
                fig3.add_trace(go.Scatter(
                    x=bw_history['Date'],
                    y=bw_history['Bodyweight_kg'],
                    mode='lines+markers',
                    name='Bodyweight',
                    line=dict(color='#fbbf24', width=2, dash='dash'),
                    marker=dict(size=8, color='#fbbf24'),
                    yaxis='y2'
                ))
            
            fig3.update_layout(
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
                    title='Relative Strength (Load/BW)',
                    title_font=dict(size=16, color='white'),
                    side='left'
                ),
                yaxis2=dict(
                    showgrid=False,
                    title='Bodyweight (kg)',
                    title_font=dict(size=16, color='#fbbf24'),
                    overlaying='y',
                    side='right',
                    tickfont=dict(color='#fbbf24')
                ),
                height=500,
                hovermode='x unified',
                legend=dict(
                    bgcolor='rgba(0,0,0,0.5)',
                    bordercolor='rgba(255,255,255,0.3)',
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            # Show relative strength stats
            col_rel1, col_rel2, col_rel3 = st.columns(3)
            
            current_rel = df_rel['Relative_Strength'].iloc[-1] if len(df_rel) > 0 else 0
            max_rel = df_rel['Relative_Strength'].max() if len(df_rel) > 0 else 0
            avg_rel = df_rel['Relative_Strength'].mean() if len(df_rel) > 0 else 0
            
            with col_rel1:
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #2d7dd2 0%, #1fc8db 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(79,172,254,0.4);'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Current Relative</div>
                        <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{current_rel:.2f}</div>
                        <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>load/bodyweight</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_rel2:
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #e1306c 0%, #f77737 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(250,112,154,0.4);'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Peak Relative</div>
                        <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{max_rel:.2f}</div>
                        <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>all-time best</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_rel3:
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(48,207,208,0.4);'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.95); margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>Average Relative</div>
                        <div style='font-size: 36px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{avg_rel:.2f}</div>
                        <div style='font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);'>typical strength</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.info("💪 **Pro Tip:** Even if your absolute strength stays the same, losing bodyweight improves your relative strength - making harder climbs more achievable!")
        else:
            st.info("📊 Log more bodyweight updates to see your relative strength trend!")
        
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
        
        # ==================== INSTAGRAM STORY GENERATOR ====================
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        with st.expander("📸 Share Your Progress on Instagram", expanded=False):
            st.markdown("Create a professional Instagram Story (1080x1920) to showcase your gains!")
            
            if st.button("Generate Story Image", use_container_width=True, type="primary"):
                with st.spinner("Creating your story..."):
                    # Calculate stats
                    total_sessions = len(df['Date'].dt.date.unique())
                    total_volume = (pd.to_numeric(df['Actual_Load_kg'], errors='coerce') *
                                   pd.to_numeric(df['Reps_Per_Set'], errors='coerce') *
                                   pd.to_numeric(df['Sets_Completed'], errors='coerce')).sum()
                    
                    dates = sorted(df['Date'].dt.date.unique())
                    current_streak = 1
                    for i in range(len(dates)-1, 0, -1):
                        if (dates[i] - dates[i-1]).days <= 3:
                            current_streak += 1
                        else:
                            break
                    
                    days_training = (datetime.now() - df['Date'].min()).days
                    
                    # Prepare stats
                    stats_dict = {
                        'total_sessions': total_sessions,
                        'total_volume': total_volume,
                        'current_streak': current_streak,
                        'days_training': days_training
                    }
                    
                    # Generate image
                    story_img = generate_instagram_story(selected_user, stats_dict)
                    
                    # Convert to bytes for download
                    buf = io.BytesIO()
                    story_img.save(buf, format='PNG')
                    byte_im = buf.getvalue()
                    
                    # Display preview in smaller size
                    st.success("✅ Story created!")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.image(story_img, caption="Preview (1080x1920)", use_container_width=True)
                    
                    # Download button
                    st.download_button(
                        label="⬇️ Download Story Image",
                        data=byte_im,
                        file_name=f"yves_tracker_{selected_user}_{datetime.now().strftime('%Y%m%d')}.png",
                        mime="image/png",
                        use_container_width=True
                    )
else:
    st.error("⚠️ Could not connect to Google Sheets.")
