import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime

# === CONFIGURATION ===
data_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv"
spike_alert_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\spike_alerts.csv"
night_leak_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\night_leak_alerts.csv"

# === LOAD DATA ===
df = pd.read_csv(data_path)
df["Date/Time"] = pd.to_datetime(df["Date/Time"])
df["Hour"] = df["Date/Time"].dt.hour
df["DayOfWeek"] = df["Date/Time"].dt.dayofweek

# === FEATURE ENGINEERING ===
features = df[["Consumption (Liters)", "Hour", "DayOfWeek"]].copy()

# === TRAIN MODEL ===
model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
df["anomaly"] = model.fit_predict(features)

# === CLASSIFY ALERTS ===
spike_alerts = df[df["anomaly"] == -1]
night_leak_alerts = spike_alerts[(spike_alerts["Hour"] >= 0) & (spike_alerts["Hour"] <= 5)]

# === SAVE RESULTS FOR DASHBOARD ===
spike_alerts.to_csv(spike_alert_path, index=False)
night_leak_alerts.to_csv(night_leak_path, index=False)

print("✅ Leak detection completed.")
print(f"  - Spike Alerts Saved: {spike_alert_path}")
print(f"  - Night Leak Alerts Saved: {night_leak_path}")
print(f"📈 Total Spike Alerts: {len(spike_alerts)} | 🌙 Night Alerts: {len(night_leak_alerts)}")
