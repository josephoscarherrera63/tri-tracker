import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Adaptation Lab", layout="wide")

# --- CONNECT TO GOOGLE SHEETS ---
url = "https://docs.google.com/spreadsheets/d/12zB73yww1IyPSVfhlofLJ4VV7Se-V3iBKd_tnwbRdWM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Load existing data with no cache (ttl=0) to ensure we see new entries immediately
df = conn.read(spreadsheet=url, ttl=0)
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

    # Dynamic labels based on Discipline
    if discipline == "Bike":
        work_label = "Avg Power (Watts)"
        work_value = 130
    elif discipline == "Run":
        work_label = "Avg Pace (Meters/Min)"
        work_value = 200
    else:
        work_label = "Avg Speed/Pace"
        work_value = 100

    avg_work = st.number_input(work_label, min_value=0, value=work_value)
    avg_hr = st.number_input("Avg Heart Rate (BPM)", min_value=0, value=120)
    drift = st.number_input("Decoupling / Drift (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    if st.button("Save to Google Sheets"):
        # Calculate EF automatically
        ef_val = avg_work / avg_hr if avg_hr > 0 else 0
        
        new_row = pd.DataFrame([{
            "Date": date_selection.strftime("%Y-%m-%d"),
            "Discipline": discipline,
            "Type": type_selection,
            "EF": round(ef_val, 4),
            "Decoupling": drift
        }])
        
        # Write back to Google Sheets
        conn.create(spreadsheet=url, data=new_row)
        st.success("Session Logged! Refresh the page to update charts.")

# --- MAIN DASHBOARD ---

if not df.empty:
    # 1. WEEKLY PERFORMANCE REPORT
    st.subheader("🗓️ Weekly Performance Report")
    
    # Filter for the last 7 days
    last_7_days = df[df['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions (7d)", len(last_7_days))
    
    green_lights = len(last_7_days[last_7_days['Decoupling'] <= 5.0])
    col2.metric("Stable Sessions", f"{green_lights} ✅")
    
    if not last_7_days.empty:
        avg_ef = last_7_days['EF'].mean()
        col3.metric("Avg Weekly EF", f"{avg_ef:.2f}")
    else:
        col3.metric("Avg Weekly EF", "N/A")

    st.divider()

    # 2. RECOVERY & FRESHNESS GAUGE
    recovery_df = df[df['Type'] == "Pure Aerobic (Recovery)"]
    if not recovery_df.empty:
        st.subheader("🔋 Recovery & Freshness")
        latest_rec = recovery_df.iloc[-1]
        avg_rec_ef = recovery_df['EF'].mean()
        efficiency_drop = (latest_rec['EF'] / avg_rec_ef) - 1
        
        r_col1, r_col2 = st.columns(2)
        r_col1.metric("Latest Recovery EF", f"{latest_rec['EF']:.2f}", f"{efficiency_drop:.1%}")
        
        if efficiency_drop < -0.05:
            r_col2.error("🚨 Fatigue Alert: Recovery efficiency is down. Take it easy!")
        else:
            r_col2.success("✅ System Ready: Your aerobic engine is recovering well.")
    
    st.divider()

    # 3. DATA PREVIEW
    st.subheader("📊 Recent Raw Data")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

else:
    st.info("No data found. Log your first session in the sidebar!")
