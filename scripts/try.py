import pandas as pd

df = pd.read_csv("Packets.csv")

# Show the first few values of the 'sensor_data' column
print(df["sensor_data"].dropna().head(5).tolist())
