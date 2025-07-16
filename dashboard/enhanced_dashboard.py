import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest

# === CONFIGURATION ===
base_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data"
combined_data_path = os.path.join(base_path, "combined_water_data.csv")
forecast_path = os.path.join(base_path, "demand_forecast.csv")
night_leaks_path = os.path.join(base_path, "night_leak_alerts.csv")
spike_alerts_path = os.path.join(base_path, "spike_alerts.csv")
deployment_image_path = os.path.join(base_path, "deployment_diagram.png")

# === ML LEAK DETECTION ===
def run_ml_leak_detection():
    try:
        df = pd.read_csv(combined_data_path)
        df["Date/Time"] = pd.to_datetime(df["Date/Time"])
        df["Hour"] = df["Date/Time"].dt.hour
        df["DayOfWeek"] = df["Date/Time"].dt.dayofweek
        features = df[["Consumption (Liters)", "Hour", "DayOfWeek"]].copy()
        model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
        df["anomaly"] = model.fit_predict(features)

        spike_alerts = df[df["anomaly"] == -1]
        night_alerts = spike_alerts[(spike_alerts["Hour"] >= 0) & (spike_alerts["Hour"] <= 5)]
        spike_alerts = spike_alerts[~spike_alerts.index.isin(night_alerts.index)]

        spike_alerts.to_csv(spike_alerts_path, index=False)
        night_alerts.to_csv(night_leaks_path, index=False)
    except Exception as e:
        st.error(f"ML Leak Detection Failed: {e}")

run_ml_leak_detection()

# === LOAD DATA ===
df = pd.read_csv(combined_data_path, parse_dates=["Date/Time"])
forecast_df = pd.read_csv(forecast_path)
night_df = pd.read_csv(night_leaks_path)
spike_df = pd.read_csv(spike_alerts_path)

# === UI SETUP ===
st.set_page_config(layout="wide")
st.title("🚰 Campus Water Digital Twin Dashboard")

# Sidebar filters
buildings = df["Building"].unique().tolist()
selected_building = st.sidebar.selectbox("🏢 Select Building", buildings)

# Filter by building
df = df[df["Building"] == selected_building]
forecast_df = forecast_df[forecast_df["Building"] == selected_building]
night_df = night_df[night_df["Building"] == selected_building]
spike_df = spike_df[spike_df["Building"] == selected_building]

# === FLOORPLAN OVERLAY ===
st.subheader("🗺️ Deployment Floorplan")
sensor_coords = {
    "A1MD": (349, 421), "A1MF": (397, 421), "A1FD": (446, 421), "A1FF": (495, 421),
    "A2MFD": (802, 190), "A2MFF": (903, 190), "AGMD": (309, 831), "AGMF": (361, 831),
    "AGFD": (414, 831), "AGFF": (463, 831), "B1MD": (675, 421), "B1MF": (726, 421),
    "B1FD": (779, 421), "B1FF": (827, 421), "B2MFD": (1083, 190), "B2MFF": (1184, 190),
    "BGMD": (638, 831), "BGMF": (692, 831), "BGFD": (743, 831), "BGFF": (792, 831),
    "BTTD": (1271, 0), "BTTF": (1372, 0), "ATTD": (987, 0), "ATTF": (1090, 0)
}

img = Image.open(deployment_image_path).convert("RGBA")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
latest = df["Date/Time"].max()
df_hourly = df.copy()
df_hourly["Hour"] = df_hourly["Date/Time"].dt.floor("H")
df_hourly = df_hourly.groupby(["Building", "Hour"])["Consumption (Liters)"].max().diff().fillna(0)

spike_buildings = set(spike_df["Building"].unique())
night_buildings = set(night_df["Building"].unique())
leak_buildings = spike_buildings.union(night_buildings)

for alias, (x, y) in sensor_coords.items():
    val = round(df_hourly.get((alias, latest.floor("H")), 0), 2)
    color = (255, 0, 0, 230) if alias in leak_buildings else (255, 255, 255, 230)
    draw.rectangle([x-5, y-5, x+85, y+15], fill=color)
    draw.text((x, y), f"{alias}: {val}L", fill="black", font=font)

st.image(img, caption=f"Overlayed Meter Readings | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", use_column_width=True)

# === SECTION: Real-Time Chart ===
st.subheader("📈 Real-Time Water Usage")
df_sorted = df.sort_values("Date/Time")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_sorted["Date/Time"], y=df_sorted["Consumption (Liters)"],
                         mode='lines+markers', name='Usage'))
fig.update_layout(height=400, margin=dict(t=10, b=10), xaxis_title="Time", yaxis_title="Liters")
st.plotly_chart(fig, use_container_width=True)

# === SECTION: Individual Sensor Selection ===
st.subheader("🔍 View Specific Sensor Data")
sensor_ids = sorted(df["Building"].unique())
selected_sensor = st.selectbox("Select a sensor to analyze:", sensor_ids)
sensor_data = df[df["Building"] == selected_sensor]

if not sensor_data.empty:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sensor_data["Date/Time"], y=sensor_data["Consumption (Liters)"], mode='lines+markers'))
    fig2.update_layout(title=f"Hourly Usage for {selected_sensor}", xaxis_title="Time", yaxis_title="Liters")
    st.plotly_chart(fig2, use_container_width=True)

# === SECTION: Forecast Table ===
st.subheader("🔮 Demand Forecast")
st.dataframe(forecast_df[["Date", "Forecast (Liters)"]].set_index("Date"))

# === SECTION: Leak Detection Alerts ===
st.subheader("🚨 Leak Detection Alerts")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🌙 Night Leaks")
    st.dataframe(night_df[["Date/Time", "Building", "Consumption (Liters)"]])
with col2:
    st.markdown("### 📈 Spike Alerts")
    st.dataframe(spike_df[["Date/Time", "Building", "Consumption (Liters)"]])

# === SECTION: Simulated Controls ===
st.subheader("🛠️ Simulated Valve Control")
with st.form("valve_control"):
    col1, col2 = st.columns(2)
    with col1:
        valve_building = st.selectbox("Select Building", buildings)
    with col2:
        action = st.radio("Valve Action", ["Open", "Close"])
    submitted = st.form_submit_button("Send Command")
    if submitted:
        st.success(f"✅ Simulated command sent: {action} valve in {valve_building}")
