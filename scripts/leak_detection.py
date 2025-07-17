import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime
import os
import numpy as np

# === CONFIGURATION ===
PROJECT_ROOT = "/home/iiitb/campus_digital_twin" # Ensure this path is correct
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")

DATA_PATH = os.path.join(DATA_FOLDER, "combined_water_data.csv")
SPIKE_ALERT_PATH = os.path.join(DATA_FOLDER, "spike_alerts.csv")
NIGHT_LEAK_PATH = os.path.join(DATA_FOLDER, "night_leak_alerts.csv")

# --- New Threshold for "No Flow" ---
# Any hourly consumption at or below this value will be considered "no flow" for leak detection
# Adjust this based on sensor precision and what you consider negligible usage.
NO_FLOW_THRESHOLD = 0.05 # For example, 50 milliliters per hour, accounting for sensor noise

print("--- Starting Leak Detection ---")
print(f"Loading data from: {DATA_PATH}")

# === LOAD AND PREPROCESS DATA ===
try:
    df = pd.read_csv(DATA_PATH, parse_dates=["Date/Time"])
    print(f"Successfully loaded {len(df)} records.")
except FileNotFoundError:
    print(f"❌ Error: 'combined_water_data.csv' not found at {DATA_PATH}.")
    print("Please ensure your data aggregation scripts have been run to generate this file.")
    # Create empty alert files with headers to avoid dashboard errors
    pd.DataFrame(columns=['Date/Time', 'Building', 'Hourly Consumption (Liters)']).to_csv(SPIKE_ALERT_PATH, index=False)
    pd.DataFrame(columns=['Date/Time', 'Building', 'Hourly Consumption (Liters)']).to_csv(NIGHT_LEAK_PATH, index=False)
    exit()
except Exception as e:
    print(f"❌ Error loading or parsing data: {e}")
    # Create empty alert files with headers
    pd.DataFrame(columns=['Date/Time', 'Building', 'Hourly Consumption (Liters)']).to_csv(SPIKE_ALERT_PATH, index=False)
    pd.DataFrame(columns=['Date/Time', 'Building', 'Hourly Consumption (Liters)']).to_csv(NIGHT_LEAK_PATH, index=False)
    exit()

df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
df.dropna(subset=['Date/Time'], inplace=True)
df = df.sort_values(by=['Building', 'Date/Time']).reset_index(drop=True)

df['Consumption (Liters)'] = df['Consumption (Liters)'].apply(lambda x: max(0, x))

df['Hourly Consumption (Liters)'] = df.groupby('Building')['Consumption (Liters)'].diff().fillna(0)
df['Hourly Consumption (Liters)'] = df['Hourly Consumption (Liters)'].apply(lambda x: max(0, x))

df["Hour"] = df["Date/Time"].dt.hour
df["DayOfWeek"] = df["Date/Time"].dt.dayofweek # Monday=0, Sunday=6

# Initialize anomaly column to 1 (not anomaly)
df['anomaly'] = 1

# === NIGHT LEAK DETECTION (0-5 AM: Should be near zero flow) ===
# We are looking for small, *persistent* flows when there should be no activity.
night_df = df[(df["Hour"] >= 0) & (df["Hour"] <= 5) & (df["Hourly Consumption (Liters)"] > NO_FLOW_THRESHOLD)].copy()

if not night_df.empty:
    print(f"Detecting night leaks from {len(night_df)} night-time consumption points...")
    # Features for night leaks: just the consumption value
    # Contamination should be set relatively low, as we expect few actual night leaks
    night_features = night_df[["Hourly Consumption (Liters)"]].copy()
    model_night = IsolationForest(n_estimators=100, contamination=0.01, random_state=42) # Adjust contamination
    
    # Handle potential inf/nan
    night_features.replace([np.inf, -np.inf], np.nan, inplace=True)
    night_features.dropna(inplace=True)

    if not night_features.empty:
        night_df.loc[night_features.index, "anomaly"] = model_night.fit_predict(night_features)
    else:
        print("No valid night features after cleaning.")
else:
    print("No significant night-time consumption data to detect night leaks.")

# === SPIKE ALERT DETECTION (Active Hours: 6 AM - 23 PM) ===
# We are looking for unusually high consumption spikes during active hours.
active_df = df[(df["Hour"] >= 6) | (df["Hour"] <= 23)].copy() # Covers 6 AM to 11 PM
# Only consider consumption above the no-flow threshold for spikes
active_df = active_df[active_df["Hourly Consumption (Liters)"] > NO_FLOW_THRESHOLD].copy()


if not active_df.empty:
    print(f"Detecting spike alerts from {len(active_df)} active-hour consumption points...")
    # Features for spike alerts: consumption, hour, day of week
    active_features = active_df[["Hourly Consumption (Liters)", "Hour", "DayOfWeek"]].copy()
    model_active = IsolationForest(n_estimators=100, contamination=0.02, random_state=42) # Adjust contamination

    # Handle potential inf/nan
    active_features.replace([np.inf, -np.inf], np.nan, inplace=True)
    active_features.dropna(inplace=True)

    if not active_features.empty:
        active_df.loc[active_features.index, "anomaly"] = model_active.fit_predict(active_features)
    else:
        print("No valid active hour features after cleaning.")
else:
    print("No significant active-hour consumption data to detect spike alerts.")


# === COMBINE ANOMALIES AND CLASSIFY ===
# Update the main df's anomaly column based on detected anomalies in night_df and active_df
if 'anomaly' in night_df.columns:
    df.loc[night_df[night_df['anomaly'] == -1].index, 'anomaly'] = -1
if 'anomaly' in active_df.columns:
    df.loc[active_df[active_df['anomaly'] == -1].index, 'anomaly'] = -1

# Filter for all detected anomalies
anomalies_final_df = df[df["anomaly"] == -1].copy()

# Separate into spike alerts and night leaks based on hour and NO_FLOW_THRESHOLD
night_leak_alerts = anomalies_final_df[(anomalies_final_df["Hour"] >= 0) & \
                                       (anomalies_final_df["Hour"] <= 5) & \
                                       (anomalies_final_df["Hourly Consumption (Liters)"] > NO_FLOW_THRESHOLD)].copy()

spike_alerts = anomalies_final_df[~anomalies_final_df.index.isin(night_leak_alerts.index)].copy()
# Also ensure spike alerts have consumption above the no-flow threshold
spike_alerts = spike_alerts[spike_alerts["Hourly Consumption (Liters)"] > NO_FLOW_THRESHOLD].copy()


# === SAVE RESULTS FOR DASHBOARD ===
required_cols = ['Date/Time', 'Building', 'Hourly Consumption (Liters)']

# Ensure alert files are created with correct columns, even if empty
if not spike_alerts.empty:
    spike_alerts[required_cols].to_csv(SPIKE_ALERT_PATH, index=False)
else:
    pd.DataFrame(columns=required_cols).to_csv(SPIKE_ALERT_PATH, index=False)

if not night_leak_alerts.empty:
    night_leak_alerts[required_cols].to_csv(NIGHT_LEAK_PATH, index=False)
else:
    pd.DataFrame(columns=required_cols).to_csv(NIGHT_LEAK_PATH, index=False)

print("✅ Leak detection completed.")
print(f"  - Spike Alerts Saved: {SPIKE_ALERT_PATH}")
print(f"  - Night Leak Alerts Saved: {NIGHT_LEAK_PATH}")
print(f"📈 Total Spike Alerts: {len(spike_alerts)} | 🌙 Total Night Leak Alerts: {len(night_leak_alerts)}")
