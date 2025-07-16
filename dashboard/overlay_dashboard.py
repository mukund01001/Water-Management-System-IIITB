import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# --- CONFIG ---
image_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\dashboard\deployment_diagram.png"
data_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv"

# Updated coordinates (measured on deployment_diagram.png)
sensor_coords = {
    "A1MD": (349, 416), "A1MF": (397, 416), "A1FD": (446, 416), "A1FF": (495, 416),
    "A2MFD": (802, 186), "A2MFF": (903, 186),
    "AGMD": (309, 826), "AGMF": (361, 826), "AGFD": (414, 826), "AGFF": (463, 826),
    "B1MD": (675, 416), "B1MF": (726, 416), "B1FD": (779, 416), "B1FF": (827, 416),
    "B2MFD": (1083, 186), "B2MFF": (1184, 186),
    "BGMD": (638, 826), "BGMF": (692, 826), "BGFD": (743, 826), "BGFF": (792, 826),
    "BTTD": (1271, 0), "BTTF": (1372, 0),
    "ATTD": (987, 0), "ATTF": (1090, 0)
}

# --- LOAD & CLEAN DATA ---
df = pd.read_csv(data_path)
df["Date/Time"] = pd.to_datetime(df["Date/Time"])

# Extract standard alias name
df["Alias"] = df["Building"].str.extract(
    r'(A1MD|A1MF|A1FD|A1FF|A2MFD|A2MFF|AGMD|AGMF|AGFD|AGFF|B1MD|B1MF|B1FD|B1FF|B2MFD|B2MFF|BGMD|BGMF|BGFD|BGFF|BTTD|BTTF|ATTD|ATTF)'
)

# Clean and compute hourly consumption
df = df.dropna(subset=["Alias"])
df["Hour"] = df["Date/Time"].dt.floor("H")
hourly = (
    df.sort_values("Date/Time")
    .groupby(["Alias", "Hour"])["Consumption (Liters)"]
    .max()
    .diff()
    .fillna(0)
)

latest_hour = df["Hour"].max()

# --- DRAW ON IMAGE ---
img = Image.open(image_path).convert("RGBA")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()

for alias, (x, y) in sensor_coords.items():
    value = round(hourly.get((alias, latest_hour), 1), 2)
    draw.rectangle([x - 5, y - 5, x + 85, y + 15], fill=(255, 255, 255, 230))
    draw.text((x, y), f"{alias}: {value}L", fill="black", font=font)

# --- STREAMLIT DASHBOARD ---
st.set_page_config(layout="wide")
st.title("💧 Digital Twin Dashboard – Hourly Consumption Overlay")
st.image(img, caption="Hourly readings (L) over floor plan", use_column_width=True)
# --- SIDEBAR SENSOR SELECTION ---
st.sidebar.header("📊 View Sensor Graph")
selected_alias = st.sidebar.selectbox("Select a sensor", list(sensor_coords.keys()))

# Filter data for selected sensor
sensor_data = df[df["Alias"] == selected_alias].copy()
sensor_data["Hour"] = sensor_data["Date/Time"].dt.floor("H")
hourly_series = (
    sensor_data.groupby("Hour")["Consumption (Liters)"]
    .max()
    .diff()
    .fillna(0)
    .rename("Hourly Consumption (L)")
)

# --- DISPLAY LINE CHART ---
st.sidebar.markdown(f"**Hourly water use – {selected_alias}**")
st.sidebar.line_chart(hourly_series)
