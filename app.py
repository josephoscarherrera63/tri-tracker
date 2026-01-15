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
# --- RACE COUNTDOWN ---
race_date = datetime(2026, 6, 21)
days_to_go = (race_date - datetime.now()).days

if days_to_go > 0:
    st.info(f"🗓️ **{days_to_go} Days** until the first Sprint Tri window (June 21)")
    
    # Progress bar towards June 21 (assuming a 20-week build)
    progress = max(0, min(100, int((1 - (days_to_go / 140)) * 100)))
    st.progress(progress, text=f"Season Build: {progress}%")
    
    with st.expander("View Summer Race Schedule"):
        st.write("Targeting one of these Sprint dates:")
        st.write("✅ **June 21** | July 12 | July 26 | August 9")
else:
    st.success("🏁 It's Race Season!")

if not df.empty:
    # --- COACH'S ANALYSIS (With Mid-Week Awareness) ---
    st.subheader("📋 Coach's Analysis")
    df_sorted = df.sort_values('Date')
    weekly_total = df_sorted.groupby(pd.Grouper(key='Date', freq='W-MON')).sum(numeric_only=True).reset_index()
    
    if len(weekly_total) > 1:
        this_week = weekly_total.iloc[-1]['Load']
        last_week = weekly_total.iloc[-2]['Load']
        
        # Check what day of the week it is (0=Mon, 6=Sun)
        day_of_week = datetime.now().weekday()
        
        # If it's Mon-Thu, we acknowledge the week is incomplete
        if day_of_week < 4: 
            st.info(f"⏳ **Mid-Week Status:** You've built {int(this_week)} load points so far. Comparison will be more accurate by Friday!")
        
        increase = ((this_week - last_week) / last_week) * 100 if last_week > 0 else 0

        if day_of_week >= 4: # Only show warnings/success on Fri, Sat, Sun
            if increase > 25:
                st.error(f"🚨 **DANGER:** Load jumped {int(increase)}%. Risk of injury is high.")
            elif increase > 15:
                st.warning(f"⚠️ **PUSHING:** Load up {int(increase)}%. Hold steady next week.")
            elif increase < -20:
                st.success("🧊 **RECOVERY:** Body is absorbing the work. Nice deload.")
            else:
                st.success(f"✅ **SWEET SPOT:** Steady {int(increase)}% progression.")    
    # --- SEASON TOTALS (2026 ONLY) ---
    st.subheader("🏁 2026 Season Totals")
    m_col1, m_col2, m_col3 = st.columns(3)
    
    # Create a filter for just the current year
    current_year = datetime.now().year
    df_2026 = df[df['Date'].dt.year == current_year]
    
    # Calculate distances using only 2026 data
    swim_dist = df_2026[df_2026['Sport'] == 'Swim']['Distance'].sum()
    bike_dist = df_2026[df_2026['Sport'] == 'Bike']['Distance'].sum()
    run_dist = df_2026[df_2026['Sport'] == 'Run']['Distance'].sum()
    
    # Display them
    m_col1.metric("🏊‍♂️ Swim", f"{int(swim_dist)} yds/m")
    m_col2.metric("🚴‍♂️ Bike", f"{round(bike_dist, 1)} miles")
    m_col3.metric("🏃‍♂️ Run", f"{round(run_dist, 1)} miles")

    st.divider()
    # Adds a nice line to separate totals from the rest of the dashboard
    # --- THE HOURLY BAR CHART WITH TREND LINE ---
    st.subheader("Weekly Training Volume (Hours)")
    
    # 1. Prepare data and convert Minutes to Hours
    weekly_sport = df_sorted.groupby([pd.Grouper(key='Date', freq='W-MON'), 'Sport']).sum(numeric_only=True).reset_index()
    weekly_sport['Hours'] = weekly_sport['Duration'] / 60
    
    # 2. Prepare the Trend Line (Moving Average of Hours)
    weekly_totals = weekly_sport.groupby('Date')['Hours'].sum().reset_index()
    weekly_totals['Trend'] = weekly_totals['Hours'].rolling(window=4, min_periods=1).mean()
    
    # 3. Create the Chart
    fig_bar = px.bar(weekly_sport, x='Date', y='Hours', color='Sport',
                 color_discrete_map={"Swim": "#00CC96", "Bike": "#636EFA", "Run": "#EF553B", "Strength": "#AB63FA"})
    
    # 4. Add the Trend Line (Average Hours)
    import plotly.graph_objects as go
    fig_bar.add_trace(
        go.Scatter(
            x=weekly_totals['Date'], 
            y=weekly_totals['Trend'],
            mode='lines+markers',
            name='4-Week Avg',
            line=dict(color='white', width=3, dash='dot')
        )
    )

    fig_bar.update_layout(
        barmode='stack', 
        xaxis_title="Week Commencing", 
        yaxis_title="Total Hours",
        yaxis=dict(ticksuffix=" hrs")
    )
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

