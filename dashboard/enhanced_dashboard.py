import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import numpy as np

# --- Streamlit Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="Campus Water Digital Twin Dashboard 💧",
    page_icon="💧"
)

# --- Custom CSS for UI Polish ---
st.markdown("""
<style>
    /* General Font and Text Styling */
    html, body, [class*="stText"] {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #333333;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #004d99; /* Darker blue for headings */
        font-weight: 600;
    }
    .stApp {
        background-color: #f0f2f6; /* Light gray background */
    }
    .stMarkdown p {
        font-size: 1rem;
        line-height: 1.6;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px; /* Spacing between tabs */
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        background-color: #e0e0e0; /* Light gray tab background */
        border-radius: 4px 4px 0 0;
        border-bottom: 3px solid transparent; /* default */
        font-size: 16px;
        font-weight: bold;
        color: #606060; /* Darker text for inactive tabs */
        margin-bottom: -3px; /* Pulls tabs slightly over the border */
    }
    .stTabs [data-baseweb="tab"] svg {
        display: none; /* Hide default Streamlit tab icons */
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #d0d0d0; /* Darker on hover */
        color: #333333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff; /* Primary blue for active tab */
        color: white; /* White text for active tab */
        border-bottom: 3px solid #007bff; /* Active border */
    }
    .stTabs [aria-selected="true"]:hover {
        background-color: #0056b3; /* Darker blue on hover for active tab */
        color: white;
    }

    /* Metric Cards Styling */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2em !important;
        color: #007bff !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9em !important;
        color: #606060 !important;
    }

    /* Info/Warning/Error boxes */
    div.stAlert {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Sidebar improvements */
    [data-testid="stSidebar"] {
        background-color: #f8f8f8; /* Lighter sidebar */
    }
    .css-1lcbmhc, .css-1y4pmv8 { /* Specific Streamlit classes for sidebar elements */
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# --- CONFIGURATION: Define Base Paths and File Locations ---
script_dir = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(script_dir, '..'))

# Verify if the derived PROJECT_ROOT seems correct
if not (os.path.isdir(os.path.join(PROJECT_ROOT, 'data')) and \
        os.path.isdir(os.path.join(PROJECT_ROOT, 'dashboard'))):
    PROJECT_ROOT = "/home/iiitb/campus_digital_twin"
    if not (os.path.isdir(os.path.join(PROJECT_ROOT, 'data')) and \
            os.path.isdir(os.path.join(PROJECT_ROOT, 'dashboard'))):
        st.error("❌ Critical Error: Could not determine project root. "
                 "Please ensure the script is run from inside 'campus_digital_twin' "
                 "or manually set 'PROJECT_ROOT' variable in the code.")
        st.stop()


DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
PLOTS_FOLDER = os.path.join(PROJECT_ROOT, "plots") # For saved forecast plots, though we plot dynamically

COMBINED_DATA_PATH = os.path.join(DATA_FOLDER, "combined_water_data.csv")
FORECAST_PATH = os.path.join(DATA_FOLDER, "demand_forecast.csv")
NIGHT_LEAKS_PATH = os.path.join(DATA_FOLDER, "night_leak_alerts.csv")
SPIKE_ALERTS_PATH = os.path.join(DATA_FOLDER, "spike_alerts.csv")
DEPLOYMENT_IMAGE_PATH = os.path.join(DATA_FOLDER, "deployment_diagram.png")

# --- Consistent with leak_detection.py ---
# This threshold defines what is considered "active flow" for visual purposes on the map.
# Any consumption below this will be shown as "normal/low consumption" (blue).
# It should align with NO_FLOW_THRESHOLD in leak_detection.py if you want consistency.
SIGNIFICANT_CONSUMPTION_THRESHOLD = 0.05 # L/hr - Adjust based on your data and what's *truly* non-zero


# --- UTILITY FUNCTIONS ---

@st.cache_data(ttl=300) # Cache data for 5 minutes
def load_and_process_water_data_cached():
    """
    Loads combined water data, cleans it, calculates hourly consumption,
    and returns processed DataFrame.
    """
    try:
        df = pd.read_csv(COMBINED_DATA_PATH, parse_dates=["Date/Time"])
        df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
        df.dropna(subset=['Date/Time'], inplace=True)
        df = df.sort_values(by=['Building', 'Date/Time']).reset_index(drop=True)

        df['Consumption (Liters)'] = df['Consumption (Liters)'].apply(lambda x: max(0, x))

        df['Hourly Consumption (Liters)'] = df.groupby('Building')['Consumption (Liters)'].diff().fillna(0)
        df['Hourly Consumption (Liters)'] = df['Hourly Consumption (Liters)'].apply(lambda x: max(0, x))

        return df

    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_csv_data_cached(path, parse_dates=None):
    """Loads a CSV file with caching. No Streamlit elements inside."""
    try:
        df = pd.read_csv(path, parse_dates=parse_dates)
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- AUTHENTICATION ---
def authenticate():
    """Handles admin login with a simple password check."""
    st.sidebar.title("🔐 Admin Login")
    password = st.sidebar.text_input("Enter password", type="password", key="admin_password_input")
    if password == "water@123":
        return True
    elif password:
        st.sidebar.error("❌ Invalid password")
    return False

# --- MAIN DASHBOARD LOGIC ---
if not authenticate():
    st.stop()

st.title("Campus Water Digital Twin Dashboard 🏙️💧")

# --- Load all data at once ---
df_combined = load_and_process_water_data_cached()
night_df = load_csv_data_cached(NIGHT_LEAKS_PATH, parse_dates=["Date/Time"])
spike_df = load_csv_data_cached(SPIKE_ALERTS_PATH, parse_dates=["Date/Time"])
forecast_df = load_csv_data_cached(FORECAST_PATH)


# --- Initial Data Load & Error Checks ---
if df_combined.empty:
    st.error("Dashboard cannot load water consumption data. Please ensure 'combined_water_data.csv' exists and is correctly formatted.")
    st.info("💡 Tip: Run `python /home/iiitb/campus_digital_twin/scripts/packet_to_combined_water_data.py` if your raw packet data is new.")
    st.stop()
else:
    st.toast(f"✅ Water data loaded from {df_combined['Date/Time'].min().strftime('%Y-%m-%d %H:%M')} to {df_combined['Date/Time'].max().strftime('%Y-%m-%d %H:%M')}")

# --- Global Data Info ---
last_updated_data = df_combined["Date/Time"].max().strftime('%Y-%m-%d %H:%M:%S') if not df_combined.empty else "N/A"
st.info(f"Data last updated: {last_updated_data}")

# --- Sidebar Actions ---
if st.sidebar.button("🔄 Reload All Data (Clear Cache)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# --- Data File Status Warnings ---
if night_df.empty:
    st.sidebar.warning("Night leak alerts file is empty or not found. Please run `leak_detection.py`.")
if spike_df.empty:
    st.sidebar.warning("Spike alerts file is empty or not found. Please run `leak_detection.py`.")
if forecast_df.empty:
    st.sidebar.warning("Demand forecast file is empty or not found. Please run `forecast_demand.py`.")


# --- Dashboard Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Sensor Details", "Campus Forecast", "All Alerts", "Valve Control"])

# --- TAB: Overview ---
with tab1:
    st.header("Campus Water Usage Overview")

    # --- KPIs ---
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    total_liters_24h = df_combined[df_combined["Date/Time"] >= (datetime.now() - timedelta(hours=24))]["Hourly Consumption (Liters)"].sum()
    total_liters_7d = df_combined[df_combined["Date/Time"] >= (datetime.now() - timedelta(days=7))]["Hourly Consumption (Liters)"].sum()
    num_night_leaks = len(night_df)
    num_spike_alerts = len(spike_df)

    col_kpi1.metric("Last 24h Consumption", f"{total_liters_24h:,.1f} L", help="Total water consumed across campus in the last 24 hours.")
    col_kpi2.metric("Last 7 Days Consumption", f"{total_liters_7d:,.1f} L", help="Total water consumed across campus in the last 7 days.")
    col_kpi3.metric("Total Night Leaks", f"{num_night_leaks}", help="Total number of night leak alerts detected.")
    col_kpi4.metric("Total Spike Alerts", f"{num_spike_alerts}", help="Total number of spike alerts detected.")

    st.markdown("---")

    # --- Floorplan Overlay ---
    st.subheader("🗺️ Live Building Status")

    SENSOR_COORDS = {
        "A1MD": (349, 421), "A1MF": (397, 421), "A1FD": (446, 421), "A1FF": (495, 421),
        "A2MFD": (802, 190), "A2MFF": (903, 190),
        "AGMD": (309, 831), "AGMF": (361, 831), "AGFD": (414, 831), "AGFF": (463, 831),
        "B1MD": (675, 421), "B1MF": (726, 421), "B1FD": (779, 421), "B1FF": (827, 421),
        "B2MFD": (1083, 190), "B2MFF": (1184, 190),
        "BGMD": (638, 831), "BGMF": (692, 831), "BGFD": (743, 831), "BGFF": (792, 831),
        "BTTD": (1271, 0), "BTTF": (1372, 0),
        "ATTD": (987, 0), "ATTF": (1090, 0)
    }

    try:
        img = Image.open(DEPLOYMENT_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 10) # Even smaller font for cleanliness
        except IOError:
            font = ImageFont.load_default()
    except FileNotFoundError:
        st.error(f"❌ Deployment diagram image not found at {DEPLOYMENT_IMAGE_PATH}. "
                 "Please ensure 'deployment_diagram.png' is in the 'data' folder.")
        img = Image.new("RGBA", (1500, 900), (240, 242, 246, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((50, 50), "Deployment Diagram Not Found. Placeholder Image.", fill=(0,0,0,255), font=font)


    latest_hourly_consumption = {}
    if not df_combined.empty:
        latest_hourly_consumption = df_combined.groupby('Building')['Hourly Consumption (Liters)'].last().to_dict()

    alert_buildings = set()
    if not night_df.empty:
        alert_buildings.update(night_df["Building"].unique())
    if not spike_df.empty:
        alert_buildings.update(spike_df["Building"].unique())

    for alias, (x, y) in SENSOR_COORDS.items():
        current_hourly_val = latest_hourly_consumption.get(alias, 0)

        # Coloring logic: Red for ML-detected leak, Orange for significant flow, Blue for normal/low flow
        if alias in alert_buildings:
            color = (255, 0, 0, 230)  # Red: Leak / Active Alert (detected by ML in leak_detection.py) 🔴
        elif current_hourly_val > SIGNIFICANT_CONSUMPTION_THRESHOLD:
            color = (255, 140, 0, 230) # Dark Orange: High Hourly Consumption (active flow, but not an ML-detected leak) 🟠
        else:
            color = (0, 102, 204, 230) # Blue: Normal/Low Consumption (little to no active flow) 🔵

        # Smaller box and font for cleanliness
        rect_width = 65 # Adjusted width (even smaller)
        rect_height = 18 # Adjusted height (even smaller)
        text_offset_y = 2 # Adjusted text vertical position
        
        # Display only the hourly reading, not the building name
        draw.rectangle([x - 5, y - 5, x - 5 + rect_width, y - 5 + rect_height], fill=color)
        draw.text((x, y + text_offset_y), f"{current_hourly_val:.1f}L/hr", fill="white", font=font)

    st.image(img, caption=f"Live Hourly Meter Readings | As of: {last_updated_data}", use_container_width=True)

    st.markdown("---")

    # --- Overall Campus Consumption Trend ---
    st.subheader("📈 Campus-Wide Daily Consumption Trend")
    if not df_combined.empty:
        df_daily_total = df_combined.set_index("Date/Time").resample("D")["Hourly Consumption (Liters)"].sum().reset_index()
        df_daily_total.rename(columns={"Date/Time": "Date", "Hourly Consumption (Liters)": "Total Daily Consumption (Liters)"}, inplace=True)

        fig_overall_trend = go.Figure()
        fig_overall_trend.add_trace(go.Scatter(
            x=df_daily_total["Date"],
            y=df_daily_total["Total Daily Consumption (Liters)"],
            mode='lines+markers',
            name='Daily Total',
            line=dict(color='steelblue', width=2),
            marker=dict(size=6, color='steelblue')
        ))
        fig_overall_trend.update_layout(
            title="Total Daily Water Consumption Across Campus",
            xaxis_title="Date",
            yaxis_title="Total Consumption (Liters)",
            hovermode="x unified",
            height=400,
            template="plotly_white"
        )
        st.plotly_chart(fig_overall_trend, use_container_width=True)
    else:
        st.info("No data available to show campus-wide consumption trend.")


# --- TAB: Sensor Details ---
with tab2:
    st.header("Individual Sensor Insights")
    sensor_ids = sorted(df_combined["Building"].unique())
    selected_sensor = st.selectbox("Select a sensor to analyze:", sensor_ids, key="selected_sensor_detail_tab")

    if selected_sensor:
        sensor_data = df_combined[df_combined["Building"] == selected_sensor].sort_values("Date/Time")

        if not sensor_data.empty:
            st.markdown(f"### 📊 Historical Hourly Usage for {selected_sensor}")

            min_date = sensor_data["Date/Time"].min().date()
            max_date = sensor_data["Date/Time"].max().date()
            date_range = st.slider(
                "Select Date Range for Historical Data:",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD",
                key="date_range_slider_tab"
            )
            filtered_sensor_data = sensor_data[(sensor_data["Date/Time"].dt.date >= date_range[0]) &
                                                (sensor_data["Date/Time"].dt.date <= date_range[1])]

            if not filtered_sensor_data.empty:
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(
                    x=filtered_sensor_data["Date/Time"],
                    y=filtered_sensor_data["Hourly Consumption (Liters)"],
                    mode='lines',
                    name='Hourly Consumption',
                    line=dict(color='deepskyblue', width=2)
                ))
                sensor_spike_alerts_hist = spike_df[(spike_df["Building"] == selected_sensor) &
                                                    (spike_df["Date/Time"].dt.date >= date_range[0]) &
                                                    (spike_df["Date/Time"].dt.date <= date_range[1])]
                sensor_night_leaks_hist = night_df[(night_df["Building"] == selected_sensor) &
                                                   (night_df["Date/Time"].dt.date >= date_range[0]) &
                                                   (night_df["Date/Time"].dt.date <= date_range[1])]

                if not sensor_spike_alerts_hist.empty:
                    fig_hist.add_trace(go.Scatter(
                        x=sensor_spike_alerts_hist["Date/Time"],
                        y=sensor_spike_alerts_hist["Hourly Consumption (Liters)"],
                        mode='markers',
                        name='Spike Alert',
                        marker=dict(color='orange', size=10, symbol='star'),
                        hoverinfo='text',
                        text=[f"Spike: {row['Hourly Consumption (Liters)']:.1f}L" for _, row in sensor_spike_alerts_hist.iterrows()]
                    ))
                if not sensor_night_leaks_hist.empty:
                    fig_hist.add_trace(go.Scatter(
                        x=sensor_night_leaks_hist["Date/Time"],
                        y=sensor_night_leaks_hist["Hourly Consumption (Liters)"],
                        mode='markers',
                        name='Night Leak',
                        marker=dict(color='red', size=10, symbol='x'),
                        hoverinfo='text',
                        text=[f"Night Leak: {row['Hourly Consumption (Liters)']:.1f}L" for _, row in sensor_night_leaks_hist.iterrows()]
                    ))

                fig_hist.update_layout(
                    title=f"Hourly Water Consumption for {selected_sensor}",
                    xaxis_title="Time",
                    yaxis_title="Hourly Consumption (Liters)",
                    hovermode="x unified",
                    height=450,
                    template="plotly_white",
                    legend_title_text='Data Series'
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info(f"No historical data available for {selected_sensor} within the selected date range.")
        else:
            st.info(f"No historical data available for {selected_sensor}.")

        st.markdown("### 🔮 Forecast for Sensor Building")
        if not forecast_df.empty:
            forecast_data = forecast_df[forecast_df["Building"] == selected_sensor].sort_values("Date")
            if not forecast_data.empty:
                fig_forecast = go.Figure()
                fig_forecast.add_trace(go.Bar(
                    x=forecast_data["Date"],
                    y=forecast_data["Forecast (Liters)"],
                    name='Forecasted Daily Demand',
                    marker_color='lightseagreen'
                ))
                fig_forecast.update_layout(
                    title=f"Daily Demand Forecast for {selected_sensor}",
                    xaxis_title="Date",
                    yaxis_title="Forecast (Liters)",
                    height=350,
                    template="plotly_white"
                )
                st.plotly_chart(fig_forecast, use_container_width=True)
                st.dataframe(forecast_data[["Date", "Forecast (Liters)"]], use_container_width=True)
            else:
                st.info(f"No forecast data available for {selected_sensor}.")
        else:
            st.warning("Forecast data not loaded. Check 'demand_forecast.csv'.")

        st.markdown("### 🚨 Recent Alerts for This Sensor")
        col_alert_sensor1, col_alert_sensor2 = st.columns(2)
        with col_alert_sensor1:
            st.markdown("#### Spike Alerts (Last 7 Days)")
            sensor_spike_alerts = spike_df[(spike_df["Building"] == selected_sensor) &
                                           (spike_df["Date/Time"] >= (datetime.now() - timedelta(days=7)))]
            if not sensor_spike_alerts.empty:
                st.dataframe(sensor_spike_alerts[["Date/Time", "Hourly Consumption (Liters)"]].sort_values("Date/Time", ascending=False), use_container_width=True)
            else:
                st.info("No recent spike alerts for this sensor.")
        with col_alert_sensor2:
            st.markdown("#### Night Leaks (Last 7 Days)")
            sensor_night_leaks = night_df[(night_df["Building"] == selected_sensor) &
                                          (night_df["Date/Time"] >= (datetime.now() - timedelta(days=7)))]
            if not sensor_night_leaks.empty:
                st.dataframe(sensor_night_leaks[["Date/Time", "Hourly Consumption (Liters)"]].sort_values("Date/Time", ascending=False), use_container_width=True)
            else:
                st.info("No recent night leaks for this sensor.")

    else:
        st.info("Select a sensor to view its detailed information.")


# --- TAB: Campus Forecast ---
with tab3:
    st.header("Campus-Wide Demand Forecast")
    if not forecast_df.empty:
        # Aggregate forecast if needed, or just display raw
        st.dataframe(forecast_df[["Building", "Date", "Forecast (Liters)"]].sort_values(["Date", "Building"]), use_container_width=True)

        # Plot overall forecast trend (e.g., sum per day)
        # Ensure 'Date' column is datetime
        forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])
        daily_campus_forecast = forecast_df.groupby('Date')['Forecast (Liters)'].sum().reset_index()

        fig_overall_forecast = go.Figure()
        fig_overall_forecast.add_trace(go.Bar(
            x=daily_campus_forecast["Date"],
            y=daily_campus_forecast["Forecast (Liters)"],
            name='Total Campus Forecast',
            marker_color='lightcoral'
        ))
        fig_overall_forecast.update_layout(
            title="Aggregated Daily Campus Demand Forecast",
            xaxis_title="Date",
            yaxis_title="Total Forecast (Liters)",
            hovermode="x unified",
            height=400,
            template="plotly_white"
        )
        st.plotly_chart(fig_overall_forecast, use_container_width=True)

    else:
        st.warning("Overall demand forecast data not available. Ensure 'demand_forecast.csv' exists and contains data.")

# --- TAB: All Alerts ---
with tab4:
    st.header("All Detected Leak Alerts")
    col_all_alerts1, col_all_alerts2 = st.columns(2)
    with col_all_alerts1:
        st.markdown("### 🌙 Night Leaks")
        if not night_df.empty:
            st.dataframe(night_df[["Date/Time", "Building", "Hourly Consumption (Liters)"]].sort_values("Date/Time", ascending=False), use_container_width=True)
        else:
            st.info("No night leaks recorded so far. Good job! 👍")
    with col_all_alerts2:
        st.markdown("### 📈 Spike Alerts")
        if not spike_df.empty:
            st.dataframe(spike_df[["Date/Time", "Building", "Hourly Consumption (Liters)"]].sort_values("Date/Time", ascending=False), use_container_width=True)
        else:
            st.info("No spike alerts recorded so far. Keep up the good work! 💪")

# --- TAB: Valve Control ---
with tab5:
    st.header("Valve Control Simulation")
    st.info("This section simulates sending commands to physical valves. In a real system, this would trigger IoT commands to close or open water supply.")

    if not df_combined.empty:
        with st.form("valve_control_form"):
            col_valve1, col_valve2 = st.columns(2)
            with col_valve1:
                valve_building = st.selectbox(
                    "Select Building for Valve Control:",
                    sorted(df_combined["Building"].unique()),
                    key="valve_building_select_tab"
                )
            with col_valve2:
                action = st.radio("Select Action:", ["Open Valve", "Close Valve"], key="valve_action_radio_tab")
            submitted = st.form_submit_button("Send Simulated Command")
            if submitted:
                st.success(f"✅ Simulated command sent: **{action}** valve for **{valve_building}**. "
                           "In a real system, this would trigger an actuator command.")
                # Removed st.balloons() for a more professional presentation
    else:
        st.warning("No building data available for valve control simulation.")
# --- SIDEBAR INFORMATION AND LEGEND ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Legend")
st.sidebar.markdown("- 🔴 **Leak / Active Alert**: Detected Night Leak or Spike Alert (from `leak_detection.py`).")
st.sidebar.markdown(f"- 🟠 **Active Flow**: Sensor is actively registering significant water flow (above {SIGNIFICANT_CONSUMPTION_THRESHOLD} L/hr).")
st.sidebar.markdown(f"- 🔵 **Low/No Flow**: Little to no active water flow (at or below {SIGNIFICANT_CONSUMPTION_THRESHOLD} L/hr).")
st.sidebar.markdown("---")
st.sidebar.markdown("🛠️ **Data Update Instructions:**")
st.sidebar.markdown("- Raw water data (`combined_water_data.csv`) is cached for 5 minutes.")
st.sidebar.markdown("- Leak alerts & forecasts are generated by external Python scripts.")
st.sidebar.markdown("- **To update alerts/forecasts:**")
st.sidebar.markdown("  1. Run `python /home/iiitb/campus_digital_twin/scripts/leak_detection.py`")
st.sidebar.markdown("  2. Run `python /home/iiitb/campus_digital_twin/scripts/forecast_demand.py`")
st.sidebar.markdown("  3. Click '🔄 Reload All Data (Clear Cache)' on the dashboard sidebar.")
st.sidebar.markdown("---")
st.sidebar.write("© 2025 IIIT Bengaluru — Water Management System")
st.sidebar.markdown("---")
