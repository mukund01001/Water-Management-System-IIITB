import pandas as pd
from prophet import Prophet
import yaml
import datetime
import matplotlib.pyplot as plt
import os

# --- Config ---
CONFIG_PATH = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\config.yaml"
DATA_PATH = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv"
FORECAST_PATH = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\demand_forecast.csv"
PLOTS_DIR = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\plots"

os.makedirs(PLOTS_DIR, exist_ok=True)

# --- Load config ---
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

forecast_days = config["forecast_days"]
buildings = config["buildings"]

# --- Load and preprocess data ---
df = pd.read_csv(DATA_PATH)
df["Date/Time"] = pd.to_datetime(df["Date/Time"])
df["Date"] = df["Date/Time"].dt.date

# --- Group daily consumption per building ---
daily = df.groupby(["Building", "Date"])["Consumption (Liters)"].sum().reset_index()

# --- Forecast and plot ---
results = []

for building in buildings:
    print(f"⏳ Processing: {building}")
    bdf = daily[daily["Building"] == building].copy()
    if bdf.empty:
        print(f"⚠️ No data for building: {building}")
        continue

    bdf.rename(columns={"Date": "ds", "Consumption (Liters)": "y"}, inplace=True)
    bdf["ds"] = pd.to_datetime(bdf["ds"])

    # Prophet model
    model = Prophet()
    model.add_seasonality(name='weekly', period=7, fourier_order=3)
    model.fit(bdf)

    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)

    # Plot
    fig = model.plot(forecast)
    plt.title(f"Water Consumption Forecast: {building}")
    plt.xlabel("Date")
    plt.ylabel("Liters")
    fig.savefig(os.path.join(PLOTS_DIR, f"{building}_forecast.png"))
    plt.close()

    # Store forecast
    forecast = forecast[["ds", "yhat"]].tail(forecast_days)
    forecast["Building"] = building
    forecast.rename(columns={"ds": "Date", "yhat": "Forecast (Liters)"}, inplace=True)
    forecast["Forecast (Liters)"] = forecast["Forecast (Liters)"].round(2)
    results.append(forecast)

# --- Save all forecasts to CSV ---
forecast_df = pd.concat(results)
forecast_df.to_csv(FORECAST_PATH, index=False)

print(f"✅ Forecast complete. Results saved to:\n→ {FORECAST_PATH}")
print(f"🖼️ Plots saved to folder:\n→ {PLOTS_DIR}")
