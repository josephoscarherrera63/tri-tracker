import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Adaptation Lab", layout="wide")

# THE IDENTIFIER
SHEET_URL = "https://docs.google.com/spreadsheets/d/12zB73yww1IyPSVfhlofLJ4VV7Se-V3iBKd_tnwbRdWM/edit?usp=sharing"

# --- CONNECT & REFRESH ---
conn = st.connection("gsheets", type=GSheetsConnection)

# ttl=0 ensures we always pull fresh data from the Google Sheet
df = conn.read(spreadsheet=SHEET_URL, ttl=0)

if not df.empty:
    # Scrub the data to ensure filtering works
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Discipline'] = df['Discipline'].astype(str).str.strip()
    df['EF'] = pd.to_numeric(df['EF'], errors='coerce')
    df['Decoupling'] = pd.to_numeric(df['Decoupling'], errors='coerce')

st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Adaptation Lab")

# --- SIDEBAR: LOG NEW SESSION ---
with st.sidebar:
    st.header("Log New Session")
    
    discipline = st.selectbox("Discipline", options=["Bike", "Run", "Swim"], key="main_disc")
    
    if discipline == "Run":
        workout_options = ["Aerobic Base Build", "Threshold Intervals", "Hill Repeats", "Easy Recovery Run", "Other"]
    elif discipline == "Bike":
        workout_options = ["Steady State (Post-Intervals)", "Progressive Build (Ride 6)", "Pure Aerobic (Recovery)", "Other"]
    else: 
        workout_options = ["Endurance Sets", "Technique/Drills", "Sprints", "Other"]

    type_selection = st.selectbox("Workout Category", options=workout_options, key="work_type")
    date_selection = st.date_input("Workout Date", value=datetime.now(), key="work_date")

    # --- DYNAMIC INPUTS ---
    if discipline == "Bike":
        avg_work = st.number_input("Avg Power (Watts)", min_value=0, value=130, key="bike_watts")
        work_for_calc = float(avg_work)
    elif discipline == "Run":
        st.write("Enter Avg Pace:")
        col_min, col_sec = st.columns(2)
        m_pace = col_min.number_input("Min", min_value=0, max_value=20, value=9, key="run_min")
        s_pace = col_sec.number_input("Sec", min_value=0, max_value=59, value=30, key="run_sec")
        pace_decimal = m_pace + (s_pace / 60)
        work_for_calc = (1 / pace_decimal) * 1000 if pace_decimal > 0 else 0
    else:
        work_for_calc = st.number_input("Avg Speed/Pace", min_value=0.0, value=100.0, key="swim_speed")

    avg_hr = st.number_input("Avg Heart Rate (BPM)", min_value=1, value=120, key="avg_hr_input")
    drift = st.number_input("Decoupling / Drift (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="drift_input")

    if st.button("Save to Google Sheets", key="save_btn"):
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

# --- MAIN DASHBOARD ---
if not df.empty:
    st.subheader("🗓️ Weekly Performance Report")
    
    # Filter for last 7 days
    now = pd.Timestamp.now().normalize()
    cutoff = now - pd.Timedelta(days=7)
    last_7_days = df[df['Date'] >= cutoff]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions (7d)", len(last_7_days))
    
    green_lights = len(last_7_days[last_7_days['Decoupling'] <= 5.0])
    col2.metric("Stable Sessions", f"{green_lights} ✅")
    
    if not last_7_days.empty:
        avg_ef = last_7_days['EF'].mean()
        col3.metric("Avg Weekly EF", f"{avg_ef:.2f}")
    
    st.divider()

    # --- STATUS LOGIC ---
    def get_status(row):
        if row['Decoupling'] <= 5.0: return "🟢 Aerobically Stable"
        elif row['Decoupling'] <= 8.0: return "🟡 Developing"
        else: return "🔴 High Fatigue"

    display_df = df.copy()
    display_df['Status'] = display_df.apply(get_status, axis=1)
    
    # --- TREND CHART WITH FILTER ---
    st.subheader("📈 Aerobic Progress Trends")
    chart_filter = st.radio("Show Trends For:", ["All", "Bike", "Run", "Swim"], horizontal=True, key="chart_filter_radio")
    
    if chart_filter == "All":
        chart_df = df.sort_values(by="Date")
    else:
        chart_df = df[df['Discipline'] == chart_filter].sort_values(by="Date")
    
    if not chart_df.empty:
        tab1, tab2 = st.tabs(["Efficiency Factor (EF)", "Decoupling (Drift %)"])
        with tab1:
            st.line_chart(data=chart_df, x="Date", y="EF")
        with tab2:
            st.line_chart(data=chart_df, x="Date", y="Decoupling")
    else:
        st.info(f"No {chart_filter} data found for charts.")

    st.divider()
    st.subheader("📊 Recent Raw Data")
    st.dataframe(
        display_df.sort_values(by="Date", ascending=False), 
        use_container_width=True,
        column_order=("Date", "Discipline", "Type", "EF", "Decoupling", "Status")
    )
else:
    st.info("No data found. Log your first session!")
