import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Adaptation Lab", layout="wide")

# 1. Define the URL globally
SHEET_URL = "https://docs.google.com/spreadsheets/d/12zB73yww1IyPSVfhlofLJ4VV7Se-V3iBKd_tnwbRdWM/edit?usp=sharing"

# 2. Establish Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Read Data
df = conn.read(spreadsheet=SHEET_URL, ttl=0)
df['Date'] = pd.to_datetime(df['Date'])

st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Adaptation Lab")

# --- SIDEBAR: LOG NEW SESSION ---
with st.sidebar:
    st.header("Log New Session")
    
    discipline = st.selectbox("Discipline", options=["Bike", "Run", "Swim"])
    
    workout_options = [
        "Steady State (Post-Intervals)", 
        "Progressive Build (Ride 6)", 
        "Pure Aerobic (Recovery)",
        "Other"
    ]
    type_selection = st.selectbox("Workout Category", options=workout_options)
    
    date_selection = st.date_input("Workout Date", value=datetime.now())

    # Dynamic labels
    if discipline == "Bike":
        work_label, work_value = "Avg Power (Watts)", 130
    elif discipline == "Run":
        work_label, work_value = "Avg Pace (Meters/Min)", 200
    else:
        work_label, work_value = "Avg Speed/Pace", 100

    avg_work = st.number_input(work_label, min_value=0, value=work_value)
    avg_hr = st.number_input("Avg Heart Rate (BPM)", min_value=0, value=120)
    drift = st.number_input("Decoupling / Drift (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    # THE SAVE BUTTON (Inside the Sidebar)
    if st.button("Save to Google Sheets"):
        ef_val = avg_work / avg_hr if avg_hr > 0 else 0
        
        new_row = pd.DataFrame([{
            "Date": date_selection.strftime("%Y-%m-%d"),
            "Discipline": discipline,
            "Type": type_selection,
            "EF": round(ef_val, 4),
            "Decoupling": drift
        }])
        
        try:
            # We use the variable SHEET_URL explicitly here
            conn.create(spreadsheet=SHEET_URL, worksheet="Sheet1", data=new_row)
            st.success("Session Logged! Click 'R' to refresh.")
            st.balloons() # Just for a bit of fun when it finally works!
        except Exception as e:
            st.error(f"Write Error: {e}")

# --- MAIN DASHBOARD SUMMARY ---
if not df.empty:
    st.subheader("🗓️ Weekly Performance Report")
    last_7_days = df[df['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions (7d)", len(last_7_days))
    
    green_lights = len(last_7_days[last_7_days['Decoupling'] <= 5.0])
    col2.metric("Stable Sessions", f"{green_lights} ✅")
    
    if not last_7_days.empty:
        avg_ef = last_7_days['EF'].mean()
        col3.metric("Avg Weekly EF", f"{avg_ef:.2f}")
    
    st.divider()
    
    # Show the table
    st.subheader("📊 Recent Raw Data")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("No data found. Log your first session in the sidebar!")
