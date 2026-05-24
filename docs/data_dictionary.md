# Data Dictionary — Synthetic Cover Glass Quality Dataset

> **Note:** All data in this project is **synthetic and simulated**. It is designed to be physically reasonable for cover glass manufacturing but does not represent real supplier, customer, or production data.

## Dataset Overview

| Property | Value |
|----------|-------|
| First dataset target | ~50,000 rows (one row per glass unit) |
| Grain | One record per `Glass_ID` |
| Time span | Simulated multi-week production with embedded special causes |
| Primary use case | CNC edge chipping and chamfer variation analysis |
| File format (planned) | CSV in `data/raw/`; processed parquet optional in `data/processed/` |

Each row represents a single cover glass unit traced from raw material through final inspection, with inline and end-of-line measurements attached.

---

## Traceability Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Glass_ID` | string | — | `GLS-2026-0048127` | Unique unit identifier; primary join key across inspections |
| `Lot_ID` | string | — | `LOT-2026-W08-A` | Lot-level containment and yield tracking |
| `Product_Model` | string | — | `CG-Model-B` | Product-specific geometry and spec limits |
| `Line_ID` | string | — | `LINE-02` | Line-level throughput and configuration differences |
| `Machine_ID` | string | — | `CNC-04` | Machine-to-machine variation; key stratification for chipping RCA |
| `Tool_ID` | string | — | `TOOL-17` | Tool wear effects on chamfer and edge quality |
| `Fixture_ID` | string | — | `FIX-B2` | Clamping repeatability; known fixture bias scenarios |
| `Shift` | string (category) | — | `Night` | Shift setup and staffing effects |
| `Operator_ID` | string | — | `OP-023` | Operator setup variation (secondary to shift/machine) |
| `Process_Time` | datetime | — | `2026-02-18 02:14:33` | Time-series SPC, tool life correlation, shift boundaries |
| `Raw_Glass_Batch` | string | — | `RGB-8841` | Upstream material traceability |

---

## Process Parameter Fields (CNC Focus)

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Tool_Life_Pct` | float | % | `78.5` | Tool life consumed; chipping risk begins to increase around **75%**, especially when combined with coolant pressure instability |
| `Coolant_Pressure_bar` | float | bar | `3.2` | Coolant delivery stability; low pressure amplifies chipping when `Tool_Life_Pct` ≥ 75% |
| `Spindle_Speed_rpm` | int | rpm | `24000` | Process stability context for CNC step |
| `Feed_Rate_mm_min` | float | mm/min | `850` | High feed can increase chipping on brittle edges |
| `Cycle_Time_sec` | float | sec | `42.3` | Proxy for process stability and handling cadence |

---

## CTQ Measurement Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Chamfer_Width_mm` | float | mm | `0.312` | Primary dimensional CTQ from CNC; capability and SPC target |
| `Chipping_Size_um` | float | μm | `62.4` | Primary defect metric for edge chipping story; 0 = no measurable chip |
| `Thickness_mm` | float | mm | `0.548` | Global thickness CTQ; affects strengthening and warpage |
| `Warpage_mm` | float | mm | `0.038` | Flatness CTQ; downstream handling and assembly risk |
| `CS_MPa` | float | MPa | `782` | Compressive stress after ion exchange |
| `DOL_um` | float | μm | `43.1` | Depth of compressive layer |
| `Haze_pct` | float | % | `0.32` | Optical quality; **Phase 2 / deferred** (coating products only; may be null) |
| `Contact_Angle_deg` | float | degrees | `112.5` | Coating performance; **Phase 2 / deferred** (may be null) |

---

## Defect and Inspection Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Inspection_Station` | string | — | `AOI` | Where the record's primary inspection outcome was captured |
| `AOI_Result` | string (pass/fail) | — | `Fail` | Automated defect gate; feeds Pareto and yield |
| `Defect_Type` | string (category) | — | `Edge_Chip` | Defect mode for Pareto analysis |
| `Defect_Location` | string (category) | — | `Edge_Long_Side` | Spatial pattern for heatmap (edge vs. corner vs. hole) |
| `Defect_Count` | int | count | `1` | Severity / multiplicity for Pareto weighting |

---

## Final Result Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Final_Result` | string (pass/fail) | — | `Fail` | Overall unit disposition after OQC logic |
| `Scrap_Flag` | bool | — | `True` | Whether unit was scrapped |
| `Rework_Flag` | bool | — | `False` | Rework path for yield accounting |
| `ORT_Sampled` | bool | — | `False` | Whether unit entered reliability sampling |
| `ORT_Result` | string (pass/fail/null) | — | `null` | Reliability outcome (sparse; mostly null) |

---

## Derived Fields (Planned, Generated in Processing)

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Chamfer_Out_of_Spec` | bool | — | `False` | Quick filter against chamfer spec limits |
| `Chipping_Fail` | bool | — | `True` | Binary fail against chipping limit (e.g., > 80 μm) |
| `Tool_Wear_Bin` | string | — | `High_75_90pct` | Binned tool life for stratification (≥ 75% = elevated chipping risk band) |
| `Week` | string | — | `2026-W08` | Weekly yield and SPC aggregation |
| `Risk_Score` | float | 0–1 | `0.73` | ML-predicted chipping risk (added after model training) |

---

## Data Quality and Simulation Rules

- **Fixed random seed** for reproducibility across generation runs.
- **Embedded special causes** in synthetic data (e.g., one `Machine_ID` + `Tool_ID` combination with elevated chipping above 75% tool life, one `Fixture_ID` with chamfer bias, night-shift `Coolant_Pressure_bar` drift).
- **Tool wear threshold:** chipping risk begins to increase around **75%** `Tool_Life_Pct`, especially when combined with coolant pressure instability.
- **Realistic null rates:** `ORT_Result` mostly null; coating CTQs may be null for non-coated models.
- **No real company names** in field values or metadata.
- **Label clearly** in all outputs: "Simulated Data."

---

## Planned File Locations

| File | Description |
|------|-------------|
| `data/raw/cover_glass_quality_simulated.csv` | Primary 50k-row dataset |
| `data/processed/cover_glass_with_derived.csv` | Adds derived fields and cleaned types |
| `outputs/reports/data_validation_summary.txt` | Output from `src/validate_data.py` |

---

## Relationship to Analysis Modules

| Module | Primary Fields Used |
|--------|---------------------|
| `src/pareto.py` | `Defect_Type`, `Defect_Count`, `AOI_Result`, `Final_Result` |
| `src/spc.py` | `Chamfer_Width_mm`, `Chipping_Size_um`, `Process_Time`, `Machine_ID` |
| `src/capability.py` | `Chamfer_Width_mm`, `Thickness_mm`, spec limits |
| `src/heatmap.py` | `Machine_ID`, `Shift`, `Defect_Type`, `Defect_Location` |
| `src/ml_risk.py` | `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`, `Tool_Life_Pct`, `Coolant_Pressure_bar`, `Spindle_Speed_rpm`, `Feed_Rate_mm_min` → `Chipping_Fail` |
