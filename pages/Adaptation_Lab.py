import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Adaptation Lab", layout="wide")

# THE IDENTIFIER
SHEET_URL = "https://docs.google.com/spreadsheets/d/12zB73yww1IyPSVfhlofLJ4VV7Se-V3iBKd_tnwbRdWM/edit?usp=sharing"

# CONNECT
conn = st.connection("gsheets", type=GSheetsConnection)

# --- REFRESH DATA ---
df = conn.read(spreadsheet=SHEET_URL, ttl=0)
if not df.empty:
    df = df.dropna(subset=['Date'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['EF'] = pd.to_numeric(df['EF'], errors='coerce')
    df['Decoupling'] = pd.to_numeric(df['Decoupling'], errors='coerce')

st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Adaptation Lab")

# --- SIDEBAR: LOG NEW SESSION ---
with st.sidebar:
    st.header("Log New Session")
    
    discipline = st.selectbox("Discipline", options=["Bike", "Run", "Swim"])
    
    # Custom options based on discipline
    if discipline == "Run":
        workout_options = ["Aerobic Base Build", "Threshold Intervals", "Hill Repeats", "Easy Recovery Run", "Other"]
    elif discipline == "Bike":
        workout_options = ["Steady State (Post-Intervals)", "Progressive Build (Ride 6)", "Pure Aerobic (Recovery)", "Other"]
    else: 
        workout_options = ["Endurance Sets", "Technique/Drills", "Sprints", "Other"]

    type_selection = st.selectbox("Workout Category", options=workout_options)
    date_selection = st.date_input("Workout Date", value=datetime.now())

    # --- DYNAMIC INPUTS ---
    if discipline == "Bike":
        avg_work = st.number_input("Avg Power (Watts)", min_value=0, value=130)
        work_for_calc = avg_work
    elif discipline == "Run":
        st.write("Enter Avg Pace:")
        col_min, col_sec = st.columns(2)
        m_pace = col_min.number_input("Min", min_value=0, max_value=20, value=9)
        s_pace = col_sec.number_input("Sec", min_value=0, max_value=59, value=30)
        pace_decimal = m_pace + (s_pace / 60)
        # Flip pace to speed for EF calculation
        work_for_calc = (1 / pace_decimal) * 1000 if pace_decimal > 0 else 0
    else:
        work_for_calc = st.number_input("Avg Speed/Pace", min_value=0, value=100)

    avg_hr = st.number_input("Avg Heart Rate (BPM)", min_value=0, value=120)
    drift = st.number_input("Decoupling / Drift (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    if st.button("Save to Google Sheets"):
        ef_val = work_for_calc / avg_hr if avg_hr > 0 else 0
        new_row = pd.DataFrame([{
            "Date": date_selection.strftime("%Y-%m-%d"),
            "Discipline": discipline,
            "Type": type_selection,
            "EF": round(ef_val, 4),
            "Decoupling": drift
        }])
        
        updated_df = pd.concat([df, new_row], ignore_index=True)
        try:
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success("Session Logged! Refresh to update charts.")
            st.balloons()
        except Exception as e:
            st.error(f"Save Error: {e}")

# --- MAIN DASHBOARD ---
if not df.empty:
    st.subheader("🗓️ Weekly Performance Report")
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=7)
    last_7_days = df[df['Date'] >= cutoff]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions (7d)", len(last_7_days))
    green_lights = len(last_7_days[last_7_days['Decoupling'] <= 5.0])
    col2.metric("Stable Sessions", f"{green_lights} ✅")
    if not last_7_days.empty:
        avg_ef = last_7_days['EF'].mean()
        col3.metric("Avg Weekly EF", f"{avg_ef:.2f}")
    
    st.divider()

    # --- STATUS TAGS ---
    def get_status(row):
        if row['Decoupling'] <= 5.0: return "🟢 Aerobically Stable"
        elif row['Decoupling'] <= 8.0: return "🟡 Developing"
        else: return "🔴 High Fatigue"

    display_df = df.copy()
    display_df['Status'] = display_df.apply(get_status, axis=1)
    
    st.subheader("📊 Recent Raw Data")
    st.dataframe(
        display_df.sort_values(by="Date", ascending=False), 
        use_container_width=True,
        column_order=("Date", "Discipline", "Type", "EF", "Decoupling", "Status")
    )

    # --- TREND CHART WITH FILTER ---
    st.divider()
    st.subheader("📈 Aerobic Progress Trends")
    
    # Filter for the charts
    chart_filter = st.radio("Show Trends For:", ["All", "Bike", "Run", "Swim"], horizontal=True)
    
    if chart_filter == "All":
        chart_df = df.sort_values(by="Date")
    else:
        chart_df = df[df['Discipline'] == chart_filter].sort_values(by="Date")
    
    if not chart_df.empty:
        tab1, tab2 = st.tabs(["Efficiency Factor (EF)", "Decoupling (Drift %)"])
        
        with tab1:
            st.line_chart(data=chart_df, x="Date", y="EF")
            st.caption(f"Tracking your output-to-HR ratio for {chart_filter}")
            
        with tab2:
            # We add a horizontal line at 5% in our minds as the 'Stability' threshold
            st.line_chart(data=chart_df, x="Date", y="Decoupling")
            st.caption("Goal: Keep these points below 5.0 for 'Stable' status.")
    else:
        st.write(f"No {chart_filter} data logged yet to show a trend.")
