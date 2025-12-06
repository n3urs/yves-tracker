import streamlit as st

st.set_page_config(page_title="Yves Tracker", page_icon="🧗", layout="wide")

st.title("🧗 Yves Arm-Lifting Tracker")
st.markdown("### Welcome to your climbing strength training app!")

st.markdown("---")

# Quick navigation
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_📝_Log_Workout.py", label="📝 Log Workout", use_container_width=True)
    st.caption("Record your training session")

with col2:
    st.page_link("pages/2_📊_Progress.py", label="📊 View Progress", use_container_width=True)
    st.caption("Analyze your gains")

with col3:
    st.page_link("pages/3_🎯_Goals.py", label="🎯 Goals & Sharing", use_container_width=True)
    st.caption("Set goals & share results")

with col4:
    st.page_link("pages/4_🏆_Leaderboard.py", label="🏆 Leaderboard", use_container_width=True)
    st.caption("Compete with your crew")

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
- 🎯 Goal setting with progress bars
- 🏆 Leaderboard & competition stats
- 📱 Social media export
- 🔥 Training streaks & consistency heatmap
- 🤖 Smart progression recommendations
""")
