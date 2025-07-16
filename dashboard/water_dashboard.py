import streamlit as st
import pandas as pd
import os

# File paths
base_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data"
combined_data_path = os.path.join(base_path, "combined_water_data.csv")
forecast_path = os.path.join(base_path, "demand_forecast.csv")
night_leaks_path = os.path.join(base_path, "night_leak_alerts.csv")
spike_alerts_path = os.path.join(base_path, "spike_alerts.csv")

# Load data
df = pd.read_csv(combined_data_path, parse_dates=["Date/Time"])
forecast_df = pd.read_csv(forecast_path)
night_df = pd.read_csv(night_leaks_path)
spike_df = pd.read_csv(spike_alerts_path)

# Title
st.title("🏫 Campus Water Digital Twin Dashboard")

# Sidebar filters
buildings = df["Building"].unique().tolist()
selected_building = st.sidebar.selectbox("Select Building", buildings)

# Filter by building
df = df[df["Building"] == selected_building]
forecast_df = forecast_df[forecast_df["Building"] == selected_building]
night_df = night_df[night_df["Building"] == selected_building]
spike_df = spike_df[spike_df["Building"] == selected_building]

# Section 1: Total usage
st.header(f"📊 Total Water Usage - {selected_building}")
daily_usage = df.groupby(df["Date/Time"].dt.date)["Consumption (Liters)"].sum()
st.line_chart(daily_usage)

# Section 2: Demand Forecast
st.header("📈 Demand Forecast (Next 3 Days)")
st.table(forecast_df[["Date", "Forecast (Liters)"]].set_index("Date"))

# Section 3: Leak Alerts
st.header("⚠️ Leak Detection Alerts")
if not night_df.empty or not spike_df.empty:
    st.warning("⚠️ Leak alerts detected! Check below.")
else:
    st.success("✅ No leak alerts at this time.")

st.subheader("🌙 Night Leak Alerts")
if not night_df.empty:
    st.dataframe(night_df[["Date/Time", "Consumption (Liters)"]])
else:
    st.success("✅ No night leaks detected.")

st.subheader("📈 Spike Alerts")
if not spike_df.empty:
    st.dataframe(spike_df[["Date/Time", "Consumption (Liters)", "RollingAvg"]])
else:
    st.success("✅ No abnormal spikes detected.")
# Section 4: Simulated Control
st.header("🛠️ Simulated Controls")

with st.form("valve_form"):
    st.subheader("🚰 Control Water Valve (Simulation)")
    valve_building = st.selectbox("Select Building to Control Valve", buildings)
    action = st.radio("Select Action", ["Close Valve", "Open Valve"])
    submitted = st.form_submit_button("Send Command")

    if submitted:
        # Simulate sending command (in real life, this would call an API or script)
        st.success(f"✅ Command sent: {action} for {valve_building}")