import pandas as pd
import json
import os

# Load your combined data
df = pd.read_csv(r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv")
df["Date/Time"] = pd.to_datetime(df["Date/Time"])

# Get last available hour
latest_time = df["Date/Time"].max()
hourly_data = df[df["Date/Time"] == latest_time]

# Prepare JSON structure
data_json = []
for _, row in hourly_data.iterrows():
    data_json.append({
        "meter_id": row["MeterID"],
        "building": row["Building"],
        "floor": row["Floor"],
        "location": row["Location"],
        "value": row["Consumption (Liters)"],
        "timestamp": row["Date/Time"].strftime("%Y-%m-%d %H:%M:%S"),
    })

# Save JSON
output_dir = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\3D_DT\public\json"
os.makedirs(output_dir, exist_ok=True)

with open(os.path.join(output_dir, "combined_water_data.json"), "w") as f:
    json.dump(data_json, f, indent=2)

print("✅ JSON exported successfully!")
