import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

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
    # --- DATE FILTER (In Sidebar) ---
st.sidebar.divider()
st.sidebar.subheader("📅 View Options")
time_frame = st.sidebar.selectbox(
    "Select Time Frame",
    ["All Time", "Year to Date", "Last 90 Days", "Last 30 Days"]
)

# Filter logic
today = datetime.now()
if time_frame == "Year to Date":
    df_filtered = df[df['Date'].dt.year == today.year]
elif time_frame == "Last 90 Days":
    df_filtered = df[df['Date'] >= (today - timedelta(days=90))]
elif time_frame == "Last 30 Days":
    df_filtered = df[df['Date'] >= (today - timedelta(days=30))]
else:
    df_filtered = df

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

# --- DATE FILTER (Internal Logic) ---
# We use df_filtered for the charts/coach, but keep df for Lifetime stats
today = datetime.now()
if time_frame == "Year to Date":
    df_filtered = df[df['Date'].dt.year == today.year]
elif time_frame == "Last 90 Days":
    df_filtered = df[df['Date'] >= (today - timedelta(days=90))]
elif time_frame == "Last 30 Days":
    df_filtered = df[df['Date'] >= (today - timedelta(days=30))]
else:
    df_filtered = df

if not df_filtered.empty:
    # --- COACH'S ANALYSIS ---
    st.subheader("📋 Coach's Analysis")
    df_sorted = df_filtered.sort_values('Date')
    
    weekly_total = df_sorted.groupby(pd.Grouper(key='Date', freq='W-MON')).sum(numeric_only=True).reset_index()
    
    if len(weekly_total) > 1:
        this_week = weekly_total.iloc[-1]['Load']
        last_week = weekly_total.iloc[-2]['Load']
        day_of_week = datetime.now().weekday()
        
        if day_of_week < 4: 
            st.info(f"⏳ **Mid-Week Status:** {int(this_week)} load points built. Check back Friday for your weekly grade!")
        
        increase = ((this_week - last_week) / last_week) * 100 if last_week > 0 else 0

        if day_of_week >= 4:
            if increase > 25:
                st.error(f"🚨 **DANGER:** Load jumped {int(increase)}%. Risk of injury is high.")
            elif increase > 15:
                st.warning(f"⚠️ **PUSHING:** Load up {int(increase)}%. Hold steady next week.")
            elif increase < -20:
                st.success("🧊 **RECOVERY:** Body is absorbing the work.")
            else:
                st.success(f"✅ **SWEET SPOT:** Steady {int(increase)}% progression.")
    
    # --- SEASON TOTALS (Always 2026) ---
    st.subheader(f"🏁 {today.year} Season Totals")
    m_col1, m_col2, m_col3 = st.columns(3)
    df_2026 = df[df['Date'].dt.year == today.year]
    
    m_col1.metric("🏊‍♂️ Swim", f"{int(df_2026[df_2026['Sport'] == 'Swim']['Distance'].sum())} yds")
    m_col2.metric("🚴‍♂️ Bike", f"{round(df_2026[df_2026['Sport'] == 'Bike']['Distance'].sum(), 1)} mi")
    m_col3.metric("🏃‍♂️ Run", f"{round(df_2026[df_2026['Sport'] == 'Run']['Distance'].sum(), 1)} mi")

    # --- VOLUME BAR CHART ---
    st.subheader(f"Weekly Volume: {time_frame}")
    
    weekly_sport = df_sorted.groupby([pd.Grouper(key='Date', freq='W-MON'), 'Sport']).sum(numeric_only=True).reset_index()
    weekly_sport['Hours'] = weekly_sport['Duration'] / 60
    
    weekly_totals = weekly_sport.groupby('Date')['Hours'].sum().reset_index()
    weekly_totals['Trend'] = weekly_totals['Hours'].rolling(window=4, min_periods=1).mean()
    
    fig_bar = px.bar(weekly_sport, x='Date', y='Hours', color='Sport',
                 color_discrete_map={"Swim": "#00CC96", "Bike": "#636EFA", "Run": "#EF553B", "Strength": "#AB63FA"})
    
    import plotly.graph_objects as go
    fig_bar.add_trace(go.Scatter(x=weekly_totals['Date'], y=weekly_totals['Trend'],
                                 mode='lines+markers', name='4-Week Avg',
                                 line=dict(color='white', width=3, dash='dot')))

    fig_bar.update_layout(barmode='stack', xaxis_title="Week", yaxis_title="Hours")
    st.plotly_chart(fig_bar, use_container_width=True)
# --- PIE CHART (Discipline Breakdown) ---
    st.divider()
    st.subheader(f"Discipline Breakdown: {time_frame}")
    
    # Use df_filtered so the pie chart reacts to your sidebar selection
    sport_df = df_filtered.groupby('Sport')['Duration'].sum().reset_index()
    
    # Create the chart
    fig_pie = px.pie(
        sport_df, 
        values='Duration', 
        names='Sport', 
        hole=0.4,
        color='Sport',
        color_discrete_map={"Swim": "#00CC96", "Bike": "#636EFA", "Run": "#EF553B", "Strength": "#AB63FA"}
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    # --- RECENT ACTIVITY ---
    st.subheader(f"Activity Log ({time_frame})")
    st.dataframe(df_sorted[['Date', 'Sport', 'Duration', 'Distance', 'Load']].sort_values('Date', ascending=False), use_container_width=True)

    # --- LIFETIME TOTALS ---
    st.divider()
    st.subheader("🏆 Lifetime Totals")
    st.write(f"Since your first triathlon on {df['Date'].min().strftime('%B %d, %Y')}")
    l_col1, l_col2, l_col3, l_col4 = st.columns(4)
    
    l_col1.metric("Total Hours", f"{round(df['Duration'].sum() / 60, 1)}")
    l_col2.metric("Total Swim", f"{int(df[df['Sport'] == 'Swim']['Distance'].sum())} yds")
    l_col3.metric("Total Bike", f"{int(df[df['Sport'] == 'Bike']['Distance'].sum())} mi")
    l_col4.metric("Total Run", f"{int(df[df['Sport'] == 'Run']['Distance'].sum())} mi")

else:
    st.info(f"No data found for the period: {time_frame}")
