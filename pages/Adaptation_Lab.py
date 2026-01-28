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

st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Adaptation Lab")

# --- DATA ENTRY ---
with st.sidebar:
    st.header("Log Session")
    date = st.date_input("Workout Date", datetime.now())
    discipline = st.selectbox("Discipline", ["Swim", "Bike", "Run"])
    w_type = st.selectbox("Session Type", ["Steady State (Z2)", "Tempo/Sweet Spot", "Intervals"])
    
    avg_hr = st.number_input("Avg Heart Rate", value=140)
    
    if discipline == "Bike":
        val = st.number_input("Avg Power (Watts)", value=200)
        ef = val / avg_hr
    else:
        p_min = st.number_input("Pace Min", value=5)
        p_sec = st.number_input("Pace Sec", value=0)
        total_sec = (p_min * 60) + p_sec
        speed = 1000 / total_sec if total_sec > 0 else 0
        ef = speed / avg_hr

    drift = st.number_input("Decoupling % (if known)", value=0.0)

    if st.button("Save to Google Sheets"):
        # Create new row
        new_data = pd.DataFrame([{
            "Date": str(date),
            "Discipline": discipline,
            "Type": w_type,
            "EF": round(ef, 4),
            "Decoupling": drift
        }])
        
        # Add to existing data and update sheet
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(spreadsheet=url, data=updated_df)
        st.success("Synced to Google Sheets!")
        st.rerun()

# --- DASHBOARD ---
if not df.empty:
    tab1, tab2 = st.tabs(["Efficiency Trends", "Decoupling Calculator"])
    
    with tab1:
        # Only chart Steady State for the 'vibe' check
        steady_df = df[df['Type'] == "Steady State (Z2)"]
        if not steady_df.empty:
            st.line_chart(steady_df, x="Date", y="EF", color="Discipline")
        else:
            st.info("No Steady State logs found yet.")
            
    with tab2:
        # Quick Decoupling Tool (Mental Math helper)
        st.subheader("Drift Calculator")
        h1 = st.number_input("1st Half EF", value=1.40)
        h2 = st.number_input("2nd Half EF", value=1.35)
        calc = ((h1 - h2) / h1) * 100
        st.metric("Calculated Drift", f"{calc:.1f}%")
        if calc < 5: st.success("Green Light: Aerobically Stable")
