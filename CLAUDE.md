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

First dataset target: about 50,000 rows.

Important fields:

- Glass_ID
- Lot_ID
- Product_Model
- Line_ID
- Machine_ID
- Tool_ID
- Fixture_ID
- Shift
- Operator_ID
- Process_Time
- Raw_Glass_Batch
- Inspection_Station
- Final_Result
- Chamfer_Width_mm
- Chipping_Size_um
- Thickness_mm
- Warpage_mm
- CS_MPa
- DOL_um
- AOI_Result
- Defect_Type
- Defect_Location

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

## Planned Structure

- data/raw/
- data/processed/
- notebooks/
- src/
- outputs/figures/
- outputs/reports/
- app/
- docs/

## Planned Modules

- src/generate_data.py
- src/validate_data.py
- src/pareto.py
- src/spc.py
- src/capability.py
- src/heatmap.py
- src/ml_risk.py
- app/app.py

## Interview Positioning

The project should emphasize:

Defect signature → Traceability → SPC → Capability → Root cause → Containment → Corrective action → Preventive control → Yield improvement