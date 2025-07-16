# validate_merge.py
import re
import pandas as pd
from pathlib import Path

# --- CONFIG ---
DATA_DIR = Path(__file__).parent.parent / "data"
COMBINED_CSV = DATA_DIR / "combined_water_data.csv"
PACKET_CSV  = DATA_DIR / "Packet-2025-06-09-23-33.csv"  # adjust to your latest file

# --- HELPERS ---
_float_cleaner = re.compile(r"[^\d\.]+")

def clean_float(x):
    """Strip any non-numeric chars and convert to float."""
    if pd.isna(x):
        return 0.0
    s = str(x)
    cleaned = _float_cleaner.sub("", s)
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def load_combined():
    print(f"🔍 Loading combined CSV from: {COMBINED_CSV}")
    df = pd.read_csv(COMBINED_CSV, parse_dates=["Date/Time"])
    print(f"   → {len(df)} rows")
    return df

def load_packets():
    print(f"🔍 Loading & grouping packets from: {PACKET_CSV}")
    pk = pd.read_csv(PACKET_CSV)
    
    # rename & parse
    pk = pk.rename(
        columns={
            "device_id":       "meter_id",
            "packet_sent_at":  "packet_time",
            "sensor_data":     "totalizer"
        }
    )
    # clean floats
    pk["totalizer"] = pk["totalizer"].apply(clean_float)
    # round packet_time to minute
    pk["Date/Time"] = pd.to_datetime(pk["packet_time"]).dt.floor("min")
    
    # group by meter & minute, take last totalizer reading
    grp = pk.groupby(["meter_id","Date/Time"], as_index=False)
    pk_min = grp.agg({"totalizer":"last"})
    
    print(f"   → {len(pk_min)} grouped rows")
    return pk_min

def validate():
    cb = load_combined()
    pk = load_packets()

    # --- Step 1: find meter ID column ---
    meter_id_col = None
    for col in cb.columns:
        if col.lower() in ("meter_id", "device_id", "building"):
            meter_id_col = col
            break

    if not meter_id_col:
        raise ValueError("❌ Could not find meter_id or device_id column in combined CSV")

    if meter_id_col != "meter_id":
        cb = cb.rename(columns={meter_id_col: "meter_id"})

    # --- Step 2: check timestamp column ---
    if "Date/Time" not in cb.columns:
        raise ValueError("❌ 'Date/Time' column not found in combined CSV")

    # --- 3) missing packet‑minute rows ---
    merged = pk.merge(
        cb,
        on=["meter_id", "Date/Time"],
        how="left",
        indicator=True,
        suffixes=("_pk", "_cb")
    )
    missing = merged[merged["_merge"] == "left_only"]
    if not missing.empty:
        print(f"\n❌ {len(missing)} packet‑minute rows missing from combined:")
        pkt_col = "totalizer" if "totalizer" in missing.columns else "totalizer_pk"
        cols = [c for c in ("meter_id", "Date/Time", pkt_col) if c in missing.columns]
        print(missing[cols].head().to_string(index=False))
    else:
        print("\n✅ No missing packet‑minute rows.")

    # --- 4) mismatched totalizer ---
    merged2 = pk.merge(
        cb,
        on=["meter_id", "Date/Time"],
        how="inner",
        suffixes=("_pk", "_cb")
    )

    cb_col = "Totalizer (Liters)"
    pk_col = "totalizer"
    pk_col2 = pk_col + "_pk"
    cb_col2 = cb_col + "_cb"

    if pk_col in merged2.columns and cb_col in merged2.columns:
        merged2 = merged2.rename(columns={pk_col: pk_col2, cb_col: cb_col2})
    elif pk_col2 not in merged2.columns or cb_col2 not in merged2.columns:
        raise RuntimeError(f"Expected '{pk_col2}' and '{cb_col2}' in merged data")

    mismatches = merged2[merged2[pk_col2] != merged2[cb_col2]]
    if not mismatches.empty:
        print(f"\n❌ {len(mismatches)} mismatched totalizer values:")
        print(
            mismatches[["meter_id", "Date/Time", pk_col2, cb_col2]].head().to_string(index=False)
        )
    else:
        print("\n✅ All totalizer values match.")


if __name__=="__main__":
    validate()
