import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime, timedelta
from streamlit_plotly_events import plotly_events

# --- CONFIG ---
image_path = "deployment_diagram.png"
data_path = "combined_water_data.csv"

# --- Load deployment image ---
bg_image = Image.open(image_path)
width, height = bg_image.size

# --- Sensor Coordinates ---
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

# --- Load data ---
df = pd.read_csv(data_path)
df["Date/Time"] = pd.to_datetime(df["Date/Time"])
df["Hour"] = df["Date/Time"].dt.floor("H")
df["Alias"] = df["Building"].str.extract(
    r'(A1MD|A1MF|A1FD|A1FF|A2MFD|A2MFF|AGMD|AGMF|AGFD|AGFF|B1MD|B1MF|B1FD|B1FF|B2MFD|B2MFF|BGMD|BGMF|BGFD|BGFF|BTTD|BTTF|ATTD|ATTF)'
)
df = df.dropna(subset=["Alias"])

# --- Hourly consumption ---
hourly_df = df.groupby(["Alias", "Hour"])["Consumption (Liters)"].max().diff().fillna(0)
latest_hour = df["Hour"].max()
sensor_values = {alias: round(hourly_df.get((alias, latest_hour), 0), 2) for alias in sensor_coords}

# --- Scatter Overlay on Image ---
x_vals = [x for x, y in sensor_coords.values()]
y_vals = [height - y for x, y in sensor_coords.values()]
labels = [f"{alias}: {sensor_values[alias]} L" for alias in sensor_coords]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x_vals,
    y=y_vals,
    text=labels,
    customdata=list(sensor_coords.keys()),  # 👈 THIS is critical
    mode="markers+text",
    textposition="bottom center",
    marker=dict(size=16, color="royalblue", line=dict(width=2, color="black"))
))


fig.update_layout(
    images=[dict(
        source=bg_image,
        xref="x", yref="y",
        x=0, y=height,
        sizex=width, sizey=height,
        sizing="stretch",
        layer="below"
    )],
    xaxis=dict(visible=False), yaxis=dict(visible=False),
    margin=dict(l=0, r=0, t=40, b=0),
    width=width, height=height,
    title="📍 Click on a water meter for details"
)

# --- Streamlit Display ---
st.set_page_config(layout="wide")
st.title("💧 Interactive Campus Water Dashboard")
click = plotly_events(fig, click_event=True, hover_event=True)
st.write("Click result:", click)

# --- If a sensor is clicked ---
if click and click[0].get("customdata"):
    clicked = click[0]["customdata"]
    st.subheader(f"📊 Water Usage at {clicked}")

    # Plot hourly usage
    sensor_data = df[df["Alias"] == clicked]
    hourly_series = (
        sensor_data.groupby("Hour")["Consumption (Liters)"].max().diff().fillna(0)
    )
    st.line_chart(hourly_series.rename("Hourly Consumption (L)"))

    # Valve toggle
    if f"{clicked}_valve" not in st.session_state:
        st.session_state[f"{clicked}_valve"] = "Open"

    valve_state = st.radio(f"Valve at {clicked}", ["Open", "Closed"],
                           index=0 if st.session_state[f"{clicked}_valve"] == "Open" else 1)
    st.session_state[f"{clicked}_valve"] = valve_state
    st.success(f"Valve is: **{valve_state}**")

else:
    st.write("ℹ️ No sensor selected or no customdata found. Try clicking a blue dot again.")

