# 💧 Water Management System – IIIT B

> An end‑to‑end **Embedded IoT + Digital Twin** platform for real‑time campus water monitoring, forecasting, leak detection & 3D visualization.

---

## 📋 Table of Contents

1. [🚀 Project Overview](#-project-overview)
2. [🏗 Architecture & Components](#-architecture--components)

   * [1. Embedded IoT Data Collection](#1-embedded-iot-data-collection)
   * [2. Data Ingestion & Processing (Python)](#2-data-ingestion--processing-python)
   * [3. Analytics & Forecasting](#3-analytics--forecasting)
   * [4. 2D Dashboard (Streamlit)](#4-2d-dashboard-streamlit)
   * [5. 3D Digital Twin (React + Three.js)](#5-3d-digital-twin-react--threejs)
   * [6. Automation & Scheduling](#6-automation--scheduling)
3. [⚙️ Setup & Installation](#️-setup--installation)
4. [🚀 Quick Start](#-quick-start)
5. [📂 Directory Structure](#-directory-structure)
6. [🛠 Key Technologies & Tags](#-key-technologies--tags)
7. [🤝 Contributing](#-contributing)
8. [📄 License](#-license)

---

## 🚀 Project Overview

IIIT Bengaluru’s **Water Management System** demonstrates a complete pipeline—from meter‑level IoT sensing to:

* **2D Dashboard** with live usage, leak alerts & valve simulation
* **Demand Forecasting** (3‑day) via Facebook Prophet
* **3D Digital Twin** campus model powered by React + Three.js

**Flow**:

1. **IoT** → 24 meters → 3 DCUs
2. **Python** scripts ingest & merge into `data/combined_water_data.csv`
3. **ML**: Isolation Forest leak detection + Prophet forecasting
4. **UI**: Streamlit 2D & React 3D dashboards
5. **Automation**: `run_all.sh` or **systemd** timer every 30 min

---

## 🏗 Architecture & Components

### 1. Embedded IoT Data Collection

* **Sensors & DCUs**: 24 water meters → 3 DCUs
* **Microcontrollers**: Raspberry Pi Pico W, ESP32
* **Protocols**: I²C, MQTT, SCP/SSH

### 2. Data Ingestion & Processing (Python)

**Location**: `scripts/`

```bash
# group + validate packets → combined_water_data.csv
python3 scripts/packet_to_combined_water_data.py  
python3 scripts/validate_merge.py  

# analytics & plots
python3 scripts/leak_detection.py
python3 scripts/forecast_demand.py
python3 scripts/generate_water_usage_plots.py
```

### 3. Analytics & Forecasting

* **Leak Detection**: threshold + Isolation Forest (`scripts/leak_detection.py`)
* **Forecasting**: 3‑day Prophet model (`scripts/forecast_demand.py`) → `plots/{building}_forecast.png`

### 4. 2D Dashboard (Streamlit)

**Location**: `dashboard/`

```bash
# activate Python venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run dashboard
streamlit run dashboard/enhanced_dashboard2.py
```

### 5. 3D Digital Twin (React + Three.js)

**Location**: `3D_DT/`

```bash
cd 3D_DT
npm install
npm run dev
# open http://localhost:3000
```

### 6. Automation & Scheduling

Use `run_all.sh` or create a **systemd** timer for `scripts/run_all.sh` every 30 min:

```ini
# /etc/systemd/system/wms.timer
[Unit]
Description=Run WMS pipeline every 30min

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
```

---

## ⚙️ Setup & Installation

```bash
git clone https://github.com/mukund01001/Water-Management-System-IIITB.git
cd Water-Management-System-IIITB

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node for 3D front‑end
cd 3D_DT
npm install
```

---

## 🚀 Quick Start

```bash
# Generate data & plots
./run_all.sh

# 2D Dashboard
cd dashboard
streamlit run enhanced_dashboard2.py

# 3D Twin
cd ../3D_DT
npm run dev
```

---

## 📂 Directory Structure

```
.
├── 3D_DT/                   # React + Three.js front‑end
├── dashboard/               # Streamlit dashboards
├── data/                    # ingested CSVs & JSON
├── plots/                   # forecast & usage plots
├── scripts/                 # Python ingestion + analytics
├── run_all.sh               # orchestrate full pipeline
├── requirements.txt
└── README.md
```

---

## 🛠 Key Technologies & Tags

| Layer          | Tech & Tools                                |
| -------------- | ------------------------------------------- |
| IoT / Embedded | MQTT · I²C · Pico W · ESP32                 |
| Data / Python  | pandas · JSON · bash                        |
| ML             | Isolation Forest · Prophet                  |
| 2D UI          | Streamlit · Plotly                          |
| 3D UI          | React · Three.js · GLTF                     |
| Automation     | Bash · systemd timers                       |
| Dev            | Git · VS Code · Node.js · Vite · TypeScript |

---

## 🤝 Contributing

Fork & git clone

```bash
git checkout -b feat/my-feature
git commit -m "feat: describe"
git push & open a PR
```

---

## 📄 License

Released under the MIT License.
