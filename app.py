import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Tri-Base Builder", layout="wide")

# --- DATA STORAGE ---
DATA_FILE = "training_log.csv"

try:
    df = pd.read_csv(DATA_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
except FileNotFoundError:
    df = pd.DataFrame(columns=["Date", "Sport", "Duration", "Distance", "Intensity", "Load"])

# --- SIDEBAR ---
st.sidebar.header("Log Session")
date = st.sidebar.date_input("Date", datetime.now())
sport = st.sidebar.selectbox("Sport", ["Swim", "Bike", "Run", "Strength", "Yoga/Mobility"])
duration = st.sidebar.number_input("Duration (mins)", min_value=0, step=5)
distance = st.sidebar.number_input("Distance (km/m)", min_value=0.0, step=0.1, help="Use km for Bike/Run, meters for Swim")
intensity = st.sidebar.slider("Intensity (1-10)", 1, 10, 5)

if st.sidebar.button("Save Workout"):
    load = duration * intensity
    new_row = pd.DataFrame([[pd.to_datetime(date), sport, duration, distance, intensity, load]], 
                            columns=["Date", "Sport", "Duration", "Distance", "Intensity", "Load"])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.rerun()

# --- DASHBOARD ---
st.title("🏊‍♂️ Triathlon Base Builder")

if not df.empty:
    # KPI Totals
    total_mins = df['Duration'].sum()
    total_sessions = len(df)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Training Time", f"{total_mins} mins")
    col2.metric("Total Sessions", total_sessions)
    col3.metric("Last Session", df.iloc[-1]['Sport'])

    # Charts Row
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Discipline Split")
        fig_pie = px.pie(df, values='Duration', names='Sport', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("Weekly Load")
        df = df.sort_values('Date')
        weekly = df.groupby(pd.Grouper(key='Date', freq='W-MON')).sum(numeric_only=True).reset_index()
        fig_bar = px.bar(weekly, x='Date', y='Load', color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_bar, use_container_width=True)

    # Historical Data Table
    st.subheader("Recent Activity")
    st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.info("Log your first workout to see your base-building stats!")
