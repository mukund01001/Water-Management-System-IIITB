import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set(style="whitegrid")

# === File Path ===
csv_path = r"C:\Users\maila\OneDrive\Desktop\campus_digital_twin\data\combined_water_data.csv"

# === Load and Clean Data ===
df = pd.read_csv(csv_path)
df["Date/Time"] = pd.to_datetime(df["Date/Time"])
df["Date"] = df["Date/Time"].dt.date
df["Hour"] = df["Date/Time"].dt.hour

# === Output Folder ===
output_dir = "water_usage_plots"
os.makedirs(output_dir, exist_ok=True)

# === 1. Daily Water Usage by Building ===
plt.figure(figsize=(12, 6))
daily_usage = df.groupby(["Date", "Building"])["Consumption (Liters)"].sum().reset_index()
sns.lineplot(data=daily_usage, x="Date", y="Consumption (Liters)", hue="Building", marker="o")
plt.title("📈 Daily Water Consumption per Building")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "daily_consumption_by_building.png"))
plt.close()

# === 2. Hourly Usage Pattern (Average by Building) ===
plt.figure(figsize=(10, 6))
hourly_avg = df.groupby(["Hour", "Building"])["Consumption (Liters)"].mean().reset_index()
sns.lineplot(data=hourly_avg, x="Hour", y="Consumption (Liters)", hue="Building", marker="o")
plt.title("🕓 Average Hourly Consumption Pattern")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "hourly_avg_by_building.png"))
plt.close()

# === 3. Boxplot: Distribution of Usage per Building ===
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x="Building", y="Consumption (Liters)")
plt.title("📦 Consumption Distribution by Building")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "boxplot_consumption.png"))
plt.close()

# === 4. Heatmap of Hourly Usage (Building x Hour) ===
pivot = df.groupby(["Building", "Hour"])["Consumption (Liters)"].mean().unstack()
plt.figure(figsize=(12, 6))
sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".1f")
plt.title("🌡️ Avg Hourly Water Usage (Heatmap)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "heatmap_hourly_usage.png"))
plt.close()

print("✅ Graphs saved in:", os.path.abspath(output_dir))
