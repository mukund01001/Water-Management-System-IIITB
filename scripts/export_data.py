import pandas as pd
import json
import os

# Load data
df = pd.read_csv(r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv")
df["Date/Time"] = pd.to_datetime(df["Date/Time"])

# Convert to JSON-friendly format
records = []

for _, row in df.iterrows():
    # Extract meter_id from the 'Source File' (e.g., "Packet-2025-06-09-23-33.csv")
    filename = os.path.basename(str(row["Source File"]))
    meter_id = filename.replace("Packet-", "").replace(".csv", "")  # or customize further if needed

    records.append({
        "datetime": row["Date/Time"].isoformat(),
        "building": row["Building"],
        "consumption": row["Consumption (Liters)"],
        "totalizer": row["Totalizer (Liters)"],
        "meter_id": meter_id
    })

# Save to JSON file (into your frontend public folder)
output_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\3D_DT\public\combined_water_data.json"
with open(output_path, "w") as f:
    json.dump(records, f, indent=2)

print(f"✅ Export complete. JSON saved to:\n{output_path}")

# Task Scheduler is built into Windows and lets you run any script at intervals.

# ➤ How to Schedule It
# Suppose your script file is:

# makefile
# Copy
# Edit
# C:\Users\maila\OneDrive\Desktop\campus_digital_twin\3D_DT\scripts\export_data.py
# Open Start Menu → search “Task Scheduler”

# Click Create Basic Task

# Name it:



# Update DT JSON
# Choose:


# Daily
# Choose:

# sql
# Copy
# Edit
# Repeat task every: 10 minutes
# For a duration of: 1 day
# Action → Start a Program

# Program/script:

# nginx
# Copy
# Edit
# python
# Add arguments:

# arduino
# Copy
# Edit
# "C:\Users\maila\OneDrive\Desktop\campus_digital_twin\3D_DT\scripts\export_data.py"
# Finish.