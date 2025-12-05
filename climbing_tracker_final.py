import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import json
import warnings

warnings.filterwarnings('ignore')

CSV_FILE = "climbing_log.csv"
SAVED_1RM_FILE = "1rm_reference.json"
PLATE_SIZES = [20, 15, 10, 5, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.25]

QUICK_NOTES = {"💪 Strong": "Strong", "😴 Tired": "Tired", "🤕 Hand pain": "Hand pain", "😤 Hard": "Hard", "✨ Great": "Great"}

EXERCISE_PLAN = {
    "20mm Edge (L)": {"Schedule": "Mon & Thu", "Frequency": "2x/week", "Sets": "3-4", "Reps": "3-5", "Rest": "3-5min", "Intensity": "80-85%", "Technique": ["Crimp grip", "Dead hang", "Shoulders packed", "Control descent"]},
    "20mm Edge (R)": {"Schedule": "Mon & Thu", "Frequency": "2x/week", "Sets": "3-4", "Reps": "3-5", "Rest": "3-5min", "Intensity": "80-85%", "Technique": ["Crimp grip", "Dead hang", "Shoulders packed", "Control descent"]},
    "Pinch (L)": {"Schedule": "Tue & Sat", "Frequency": "2x/week", "Sets": "3-4", "Reps": "5-8", "Rest": "2-3min", "Intensity": "75-80%", "Technique": ["Pinch hold", "Arms straight", "Squeeze at top", "Lower slowly"]},
    "Pinch (R)": {"Schedule": "Tue & Sat", "Frequency": "2x/week", "Sets": "3-4", "Reps": "5-8", "Rest": "2-3min", "Intensity": "75-80%", "Technique": ["Pinch hold", "Arms straight", "Squeeze at top", "Lower slowly"]},
    "Wrist Roller (L)": {"Schedule": "Wed & Sun", "Frequency": "2x/week", "Sets": "2-3", "Reps": "Full ROM", "Rest": "2min", "Intensity": "50-60%", "Technique": ["Arms extended", "Roll forward", "Roll backward", "Slow & controlled"]},
    "Wrist Roller (R)": {"Schedule": "Wed & Sun", "Frequency": "2x/week", "Sets": "2-3", "Reps": "Full ROM", "Rest": "2min", "Intensity": "50-60%", "Technique": ["Arms extended", "Roll forward", "Roll backward", "Slow & controlled"]}
}

st.set_page_config(page_title="Yves Tracker", layout="wide", initial_sidebar_state="collapsed")
st.title("🧗 Yves Arm-Lifting Tracker")

is_mobile = st.query_params.get("mobile", "false").lower() == "true"

if not os.path.exists(CSV_FILE):
    df_template = pd.DataFrame(columns=["Date", "Exercise", "1RM_Reference", "Target_Percentage", "Prescribed_Load_kg", "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE", "Notes"])
    df_template.to_csv(CSV_FILE, index=False)

if not os.path.exists(SAVED_1RM_FILE):
    default_1rms = {"20mm Edge (L)": 105, "20mm Edge (R)": 105, "Pinch (L)": 85, "Pinch (R)": 85, "Wrist Roller (L)": 75, "Wrist Roller (R)": 75}
    with open(SAVED_1RM_FILE, "w") as f:
        json.dump(default_1rms, f, indent=2)

with open(SAVED_1RM_FILE, "r") as f:
    saved_1rms = json.load(f)

df = pd.read_csv(CSV_FILE)

def calculate_plates(target_kg, pin_kg=1):
    load_per_side = (target_kg - pin_kg) / 2
    best_diff, best_load, best_plates = float('inf'), target_kg, []
    for multiplier in range(int(load_per_side * 4) - 5, int(load_per_side * 4) + 10):
        test_per_side, test_total = multiplier / 4, multiplier / 4 * 2 + pin_kg
        if test_total > target_kg + 3 or test_total < target_kg - 3:
            continue
        plates, remaining = [], test_per_side
        for plate in PLATE_SIZES:
            while remaining >= plate - 0.001:
                plates.append(plate)
                remaining -= plate
        if remaining < 0.001:
            diff = abs(test_total - target_kg)
            if diff < best_diff:
                best_diff, best_load, best_plates = diff, test_total, sorted(plates, reverse=True)
    if best_plates:
        plates_str = f"{' + '.join(map(str, best_plates))} kg per side"
        return plates_str, best_load
    return "No exact combo found", target_kg

def estimate_1rm_epley(load_kg, reps):
    return load_kg if reps == 1 else load_kg * (1 + reps / 30)

def save_1rms(rms_dict):
    with open(SAVED_1RM_FILE, "w") as f:
        json.dump(rms_dict, f, indent=2)

st.sidebar.header("💾 1RM Manager")
st.sidebar.subheader("Save your max lifts:")
exercise_list = ["20mm Edge (L)", "20mm Edge (R)", "Pinch (L)", "Pinch (R)", "Wrist Roller (L)", "Wrist Roller (R)"]

for ex in exercise_list:
    saved_1rms[ex] = st.sidebar.number_input(f"{ex} MVC-7 (kg)", min_value=20, max_value=200, value=saved_1rms.get(ex, 105), step=1, key=f"1rm_{ex}")

if st.sidebar.button("💾 Save All 1RMs", key="save_1rms_btn", use_container_width=True):
    save_1rms(saved_1rms)
    st.sidebar.success("✅ 1RMs saved!")

st.sidebar.markdown("---")
st.sidebar.header("📋 Exercise Plan")
if st.sidebar.button("📖 View Plan", key="view_plan_btn", use_container_width=True):
    st.session_state.show_plan = not st.session_state.get("show_plan", False)

if st.session_state.get("show_plan", False):
    st.sidebar.markdown("---")
    selected_plan_exercise = st.sidebar.selectbox("Choose exercise:", exercise_list, key="plan_select")
    plan = EXERCISE_PLAN[selected_plan_exercise]
    st.sidebar.subheader(f"📅 {selected_plan_exercise}")
    for key in ["Schedule", "Frequency", "Sets", "Reps", "Rest", "Intensity"]:
        st.sidebar.write(f"**{key}:** {plan[key]}")
    st.sidebar.subheader("🎯 Technique Tips:")
    for tip in plan["Technique"]:
        st.sidebar.write(f"• {tip}")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Calculator")
selected_exercise = st.sidebar.selectbox("Exercise", exercise_list, key="exercise_select")
current_1rm = saved_1rms.get(selected_exercise, 105)

intensity_options = {"50% Warm-up": 0.50, "60% Warm-up": 0.60, "70% Warm-up": 0.70, "80% Work": 0.80, "Custom": None}
intensity_label = st.sidebar.selectbox("Intensity", list(intensity_options.keys()), key="intensity_select")
target_pct = st.sidebar.slider("Custom %", min_value=0.3, max_value=1.0, step=0.05, value=0.8) if intensity_label == "Custom" else intensity_options[intensity_label]

prescribed_load = current_1rm * target_pct
st.sidebar.markdown("---")
st.sidebar.subheader(f"📊 Target Load: **{prescribed_load:.1f} kg**")
plates_str, actual_load = calculate_plates(prescribed_load)
st.sidebar.write(f"**Plates:** {plates_str}")
st.sidebar.write(f"**Total weight: {actual_load:.1f} kg**")

st.header("📝 Log Today's Session")

if is_mobile or st.session_state.get("is_mobile", False):
    actual_load = st.number_input("Actual Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load, step=0.5)
    reps = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1)
    sets = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1)
    rpe = st.slider("RPE", min_value=1, max_value=10, value=7)
    quick_note = st.selectbox("Quick note:", ["None"] + list(QUICK_NOTES.keys()), key="quick_note_select")
    quick_note_text = QUICK_NOTES.get(quick_note, "") if quick_note != "None" else ""
    notes = st.text_input("Custom notes", placeholder="e.g., felt strong")
    full_notes = f"{quick_note_text} {notes}".strip()
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        actual_load = st.number_input("Actual Load (kg)", min_value=10.0, max_value=200.0, value=prescribed_load, step=0.5)
    with col2:
        reps = st.number_input("Reps", min_value=1, max_value=20, value=4, step=1)
    with col3:
        sets = st.number_input("Sets", min_value=1, max_value=10, value=4, step=1)
    col4, col5, col6 = st.columns(3)
    with col4:
        rpe = st.slider("RPE", min_value=1, max_value=10, value=7)
    with col5:
        quick_note = st.selectbox("Quick note:", ["None"] + list(QUICK_NOTES.keys()), key="quick_note_select")
        quick_note_text = QUICK_NOTES.get(quick_note, "") if quick_note != "None" else ""
    with col6:
        notes = st.text_input("Custom notes", placeholder="e.g., felt strong")
        full_notes = f"{quick_note_text} {notes}".strip()

if st.button("✅ Save Workout", key="save_btn", use_container_width=True):
    new_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Exercise": selected_exercise, "1RM_Reference": current_1rm, "Target_Percentage": target_pct, "Prescribed_Load_kg": prescribed_load, "Actual_Load_kg": actual_load, "Reps_Per_Set": reps, "Sets_Completed": sets, "RPE": rpe, "Notes": full_notes}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    st.success(f"✅ Logged {selected_exercise}: {actual_load} kg x {reps} x {sets} @ RPE {rpe}")
    st.rerun()

st.markdown("---")
st.header("📈 Progress")

df_fresh = pd.read_csv(CSV_FILE)
if len(df_fresh) > 0:
    exercise_options = df_fresh["Exercise"].unique().tolist()
    selected_analysis_exercise = st.selectbox("View progress for:", exercise_options, key="analysis_exercise")
    df_filtered = df_fresh[df_fresh["Exercise"] == selected_analysis_exercise].copy()
    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
    df_filtered = df_filtered.sort_values("Date").reset_index(drop=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Best Load", f"{df_filtered['Actual_Load_kg'].max():.1f} kg")
    with col2:
        st.metric("Avg RPE", f"{df_filtered['RPE'].mean():.1f} / 10")
    with col3:
        total_volume = (df_filtered["Actual_Load_kg"] * df_filtered["Reps_Per_Set"] * df_filtered["Sets_Completed"]).sum()
        st.metric("Total Volume", f"{total_volume:.0f} kg")
    with col4:
        st.metric("Sessions", len(df_filtered))
    
    st.subheader("Load Over Time")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df_filtered["Date"], df_filtered["Actual_Load_kg"], marker="o", label="Load", linewidth=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Load (kg)")
    ax.set_title(f"{selected_analysis_exercise} Progress")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    
    st.subheader("Workout Log")
    display_cols = ["Date", "Exercise", "Actual_Load_kg", "Reps_Per_Set", "Sets_Completed", "RPE", "Notes"]
    st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No workouts logged yet!")
