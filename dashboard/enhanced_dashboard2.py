import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
st.set_page_config(layout="wide")
# === CONFIGURATION ===
base_path = r"/home/iiitb/campus_digital_twin/data"
combined_data_path = os.path.join(base_path, "combined_water_data.csv")
forecast_path = os.path.join(base_path, "demand_forecast.csv")
night_leaks_path = os.path.join(base_path, "night_leak_alerts.csv")
spike_alerts_path = os.path.join(base_path, "spike_alerts.csv")
deployment_image_path = os.path.join(base_path, "deployment_diagram.png")
st.write("✅ Script started")
try:
    df = pd.read_csv(combined_data_path)
    st.write("✅ Loaded water data:", df.shape)
except Exception as e:
    st.error(f"❌ Failed to load water data: {e}")

# === LOGIN ===
def authenticate():
    st.sidebar.title("🔐 Admin Login")
    password = st.sidebar.text_input("Enter password", type="password")
    if password == "water@123":
        return True
    elif password:
        st.sidebar.error("❌ Invalid password")
    return False

if not authenticate():
    st.stop()

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

st.title("🚰 Campus Water Digital Twin Dashboard")

# === FLOORPLAN OVERLAY ===
st.subheader("🗺️ Deployment Floorplan")
sensor_coords = {
    "A1MD": (349, 421), "A1MF": (397, 421), "A1FD": (446, 421), "A1FF": (495, 421),
    "A2MFD": (802, 190), "A2MFF": (903, 190),
    "AGMD": (309, 831), "AGMF": (361, 831), "AGFD": (414, 831), "AGFF": (463, 831),
    "B1MD": (675, 421), "B1MF": (726, 421), "B1FD": (779, 421), "B1FF": (827, 421),
    "B2MFD": (1083, 190), "B2MFF": (1184, 190),
    "BGMD": (638, 831), "BGMF": (692, 831), "BGFD": (743, 831), "BGFF": (792, 831),
    "BTTD": (1271, 0), "BTTF": (1372, 0),
    "ATTD": (987, 0), "ATTF": (1090, 0)
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
    if alias in leak_buildings:
        color = (255, 0, 0, 230)  # Red
    elif val > 300:
        color = (255, 0, 0, 230)
    elif val > 150:
        color = (255, 165, 0, 230)  # Orange
    else:
        color = (0, 102, 204, 230)  # Blue
    draw.rectangle([x - 5, y - 5, x + 85, y + 15], fill=color)
    draw.text((x, y), f"{alias}: {val}L", fill="white", font=font)

st.image(img, caption=f"Overlayed Meter Readings | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", use_column_width=True)

# === Sensor Dropdown for Details ===
st.subheader("🔎 Inspect a Sensor")
sensor_ids = sorted(df["Building"].unique())
selected_sensor = st.selectbox("Select a sensor to analyze:", sensor_ids)
sensor_data = df[df["Building"] == selected_sensor]

if not sensor_data.empty:
    st.markdown(f"### 📊 Historical Usage for {selected_sensor}")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sensor_data["Date/Time"], y=sensor_data["Consumption (Liters)"], mode='lines+markers'))
    fig2.update_layout(xaxis_title="Time", yaxis_title="Liters", height=400)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🔮 Forecast for Sensor Building")
    forecast_data = forecast_df[forecast_df["Building"] == selected_sensor]
    st.dataframe(forecast_data[["Date", "Forecast (Liters)"]])

    st.markdown("### 🚨 Recent Alerts for This Sensor")
    st.dataframe(spike_df[spike_df["Building"] == selected_sensor][["Date/Time", "Consumption (Liters)"]])
    st.dataframe(night_df[night_df["Building"] == selected_sensor][["Date/Time", "Consumption (Liters)"]])

# === Forecast Table ===
st.subheader("🔮 Overall Demand Forecast")
st.dataframe(forecast_df[["Building", "Date", "Forecast (Liters)"]])

# === Leak Alerts ===
st.subheader("🚨 Full Leak Alerts")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🌙 Night Leaks")
    st.dataframe(night_df[["Date/Time", "Building", "Consumption (Liters)"]])
with col2:
    st.markdown("### 📈 Spike Alerts")
    st.dataframe(spike_df[["Date/Time", "Building", "Consumption (Liters)"]])

# === Simulated Valve Control ===
st.subheader("🛠️ Valve Control Simulation")
with st.form("valve_control"):
    col1, col2 = st.columns(2)
    with col1:
        valve_building = st.selectbox("Control Valve for Building", df["Building"].unique())
    with col2:
        action = st.radio("Select Action", ["Open", "Close"])
    submitted = st.form_submit_button("Send Command")
    if submitted:
        st.success(f"✅ Simulated command sent: {action} valve for {valve_building}")

# === Sidebar Info ===
st.sidebar.markdown("---")
st.sidebar.markdown("ℹ️ **Legend**")
st.sidebar.markdown("- 🔴 Leak / High Use")
st.sidebar.markdown("- 🟠 Medium Use")
st.sidebar.markdown("- 🔵 Normal")
st.sidebar.markdown("🛠️ Redrawn every time you refresh.")
if st.sidebar.button("🔄 Re-run ML Leak Detection"):
    run_ml_leak_detection()
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.write("© 2025 IIIT Bengaluru — Water Management system")
