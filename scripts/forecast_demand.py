import pandas as pd
from prophet import Prophet
import yaml
import datetime
import matplotlib.pyplot as plt
import os
import numpy as np # Import numpy for numerical operations

# --- Config ---
# Ensure this path is correct for your environment
PROJECT_ROOT = "/home/iiitb/campus_digital_twin"
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "combined_water_data.csv")
FORECAST_PATH = os.path.join(PROJECT_ROOT, "data", "demand_forecast.csv")
PLOTS_DIR = os.path.join(PROJECT_ROOT, "plots")

os.makedirs(PLOTS_DIR, exist_ok=True)
print("--- Starting Demand Forecasting ---")

# --- Load config ---
try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"❌ Error: 'config.yaml' not found at {CONFIG_PATH}.")
    print("Please ensure config.yaml exists and is accessible.")
    exit()
except Exception as e:
    print(f"❌ Error loading config.yaml: {e}")
    exit()

forecast_days = config.get("forecast_days", 3) # Default to 3 days if not specified in config
buildings = config.get("buildings", []) # Default to empty list if not specified

if not buildings:
    print("⚠️ No buildings specified in config.yaml. Please define 'buildings' list.")
    exit()

print(f"Forecasting for the next {forecast_days} days.")

# --- Load and preprocess data ---
try:
    df = pd.read_csv(DATA_PATH, parse_dates=["Date/Time"])
    print(f"Successfully loaded {len(df)} records from {DATA_PATH}.")
except FileNotFoundError:
    print(f"❌ Error: 'combined_water_data.csv' not found at {DATA_PATH}.")
    print("Please ensure your data aggregation scripts have been run to generate this file.")
    exit()
except Exception as e:
    print(f"❌ Error loading or parsing data: {e}")
    exit()

df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors='coerce')
df.dropna(subset=['Date/Time'], inplace=True)
df["Date"] = df["Date/Time"].dt.date

# Ensure 'Consumption (Liters)' is non-negative before summing
df['Consumption (Liters)'] = df['Consumption (Liters)'].apply(lambda x: max(0, x))

# --- Group daily consumption per building ---
daily = df.groupby(["Building", "Date"])["Consumption (Liters)"].sum().reset_index()

# --- Forecast and plot ---
results = []

for building in buildings:
    print(f"⏳ Processing forecast for: {building}")
    bdf = daily[daily["Building"] == building].copy()
    if bdf.empty:
        print(f"⚠️ No historical data for building: {building}. Skipping forecast.")
        continue

    # Prophet requires 'ds' (datestamp) and 'y' (value)
    bdf.rename(columns={"Date": "ds", "Consumption (Liters)": "y"}, inplace=True)
    bdf["ds"] = pd.to_datetime(bdf["ds"])

    # Prophet model
    model = Prophet(
        seasonality_mode='multiplicative', # Good for consumption data where seasonality scales with trend
        weekly_seasonality=True,
        daily_seasonality=False # Daily seasonality often captured by hourly if data is granular enough
    )
    # Add yearly seasonality if you have more than a year of data
    # model.add_seasonality(name='yearly', period=365.25, fourier_order=10)
    # model.add_seasonality(name='weekly', period=7, fourier_order=3) # Already enabled by weekly_seasonality=True

    model.fit(bdf)

    future = model.make_future_dataframe(periods=forecast_days, include_history=False) # Only future dates
    if future.empty:
        print(f"⚠️ Could not generate future dataframe for {building}. Skipping forecast.")
        continue

    forecast = model.predict(future)

    # Ensure forecasts are non-negative
    forecast["yhat"] = np.maximum(0, forecast["yhat"])
    forecast["yhat_lower"] = np.maximum(0, forecast["yhat_lower"])
    forecast["yhat_upper"] = np.maximum(0, forecast["yhat_upper"])


    # Plot and save
    fig = model.plot(forecast, xlabel="Date", ylabel="Forecasted Liters")
    plt.title(f"Water Consumption Forecast: {building}")
    plt.xlabel("Date")
    plt.ylabel("Liters")
    fig.savefig(os.path.join(PLOTS_DIR, f"{building}_forecast.png"))
    plt.close(fig) # Close the figure to free memory

    # Store forecast results
    forecast_current_building = forecast[["ds", "yhat"]].copy()
    forecast_current_building["Building"] = building
    forecast_current_building.rename(columns={"ds": "Date", "yhat": "Forecast (Liters)"}, inplace=True)
    forecast_current_building["Forecast (Liters)"] = forecast_current_building["Forecast (Liters)"].round(2)
    results.append(forecast_current_building)

# --- Save all forecasts to CSV ---
if results:
    forecast_df = pd.concat(results)
    forecast_df.to_csv(FORECAST_PATH, index=False)
    print(f"✅ Forecast complete. Results saved to:\n→ {FORECAST_PATH}")
else:
    print("⚠️ No forecasts generated for any building. 'demand_forecast.csv' will be empty or not updated.")
    # Ensure an empty but correctly structured CSV is created if no forecasts
    pd.DataFrame(columns=['Date', 'Forecast (Liters)', 'Building']).to_csv(FORECAST_PATH, index=False)


print(f"🖼️ Plots saved to folder:\n→ {PLOTS_DIR}")
