import pandas as pd
import glob
import os
import yaml

# Load config
with open(r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\config.yaml", "r") as f:
    config = yaml.safe_load(f)

buildings = config["buildings"]
file_pattern = config["file_format"]

# Output DataFrame
all_data = []

for building in buildings:
    pattern = rf"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\{file_pattern.replace('{building}', building)}"

    print(f"🔍 Looking for files with pattern: {pattern}") 
    files = glob.glob(pattern)
    print(f"📁 Found {len(files)} files for {building}")
    for file in files:
        try:
            df = pd.read_csv(file)
            df["Building"] = building
            df["Source File"] = os.path.basename(file)
            all_data.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

# Combine all data
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df["Date/Time"] = pd.to_datetime(combined_df["Date/Time"])
    combined_df = combined_df.sort_values(by=["Building", "Date/Time"])

    # Save cleaned dataset
    combined_df.to_csv(r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv", index=False)
    print("✅ Combined data saved to data/combined_water_data.csv")
else:
    print("⚠️ No data files found.")
