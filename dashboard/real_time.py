import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# --- CONFIG ---
image_path = "deployment_diagram.png"
data_path = "combined_water_data.csv"
refresh_interval = 300  # 5 minutes in seconds

# Sensor coordinates
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

st.set_page_config(layout="wide")
st.title("💧Campus Water Dashboard")

# --- LOAD DATA ---
df = pd.read_csv(data_path)
df["Date/Time"] = pd.to_datetime(df["Date/Time"])
df["Alias"] = df["Building"].str.extract(
    r'(A1MD|A1MF|A1FD|A1FF|A2MFD|A2MFF|AGMD|AGMF|AGFD|AGFF|B1MD|B1MF|B1FD|B1FF|B2MFD|B2MFF|BGMD|BGMF|BGFD|BGFF|BTTD|BTTF|ATTD|ATTF)'
)
df = df.dropna(subset=["Alias"])
df["Hour"] = df["Date/Time"].dt.floor("H")

# --- HOURLY USAGE ---
hourly_df = df.groupby(["Alias", "Hour"])["Consumption (Liters)"].max().diff().fillna(0)
latest_hour = df["Hour"].max()

# --- LEAK DETECTION ---
alerts = []
for alias in sensor_coords:
    if (alias, latest_hour) not in hourly_df:
        continue
    current = hourly_df.get((alias, latest_hour), 0)
    last_3 = [hourly_df.get((alias, latest_hour - timedelta(hours=i)), 0) for i in range(1, 4)]
    avg_last_3 = sum(last_3) / 3 if last_3 else 0
    if avg_last_3 > 0 and current > 3 * avg_last_3:
        alerts.append(f"🚨 Leak at {alias}: {round(current, 1)}L (>{round(3*avg_last_3, 1)}L)")

# --- DRAW OVERLAY ---
img = Image.open(image_path).convert("RGBA")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()

for alias, (x, y) in sensor_coords.items():
    value = round(hourly_df.get((alias, latest_hour), 0), 2)
    draw.rectangle([x - 5, y - 5, x + 85, y + 15], fill=(255, 255, 255, 230))
    draw.text((x, y), f"{alias}: {value}L", fill="black", font=font)

st.image(img, caption=f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", use_column_width=True)

# --- ALERTS ---
if alerts:
    st.warning("⚠️ Leak Alerts:")
    for alert in alerts:
        st.write(alert)
else:
    st.success("✅ No leaks detected in the latest hour.")

# --- CONTROLS ---
st.sidebar.header("Valve Control Simulation")
for alias in sorted(sensor_coords):
    if f"{alias}_valve" not in st.session_state:
        st.session_state[f"{alias}_valve"] = "Open"
    status = st.radio(f"{alias} valve", ["Open", "Closed"], index=0 if st.session_state[f"{alias}_valve"] == "Open" else 1, key=alias)
    st.session_state[f"{alias}_valve"] = status

# --- SENSOR CHART ---
st.sidebar.header("📊 Sensor Usage History")
selected_sensor = st.sidebar.selectbox("Select sensor", sorted(sensor_coords.keys()))
sensor_data = df[df["Alias"] == selected_sensor]
hourly_series = (
    sensor_data.groupby("Hour")["Consumption (Liters)"].max().diff().fillna(0)
    .rename("Hourly Consumption (L)")
)
st.sidebar.line_chart(hourly_series)
