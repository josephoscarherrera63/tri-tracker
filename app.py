import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIG ---
SHEET_ID = "YOUR_ID_HERE" 
SCRIPT_URL = "YOUR_EXEC_URL_HERE"

# Connection string for reading
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="Triathlon Training Hub", layout="wide")

# --- 2. DATA LOADING ---
def load_data():
    try:
        # We add a random number to the URL to force Google to give us the freshest data
        data = pd.read_csv(f"{SHEET_URL}&cache={datetime.now().timestamp()}")
        if not data.empty:
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.sort_values('Date', ascending=False)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. SIDEBAR ---
st.sidebar.header("Log Workout")
date_in = st.sidebar.date_input("Date", datetime.now())
sport_in = st.sidebar.selectbox("Sport", ["Swim", "Bike", "Run", "Strength"])
dur_in = st.sidebar.number_input("Duration (mins)", min_value=1, step=5)
dist_in = st.sidebar.number_input("Distance", min_value=0.0, step=0.1)
int_in = st.sidebar.slider("Intensity (1-10)", 1, 10, 5)

if st.sidebar.button("🚀 Log to Google Sheets"):
    params = {
        "date": date_in.strftime("%Y-%m-%d"),
        "sport": sport_in,
        "duration": dur_in,
        "distance": dist_in,
        "intensity": int_in,
        "load": dur_in * int_in
    }
    
    # We send the data and don't "wait" for a complex response to avoid false errors
    try:
        requests.get(SCRIPT_URL, params=params, timeout=5)
        st.sidebar.success("Workout Recorded!")
        st.rerun()
    except:
        # If the data still shows up in your sheet, ignore this!
        st.sidebar.warning("Note: Refresh sheet to verify log.")

# --- 4. DASHBOARD ---
st.title("🏊‍♂️ My Training Dashboard")

if not df.empty:
    # Top Level Metrics
    col1, col2, col3 = st.columns(3)
    total_hrs = round(df['Duration'].sum() / 60, 1)
    total_sessions = len(df)
    avg_intensity = round(df['Intensity'].mean(), 1)
    
    col1.metric("Total Time", f"{total_hrs} Hours")
    col2.metric("Sessions", total_sessions)
    col3.metric("Avg Intensity", f"{avg_intensity}/10")

    # Chart Area
    st.subheader("Weekly Training Load")
    # Group by week and sum the 'Load'
    weekly_df = df.groupby(pd.Grouper(key='Date', freq='W')).sum(numeric_only=True).reset_index()
    fig = px.bar(weekly_df, x='Date', y='Load', 
                 title="Cumulative Stress Score",
                 color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig, use_container_width=True)

    # Activity Table
    st.subheader("Recent Activity")
    st.dataframe(df[['Date', 'Sport', 'Duration', 'Distance', 'Load']], use_container_width=True)
else:
    st.info("Your dashboard is ready! Log a workout in the sidebar to see your stats.")
