#!/usr/bin/env python3
import os, glob, json
import pandas as pd

# ——— CONFIGURATION ——————————————————————————————————————
# (the script file is in scripts/, data/ is sibling)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
COMBINED_CSV = os.path.join(BASE_DIR, "combined_water_data.csv")
PACKET_GLOB = os.path.join(BASE_DIR, "Packet-*.csv")
# ————————————————————————————————————————————————————————


def main():
    # 1) load existing combined data
    combined = pd.read_csv(COMBINED_CSV, parse_dates=["Date/Time"])
    if combined.empty:
        last_ts = pd.Timestamp.min
    else:
        last_ts = combined["Date/Time"].max()

    # 2) find packet files
    packet_files = sorted(glob.glob(PACKET_GLOB))
    new_rows = []

    for pf in packet_files:
        df = pd.read_csv(pf)
        # parse packet_sent_at into a Timestamp
        df["ts"] = pd.to_datetime(df["packet_sent_at"], errors="coerce")
        # only keep strictly newer than last_ts
        df = df[df["ts"] > last_ts]

        for _, row in df.iterrows():
            ts = row["ts"].floor("min")
            try:
                payload = json.loads(row["sensor_data"])
            except json.JSONDecodeError:
                continue
            for reading in payload.get("t", []):
                il = reading.get("il")
                r  = reading.get("r")
                if il is None or r is None:
                    continue
                try:
                    tot = float(r)
                except:
                    continue

                new_rows.append({
                    "Date/Time": ts,
                    "Totalizer (Liters)": tot,
                    "Building": il,
                    "Source File": os.path.basename(pf)
                })

    if not new_rows:
        print("❌ No new packets found since", last_ts)
        return

    # 3) build DataFrame of all new readings
    new_df = pd.DataFrame(new_rows)
    new_df.sort_values(["Building", "Date/Time"], inplace=True)

    # 4) compute consumption as diff of totalizer
    new_df["Consumption (Liters)"] = (
        new_df
        .groupby("Building")["Totalizer (Liters)"]
        .diff()
        .fillna(0)
    )

    # 5) append and re-sort
    combined_updated = pd.concat([combined, new_df], ignore_index=True)
    combined_updated.sort_values("Date/Time", inplace=True)

    # 6) save back (same columns, same order)
    cols = ["Date/Time", "Totalizer (Liters)", "Consumption (Liters)", "Building", "Source File"]
    combined_updated.to_csv(COMBINED_CSV, columns=cols, index=False)

    print(f"✅ Appended {len(new_df)} new readings. Combined updated.")

if __name__ == "__main__":
    main()
