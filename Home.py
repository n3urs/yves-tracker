import streamlit as st

st.set_page_config(page_title="Yves Tracker", page_icon="🧗", layout="wide")

st.title("🧗 Yves Arm-Lifting Tracker")
st.markdown("### Welcome to your climbing strength training app!")

st.markdown("---")

# Quick navigation
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.page_link("pages/1_Log_Workout.py", label="📝 Log Workout", use_container_width=True)
    st.caption("Record your training session")

with col2:
    st.page_link("pages/2_Progress.py", label="📊 View Progress", use_container_width=True)
    st.caption("Analyze your gains")

with col3:
    st.page_link("pages/3_Goals.py", label="🎯 Goals & Sharing", use_container_width=True)
    st.caption("Set goals & share results")

with col4:
    st.page_link("pages/4_Leaderboard.py", label="🏆 Leaderboard", use_container_width=True)
    st.caption("Compete with your crew")

with col5:
    st.page_link("pages/5_Profile.py", label="👤 Profile", use_container_width=True)
    st.caption("Manage your settings")

st.markdown("---")

# Quick stats overview
st.subheader("📈 Quick Stats")

# Initialize session state for user
if "current_user" not in st.session_state:
    st.session_state.current_user = "Oscar"

st.info("💡 **Tip:** Select your name in the sidebar on any page to track your personal progress!")

st.markdown("---")

st.markdown("""
### 🎯 Features:

- ✅ Track finger strength training (20mm Edge, Pinch, Wrist Roller)
- 📊 Automatic plate calculator
- 📈 Progress charts & RPE tracking
- 🎯 Goal setting with progress bars & persistence
- 🏆 Leaderboard & competition stats (averaged L/R arms)
- 👤 User profiles with bodyweight tracking
- 📱 Social media export (Instagram Stories ready!)
- 🔥 Training streaks & consistency heatmap
- 🤖 Smart progression recommendations
- ☁️ Cloud sync via Google Sheets
""")

st.markdown("---")

st.markdown("""
### 🚀 Quick Start Guide:

1. **📝 Log Workout** - Record your training session with automatic plate calculations
2. **📊 View Progress** - See your strength gains with interactive charts
3. **🎯 Set Goals** - Track progress towards your strength targets
4. **👤 Update Profile** - Set your bodyweight for accurate relative strength rankings
5. **🏆 Check Leaderboard** - See how you stack up against your crew!
""")

st.markdown("---")
st.caption("💪 Built for climbers, by climbers. Train hard, climb harder!")
