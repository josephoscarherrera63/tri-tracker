import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIG (RE-PASTE YOUR KEYS HERE) ---
SHEET_ID = "184l-kXElCBotL4dv0lzyH1_uzQTtZuFkM5obZtsewBQ" 
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzCUgz0fDWf4QQxzbTCP1zh-KsEDWR9IFG5qlljjNaf8XFus6UKVcCjUTdyhSiNWSbV/exec"

# Connection string for reading
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="Triathlon Training Hub", layout="wide")

# --- 2. DATA LOADING ---
def load_data():
    try:
        data = pd.read_csv(f"{SHEET_URL}&cache={datetime.now().timestamp()}")
        if not data.empty:
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.sort_values('Date', ascending=False)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. SIDEBAR (Mobile-Friendly Form) ---
st.sidebar.header("Log Workout")
with st.sidebar.form("workout_form", clear_on_submit=True):
    date_in = st.date_input("Date", datetime.now())
    sport_in = st.selectbox("Sport", ["Swim", "Bike", "Run", "Strength"])
    dur_in = st.number_input("Duration (mins)", min_value=1, step=5)
    dist_in = st.number_input("Distance", min_value=0.0, step=0.1)
    int_in = st.slider("Intensity (1-10)", 1, 10, 5)
    submit_button = st.form_submit_button("🚀 Log to Google Sheets")

if submit_button:
    params = {
        "date": date_in.strftime("%Y-%m-%d"),
        "sport": sport_in,
        "duration": dur_in,
        "distance": dist_in,
        "intensity": int_in,
        "load": dur_in * int_in
    }
    try:
        requests.get(SCRIPT_URL, params=params, timeout=5)
        st.sidebar.success("Workout Recorded!")
        st.rerun()
    except:
        st.sidebar.warning("Syncing... Refresh in a moment.")

# --- 4. DASHBOARD ---
st.title("🏊‍♂️ My Training Dashboard")

if not df.empty:
    # --- COACH'S ANALYSIS ---
    st.subheader("📋 Coach's Analysis")
    df_sorted = df.sort_values('Date')
    weekly_total = df_sorted.groupby(pd.Grouper(key='Date', freq='W-MON')).sum(numeric_only=True).reset_index()
    
    if len(weekly_total) > 1:
        this_week = weekly_total.iloc[-1]['Load']
        last_week = weekly_total.iloc[-2]['Load']
        increase = ((this_week - last_week) / last_week) * 100 if last_week > 0 else 0

        if increase > 25:
            st.error(f"🚨 **DANGER:** Load jumped {int(increase)}%. Risk of injury is high.")
        elif increase > 15:
            st.warning(f"⚠️ **PUSHING:** Load up {int(increase)}%. Hold steady next week.")
        elif increase < -20:
            st.success("🧊 **RECOVERY:** Body is absorbing the work. Nice deload.")
        else:
            st.success(f"✅ **SWEET SPOT:** Steady {int(increase)}% progression.")
    
    # --- METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Time", f"{round(df['Duration'].sum() / 60, 1)} Hours")
    col2.metric("Sessions", len(df))
    col3.metric("Avg Intensity", f"{round(df['Intensity'].mean(), 1)}/10")

    # --- THE MULTI-COLOR BAR CHART ---
    st.subheader("Weekly Training Load by Sport")
    # Group by Week AND Sport for the colors
    weekly_sport = df_sorted.groupby([pd.Grouper(key='Date', freq='W-MON'), 'Sport']).sum(numeric_only=True).reset_index()
    
    fig_bar = px.bar(weekly_sport, x='Date', y='Load', color='Sport',
                 color_discrete_map={"Swim": "#00CC96", "Bike": "#636EFA", "Run": "#EF553B", "Strength": "#AB63FA"})
    fig_bar.update_layout(barmode='stack', xaxis_title="Week Commencing", yaxis_title="Training Load")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- PIE CHART & TABLE ---
    st.subheader("Discipline Breakdown")
    sport_df = df.groupby('Sport')['Duration'].sum().reset_index()
    fig_pie = px.pie(sport_df, values='Duration', names='Sport', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Recent Activity")
    st.dataframe(df[['Date', 'Sport', 'Duration', 'Distance', 'Load']], use_container_width=True)
else:
    st.info("Awaiting training data...")
