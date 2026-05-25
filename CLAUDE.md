# CLAUDE.md

This repository is a portfolio-style manufacturing quality analytics project for a cover glass / brittle materials MQE role.

## Project Goal

Build a simulated but physically reasonable cover glass manufacturing quality analytics project.

The purpose is to demonstrate MQE problem solving, not to claim access to real Apple or supplier confidential data.

All data must be synthetic and clearly labeled as simulated.

## Core Story

A high-volume cover glass production line shows increased edge chipping and dimension variation.

The project should use:

- Traceability
- Pareto analysis
- SPC control charts
- Process capability analysis
- Root cause analysis
- Simple ML risk prediction
- Preventive quality control recommendations

The main focus is CNC-related edge chipping, tool wear, coolant pressure, fixture effects, machine variation, and shift effects.

ML is a supporting tool. It should not become the main story.

## Manufacturing Context

Simulated process flow:

Incoming glass inspection → Cutting or laser cutting → CNC contour / drilling / chamfering → Edge polishing → Cleaning → Chemical strengthening → Coating or printing → AOI inspection → OQC → ORT / reliability testing

Do not over-expand into too many unrelated defects in the first version.

## Synthetic Data Rules

Use synthetic data only.

Do not imply the data comes from Apple, Lens Technology, Corning, or any real supplier.

Primary dataset: `data/raw/cover_glass_synthetic.csv` (~50,000 rows).

Phase 1 CSV fields:

- Glass_ID, Lot_ID, Product_Model, Raw_Glass_Batch, Line_ID
- Machine_ID, Tool_ID, Fixture_ID, Operator_ID, Shift, Process_Time, Inspection_Station
- Tool_Life_Pct, Spindle_Speed_rpm, Feed_Rate_mm_min, Coolant_Pressure_bar, Coolant_Pressure_Stability, Vacuum_Level_kPa
- Chamfer_Width_mm, Chipping_Size_um, Thickness_mm, Warpage_mm, CS_MPa, DOL_um
- Defect_Type, Defect_Location, AOI_Result, Final_Result

## Coding Rules

Use Python 3.12 and uv.

Keep code beginner-readable with clear comments.

Prefer small modular scripts instead of one huge file.

Approved libraries:

- pandas
- numpy
- scikit-learn
- matplotlib
- streamlit
- openpyxl
- jupyter

Do not use seaborn unless explicitly requested.

Use fixed random seeds.

Do not use hardcoded local absolute paths.

Before large or multi-file changes, first explain the plan and list files to be changed.

## Repository Structure

- data/raw/ — `cover_glass_synthetic.csv`
- data/processed/ — reserved for derived datasets
- notebooks/
- src/
- outputs/figures/
- outputs/reports/
- app/ — Streamlit (Phase 2, not implemented)
- docs/

## Implemented Modules (Phase 1)

- src/generate_data.py
- src/validate_data.py
- src/pareto.py
- src/stratify.py
- src/spc.py
- src/capability.py
- src/heatmap.py
- src/ml_risk.py
- src/export_jmp.py

## Phase 2 / Not Yet Implemented

- app/app.py — Streamlit dashboard (optional)
- Deferred CSV fields: Cycle_Time_sec, Haze_pct, Contact_Angle_deg, Defect_Count, Scrap_Flag, Rework_Flag, ORT_Sampled, ORT_Result

## Interview Positioning

The project should emphasize:

Defect signature → Traceability → SPC → Capability → Root cause → Containment → Corrective action → Preventive control → Yield improvement
