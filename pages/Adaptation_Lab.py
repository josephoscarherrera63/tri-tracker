import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Adaptation Lab", layout="wide")

# THE IDENTIFIER
SHEET_URL = "https://docs.google.com/spreadsheets/d/12zB73yww1IyPSVfhlofLJ4VV7Se-V3iBKd_tnwbRdWM/edit?usp=sharing"

# --- CONNECT & REFRESH ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=SHEET_URL, ttl=0)

if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Discipline'] = df['Discipline'].astype(str).str.strip()
    df['EF'] = pd.to_numeric(df['EF'], errors='coerce')
    df['Decoupling'] = pd.to_numeric(df['Decoupling'], errors='coerce')

st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Adaptation Lab")

# --- SIDEBAR: LOG NEW SESSION ---
with st.sidebar:
    st.header("Log New Session")
    
    discipline = st.selectbox("Discipline", options=["Bike", "Run", "Swim"], key="disc_select")
    
    if discipline == "Run":
        workout_options = ["Aerobic Base Build", "Threshold Intervals", "Hill Repeats", "Easy Recovery Run", "Other"]
    elif discipline == "Bike":
        workout_options = ["Steady State (Post-Intervals)", "Progressive Build (Ride 6)", "Pure Aerobic (Recovery)", "Other"]
    else: 
        workout_options = ["Endurance Swim", "Technique/Drills", "Sprints", "Other"]

    type_selection = st.selectbox("Workout Category", options=workout_options, key="cat_select")
    date_selection = st.date_input("Workout Date", value=datetime.now(), key="date_select")

    # --- DYNAMIC INPUTS ---
    if discipline == "Bike":
        avg_work = st.number_input("Avg Power (Watts)", min_value=0, value=130, key="bike_input")
        work_for_calc = float(avg_work)
        
    elif discipline == "Run":
        st.write("Enter Avg Pace (Min/Mile):")
        col_min, col_sec = st.columns(2)
        m_pace = col_min.number_input("Min", min_value=0, max_value=20, value=9, key="run_m")
        s_pace = col_sec.number_input("Sec", min_value=0, max_value=59, value=30, key="run_s")
        pace_decimal = m_pace + (s_pace / 60)
        # Convert pace to speed index: (1/pace) * 1000
        work_for_calc = (1 / pace_decimal) * 1000 if pace_decimal > 0 else 0
        
    else: # Swim
        avg_mph = st.number_input("Avg Speed (MPH from Garmin)", min_value=0.0, max_value=5.0, value=1.4, step=0.1, key="swim_input")
        # Scale MPH so EF matches the scale of Bike/Run (roughly multiplying by 100)
        work_for_calc = avg_mph * 100

    avg_hr = st.number_input("Avg Heart Rate (BPM)", min_value=1, value=120, key="hr_input")
    drift = st.number_input("Decoupling / Drift (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="drift_input")

    if st.button("Save to Google Sheets", key="save_button"):
        calculated_ef = round(work_for_calc / avg_hr, 4) if avg_hr > 0 else 0
        new_row = pd.DataFrame([{
            "Date": date_selection.strftime("%Y-%m-%d"),
            "Discipline": discipline,
            "Type": type_selection,
            "EF": calculated_ef,
            "Decoupling": float(drift)
        }])
        
        updated_df = pd.concat([df, new_row], ignore_index=True)
        try:
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success(f"Successfully saved {discipline} session!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Save Error: {e}")

# --- DASHBOARD ---
if not df.empty:
    st.subheader("🗓️ Weekly Performance Report")
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=7)
    last_7_days = df[df['Date'] >= cutoff]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sessions (7d)", len(last_7_days))
    green = len(last_7_days[last_7_days['Decoupling'] <= 5.0])
    c2.metric("Stable Sessions", f"{green} ✅")
    if not last_7_days.empty:
        c3.metric("Avg Weekly EF", f"{last_7_days['EF'].mean():.2f}")

    st.divider()
    st.subheader("📈 Aerobic Progress Trends")
    chart_filter = st.radio("Show Trends For:", ["All", "Bike", "Run", "Swim"], horizontal=True, key="filter_radio")
    
    chart_df = df if chart_filter == "All" else df[df['Discipline'] == chart_filter]
    chart_df = chart_df.sort_values(by="Date")
    
    if not chart_df.empty:
        t1, t2 = st.tabs(["Efficiency Factor (EF)", "Decoupling (Drift %)"])
        with t1: st.line_chart(data=chart_df, x="Date", y="EF")
        with t2: st.line_chart(data=chart_df, x="Date", y="Decoupling")
    
    st.divider()
    st.subheader("📊 Recent Raw Data")
    
    def get_status(row):
        if row['Decoupling'] <= 5.0: return "🟢 Aerobically Stable"
        elif row['Decoupling'] <= 8.0: return "🟡 Developing"
        else: return "🔴 High Fatigue"

    display_df = df.copy()
    display_df['Status'] = display_df.apply(get_status, axis=1)
    st.dataframe(display_df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("No data found. Log your first session!")
