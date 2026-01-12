import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- APP CONFIG ---
st.set_page_config(page_title="Tri-Volume Tracker", layout="centered")
st.title("🏊‍♂️ Tri-Volume Coach")

# --- DATA STORAGE ---
# In a real app, we'd use a database, but for V1 we'll use a CSV file.
DATA_FILE = "training_log.csv"

try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Date", "Sport", "Duration", "Intensity"])

# --- SIDEBAR: LOG WORKOUT ---
st.sidebar.header("Log Your Session")
date = st.sidebar.date_input("Date", datetime.now())
sport = st.sidebar.selectbox("Sport", ["Swim", "Bike", "Run", "Strength"])
duration = st.sidebar.number_input("Duration (mins)", min_value=0, step=5)
intensity = st.sidebar.slider("Intensity (RPE 1-10)", 1, 10, 5)

if st.sidebar.button("Add Workout"):
    new_data = pd.DataFrame([[date, sport, duration, intensity]], 
                            columns=["Date", "Sport", "Duration", "Intensity"])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success("Session Saved!")

# --- ENGINE: CALCULATE WEEKLY TOTALS ---
df['Date'] = pd.to_datetime(df['Date'])
# Group by week (starting Monday)
weekly_totals = df.groupby(pd.Grouper(key='Date', freq='W-MON'))['Duration'].sum().reset_index()

# --- THE COACH'S BRAIN ---
if len(weekly_totals) > 0:
    current_week_vol = weekly_totals.iloc[-1]['Duration']
    
    st.subheader("📊 Training Status")
    col1, col2 = st.columns(2)
    col1.metric("This Week's Volume", f"{current_week_vol} mins")

    if len(weekly_totals) > 1:
        prev_week_vol = weekly_totals.iloc[-2]['Duration']
        increase = ((current_week_vol - prev_week_vol) / prev_week_vol) * 100
        
        # Logic Check
        if len(weekly_totals) % 4 == 0:
            st.warning("🚨 COACH SAYS: You've completed 3 weeks of build. This should be a **DELOAD WEEK**. Aim for 30% less volume.")
        elif increase > 10:
            st.error(f"⚠️ CAUTION: Your volume increased by {increase:.1f}%. Keep it under 10% to stay injury-free!")
        else:
            st.success(f"✅ Steady Progress: Volume is up {increase:.1f}%. You are in the green zone.")

# --- VISUALIZATION ---
st.subheader("Volume Trend")
st.line_chart(data=weekly_totals, x='Date', y='Duration')

st.subheader("Recent Sessions")
st.table(df.tail(5))
