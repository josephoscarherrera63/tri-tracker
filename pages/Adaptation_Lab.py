import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Adaptation Lab", layout="wide")

# --- CONNECT TO GOOGLE SHEETS ---
# Paste your Google Sheet URL here
url = "https://docs.google.com/spreadsheets/d/12zB73yww1IyPSVfhlofLJ4VV7Se-V3iBKd_tnwbRdWM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
# This tells Streamlit to ignore the old "empty" version of the sheet
df = conn.read(spreadsheet=url, ttl=0)
# Load existing data
df = conn.read(spreadsheet=url)
df = conn.read(spreadsheet=url, ttl=0)
df['Date'] = pd.to_datetime(df['Date']) # This makes the chart timeline look pretty

st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Adaptation Lab")

# --- DATA ENTRY ---
with st.sidebar:
    st.header("Log Session")
    date = st.date_input("Workout Date", datetime.now())
    # Separate the 'Work' from the 'Recovery'
steady_state_df = df[df['Type'] == "Steady State (Post-Intervals)"]
recovery_df = df[df['Type'] == "Pure Aerobic (Recovery)"]

# Calculate your 'Baseline Recovery EF' (Average of all recovery rides)
if not recovery_df.empty:
    avg_recovery_ef = recovery_df['EF'].mean()
    latest_recovery_ef = recovery_df['EF'].iloc[-1]
    
    # If your latest recovery is much worse than your average, show a warning
    if latest_recovery_ef < (avg_recovery_ef * 0.95):
        st.warning("⚠️ Fatigue Alert: Your recovery efficiency is lower than usual. Consider an extra rest day.")
    discipline = st.selectbox("Discipline", ["Swim", "Bike", "Run"])
   # --- SIDEBAR INPUTS ---
st.sidebar.header("Log New Session")

# 1. The "Where" and "What"
discipline = st.sidebar.selectbox("Discipline", options=["Bike", "Run", "Swim"])

workout_options = [
    "Steady State (Post-Intervals)", 
    "Progressive Build (Ride 6)", 
    "Pure Aerobic (Recovery)",
    "Other"
]
type_selection = st.sidebar.selectbox("Workout Category", options=workout_options)

date_selection = st.sidebar.date_input("Workout Date")

# 2. The "Data" (This is likely what went missing!)
if discipline == "Bike":
    work_label = "Avg Power (Watts)"
    work_value = 130
elif discipline == "Run":
    work_label = "Avg Pace (Meters/Min)"
    work_value = 200
else:
    work_label = "Avg Speed/Pace"
    work_value = 100

avg_work = st.sidebar.number_input(work_label, min_value=0, value=work_value)
avg_hr = st.sidebar.number_input("Avg Heart Rate (BPM)", min_value=0, value=120)
drift = st.sidebar.number_input("Decoupling / Drift (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

# 3. The Save Button

    # Calculate EF before saving
    ef_val = avg_work / avg_hr if avg_hr > 0 else 0
    
    new_data = pd.DataFrame([{
        "Date": date_selection.strftime("%Y-%m-%d"),
        "Discipline": discipline,
        "Type": type_selection,
        "EF": round(ef_val, 4),
        "Decoupling": drift
    }])
    
    # Append to Google Sheets
    conn.create(data=new_data)
    st.sidebar.success("Session Logged! Refresh to see the chart.")
    # --- UPDATE THIS SECTION ---
if st.sidebar.button("Save to Google Sheets"):
    # Calculate EF before saving
    ef_val = avg_work / avg_hr if avg_hr > 0 else 0
    
    new_data = pd.DataFrame([{
        "Date": date_selection.strftime("%Y-%m-%d"),
        "Discipline": discipline,
        "Type": type_selection,
        "EF": round(ef_val, 4),
        "Decoupling": drift
    }])
    
    # ADD THE URL HERE:
    conn.create(spreadsheet=url, data=new_data) 
    st.sidebar.success("Session Logged! Refresh to see the chart.")
# --- RECOVERY MONITORING LOGIC ---
# Place this after you've defined 'df' (the part where you read from Google Sheets)
if not df.empty:
    recovery_df = df[df['Type'] == "Pure Aerobic (Recovery)"]
    
    if not recovery_df.empty:
        st.subheader("🔋 Recovery & Freshness")
        latest_rec = recovery_df.iloc[-1]
        
        # We compare the latest recovery EF to the average of previous ones
        avg_rec_ef = recovery_df['EF'].mean()
        efficiency_drop = (latest_rec['EF'] / avg_rec_ef) - 1
        
        col1, col2 = st.columns(2)
        col1.metric("Recovery EF", f"{latest_rec['EF']:.2f}", f"{efficiency_drop:.1%}")
        
        if efficiency_drop < -0.05:
            col2.error("🚨 System Fatigued: Efficiency is significantly down. Prioritize sleep.")
        else:
            col2.success("✅ System Ready: Recovery metrics are stable.")

# --- DASHBOARD SUMMARY ---
st.divider()

if not df.empty:
    # Ensure Date is datetime for filtering
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Filter for the last 7 days
    last_7_days = df[df['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
    
    st.subheader("🗓️ Weekly Performance Report")
    col1, col2, col3 = st.columns(3)
    
    # 1. Volume Count
    col1.metric("Sessions (7d)", len(last_7_days))
    
    # 2. Green Light Count
    green_lights = len(last_7_days[last_7_days['Decoupling'] <= 5.0])
    col2.metric("Stable Sessions", f"{green_lights} ✅")
    
    # 3. Avg Efficiency Factor
    if not last_7_days.empty:
        avg_ef = last_7_days['EF'].mean()
        col3.metric("Avg Weekly EF", f"{avg_ef:.2f}")
    else:
        col3.metric("Avg Weekly EF", "N/A")

    # --- RECOVERY & COACH'S REC SECTIONS ---
    # (Keep the Recovery and Recommendation logic we built earlier here)
