#!/bin/bash

# Activate venv
source /home/iiitb/campus_digital_twin/venv/bin/activate

# Go to scripts dir
cd /home/iiitb/campus_digital_twin/scripts

# Run scripts
echo "====== Running all scripts at $(date) ======"

python export_data.py
python forecast_demand.py
python generate_water_usage_plots.py
python leak_detection.py
python packet_to_combined_water_data.py
python update_yaml.py
python validate_merge.py

echo "====== All scripts done at $(date) ======"
