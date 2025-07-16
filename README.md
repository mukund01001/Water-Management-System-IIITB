````markdown
# 💧 Water Management System – IIIT Bengaluru

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](#) [![Node.js](https://img.shields.io/badge/Node.js-%3E%3D14-green)](#)

> **An end-to-end Embedded IoT + Digital Twin** platform for real-time campus water monitoring, forecasting, leak detection, and 3D visualization.

---

## 📋 Table of Contents

1. [🚀 Project Overview](#-project-overview)
2. [🌟 Features](#-features)
3. [🏗 Architecture & Components](#-architecture--components)
4. [⚙️ Prerequisites](#️-prerequisites)
5. [⚙️ Setup & Installation](#️-setup--installation)
6. [🚀 Quick Start](#-quick-start)
7. [📂 Directory Structure](#-directory-structure)
8. [🛠 Usage Examples](#-usage-examples)
9. [🐞 Troubleshooting](#-troubleshooting)
10. [📈 Roadmap](#-roadmap)
11. [🤝 Contributing](#-contributing)
12. [📄 License](#-license)

---

## 🚀 Project Overview

IIIT Bengaluru’s **Water Management System** delivers a full-stack solution encompassing:

- **IoT Data Collection:** 24 smart meters connected via microcontrollers
- **Data Pipeline:** Automated ingestion, validation & merging of raw sensor data
- **ML Analytics:** Leak detection with Isolation Forest and demand forecasting using Prophet
- **2D Visualization:** Interactive Streamlit dashboard for real-time metrics & alerts
- **3D Digital Twin:** Campus model in React + Three.js for spatial context
- **Automation:** End-to-end scheduling via shell script or systemd timers

This platform enables facility managers to monitor usage, predict demand, detect leaks early, and visualize campus water flow in 3D.

---

## 🌟 Features

- **Real-time Monitoring** of flow, pressure, and valve status
- **Leak Detection** with anomaly detection algorithms
- **3-Day Water Demand Forecasting** using Prophet
- **Interactive 2D Dashboard** with metrics, graphs & alerts
- **3D Digital Twin** for intuitive spatial mapping
- **Modular Architecture**: swap in new forecasting models or UI frameworks
- **Automated Scheduling**: CI-friendly pipeline orchestration

---

## 🏗 Architecture & Components

![Architecture Diagram](docs/architecture_diagram.png)

| Component                            | Description                                                                 |
| ------------------------------------ | --------------------------------------------------------------------------- |
| **Embedded IoT Data Collection**     | Raspberry Pi Pico W & ESP32 collect meter readings via I²C & MQTT           |
| **Data Ingestion & Processing**      | Python scripts validate, merge & store data as `data/combined_water_data.csv`|
| **Analytics & Forecasting**          | `scripts/leak_detection.py` & `scripts/forecast_demand.py`                  |
| **2D Dashboard (Streamlit)**         | `dashboard/enhanced_dashboard2.py`: dashboards + Plotly charts              |
| **3D Digital Twin (React + Three.js)**| `3D_DT/`: interactive 3D campus model                                       |
| **Automation & Scheduling**          | `run_all.sh` or Systemd timer to run pipeline every 30 minutes              |

---

## ⚙️ Prerequisites

- **Operating System:** Linux or macOS (Windows via WSL2)
- **Python:** 3.8 or higher
- **Node.js:** v14 or higher
- **npm/yarn:** for front-end dependencies
- **Git:** for version control

---

## ⚙️ Setup & Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/mukund01001/Water-Management-System-IIITB.git
   cd Water-Management-System-IIITB
````

2. **Python environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Front-end dependencies**

   ```bash
   cd 3D_DT
   npm install
   cd ..
   ```

4. **Make scripts executable**

   ```bash
   chmod +x run_all.sh
   ```

---

## 🚀 Quick Start

1. **Run full pipeline (ingestion → analytics → plots)**

   ```bash
   ./run_all.sh
   ```

2. **Launch 2D Dashboard**

   ```bash
   cd dashboard
   streamlit run enhanced_dashboard2.py
   ```

3. **Launch 3D Digital Twin**

   ```bash
   cd ../3D_DT
   npm run dev
   # Visit http://localhost:3000
   ```

---

## 📂 Directory Structure

```text
Water-Management-System-IIITB/
├── 3D_DT/                   # React + Three.js front-end
├── dashboard/               # Streamlit dashboard
├── data/                    # Raw & combined data files
├── docs/                    # Diagrams, screenshots & design docs
├── plots/                   # Forecast & usage visualizations
├── scripts/                 # Data ingestion & analytics scripts
├── run_all.sh               # Pipeline orchestration script
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

---

## 🛠 Usage Examples

### Data Ingestion

```bash
python3 scripts/packet_to_combined_water_data.py --input ./data/raw/ --output ./data/combined.csv
```

### Leak Detection

```bash
python3 scripts/leak_detection.py --data data/combined_water_data.csv --threshold 0.1
```

### Forecasting

```bash
python3 scripts/forecast_demand.py --data data/combined_water_data.csv --days 3
```

---

## 🐞 Troubleshooting

* **Missing dependencies:** ensure `venv` is activated and `pip install -r requirements.txt` succeeded.
* **Streamlit errors:** upgrade with `pip install --upgrade streamlit`.
* **Node build failures:** remove `node_modules/` and re-run `npm install`.
* **Permissions issues:** ensure `run_all.sh` has execute permissions (`chmod +x run_all.sh`).

---

## 📈 Roadmap

* [ ] Add user authentication & role-based access
* [ ] Integrate alert notifications via email/SMS
* [ ] Dockerize entire pipeline for easy deployment
* [ ] Support multiple campuses & scalability

---

## 🤝 Contributing

We welcome your contributions! Follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit changes: \`git commit -m "feat: add new feature"
4. Push to your branch: `git push origin feat/my-feature`
5. Open a Pull Request and describe your changes

Please adhere to the [Code of Conduct](CODE_OF_CONDUCT.md) and update tests as needed.

---

## 📄 License

This project is released under the [MIT License](LICENSE).

```
```
