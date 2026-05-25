# Data Dictionary — Synthetic Cover Glass Quality Dataset

> **Note:** All data in this project is **synthetic and simulated**. It does not represent real production data from Apple, Lens Technology, Corning, or any supplier.

## Dataset Overview

| Property | Value |
|----------|-------|
| Primary file | `data/raw/cover_glass_synthetic.csv` |
| Row count | ~50,000 (one row per `Glass_ID`) |
| Grain | One record per unit |
| Time span | Simulated multi-week production with embedded special causes |
| Primary use case | CNC edge chipping and chamfer variation analysis |

Each row represents a single cover glass unit traced from raw material through final inspection, with inline and end-of-line measurements attached.

**Phase 1 CSV columns (28):** all fields below in Traceability, CNC Process, CTQ, and Defect sections.

---

## Traceability Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Glass_ID` | string | — | `GLS-2026-0048127` | Unique unit identifier; primary join key |
| `Lot_ID` | string | — | `LOT-2026-W08-A` | Lot-level containment and yield tracking |
| `Product_Model` | string | — | `CG-Model-B` | Product-specific geometry and spec limits |
| `Raw_Glass_Batch` | string | — | `RGB-8841` | Upstream material traceability |
| `Line_ID` | string | — | `LINE-02` | Line-level throughput and configuration |
| `Machine_ID` | string | — | `CNC-04` | Machine-to-machine variation; key stratification for chipping RCA |
| `Tool_ID` | string | — | `TOOL-17` | Tool wear effects on chamfer and edge quality |
| `Fixture_ID` | string | — | `FIX-B2` | Clamping repeatability; known fixture bias scenarios |
| `Operator_ID` | string | — | `OP-023` | Operator setup variation (secondary to shift/machine) |
| `Shift` | string (category) | — | `Night` | Shift setup and staffing effects |
| `Process_Time` | datetime | — | `2026-02-18 02:14:33` | Time-series SPC, tool life correlation, shift boundaries |
| `Inspection_Station` | string | — | `AOI` | Primary inspection gate for defect capture |

---

## Process Parameter Fields (CNC Focus)

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Tool_Life_Pct` | float | % | `78.5` | Tool life consumed; chipping risk rises around **75%**, especially with coolant instability |
| `Spindle_Speed_rpm` | int | rpm | `24000` | Process stability context for CNC step |
| `Feed_Rate_mm_min` | float | mm/min | `850` | High feed can increase chipping on brittle edges |
| `Coolant_Pressure_bar` | float | bar | `3.2` | Coolant delivery; low pressure amplifies chipping when `Tool_Life_Pct` ≥ 75% |
| `Coolant_Pressure_Stability` | float | index | `0.97` | Coolant stability (1.0 = stable); instability amplifies wear-related chipping |
| `Vacuum_Level_kPa` | float | kPa | `-82.0` | Fixture vacuum level; weak vacuum can affect clamping repeatability |

---

## CTQ Measurement Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Chamfer_Width_mm` | float | mm | `0.312` | Primary dimensional CTQ from CNC; capability and SPC target |
| `Chipping_Size_um` | float | μm | `62.4` | Primary defect metric for edge chipping; 0 = no measurable chip |
| `Thickness_mm` | float | mm | `0.700` | Global thickness CTQ; target ~0.70 mm, spec 0.68–0.72 mm |
| `Warpage_mm` | float | mm | `0.038` | Flatness CTQ; downstream handling and assembly risk |
| `CS_MPa` | float | MPa | `782` | Compressive stress after ion exchange |
| `DOL_um` | float | μm | `43.1` | Depth of compressive layer |

---

## Defect and Inspection Fields

| Field Name | Data Type | Unit | Example | Why It Matters |
|------------|-----------|------|---------|----------------|
| `Defect_Type` | string (category) | — | `Edge_Chipping` | Defect mode for Pareto analysis (`None` for OK units) |
| `Defect_Location` | string (category) | — | `Edge` | Spatial pattern for heatmap (Edge, Corner, Camera_Hole, Speaker_Slot, etc.) |
| `AOI_Result` | string | — | `Fail` | Automated defect gate (`Pass` / `Fail`) |
| `Final_Result` | string | — | `NG` | Overall unit disposition (`OK` / `NG`) |

---

## Derived / Analysis Fields (Not in Raw CSV)

These are computed in analysis scripts or reserved for future processing—not present in `cover_glass_synthetic.csv`:

| Field Name | Source | Why It Matters |
|------------|--------|----------------|
| `Tool_Life_Bin` | `src/stratify.py`, `src/ml_risk.py` | Binned tool life for stratification |
| `Coolant_Stability_Bin` | `src/stratify.py`, `src/ml_risk.py` | Binned coolant stability for stratification |
| `Predicted_Risk` | `src/ml_risk.py` | Random forest Edge_Chipping probability |
| `Chamfer_Out_of_Spec` | Future processing | Quick filter against chamfer spec limits |
| `Chipping_Fail` | Future processing | Binary fail against chipping limit (> 80 μm) |

---

## Phase 2 / Deferred Fields (Not in Phase 1 CSV)

| Field Name | Status | Notes |
|------------|--------|-------|
| `Cycle_Time_sec` | Deferred | Planned CNC cadence field; not generated yet |
| `Haze_pct` | Deferred | Coating CTQ; Phase 2 |
| `Contact_Angle_deg` | Deferred | Coating CTQ; Phase 2 |
| `Defect_Count` | Deferred | Multiplicity count; Phase 1 uses one primary defect per unit |
| `Scrap_Flag` | Deferred | Disposition detail; Phase 1 uses `Final_Result` only |
| `Rework_Flag` | Deferred | Disposition detail; Phase 1 uses `Final_Result` only |
| `ORT_Sampled` | Deferred | Reliability sampling flag; Phase 2/3 |
| `ORT_Result` | Deferred | Reliability test outcome; Phase 2/3 |

---

## Data Quality and Simulation Rules

- **Fixed random seed** (`42`) for reproducibility.
- **Embedded special causes:** elevated chipping above 75% tool life, fixture chamfer bias (`FIX-B2`), night-shift coolant drift, high-risk machines (`CNC-04`, `CNC-06`).
- **Tool wear threshold:** chipping risk rises around **75%** `Tool_Life_Pct`, especially with coolant pressure instability.
- **No real company names** in field values or metadata.
- **Label clearly** in all outputs: "Simulated Data."

---

## File Locations

| File | Description |
|------|-------------|
| `data/raw/cover_glass_synthetic.csv` | Primary 50k-row Phase 1 dataset |
| `data/processed/` | Reserved for future derived datasets |
| `outputs/reports/` | Analysis CSV summaries and JMP workbook |
| `outputs/figures/` | Charts from analysis modules |

---

## Relationship to Analysis Modules

| Module | Primary Fields Used |
|--------|---------------------|
| `src/validate_data.py` | Schema and range checks on all CSV columns |
| `src/pareto.py` | `Defect_Type`, `AOI_Result`, `Final_Result` |
| `src/stratify.py` | `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`, `Tool_Life_Pct`, `Coolant_Pressure_Stability`, `Chipping_Size_um`, `Chamfer_Width_mm` |
| `src/spc.py` | `Chamfer_Width_mm`, `Chipping_Size_um`, `Process_Time`, `Machine_ID` |
| `src/capability.py` | `Chamfer_Width_mm`, `Thickness_mm`, spec limits |
| `src/heatmap.py` | `Machine_ID`, `Defect_Type`, `Defect_Location` |
| `src/ml_risk.py` | Process + traceability features → `Defect_Type == Edge_Chipping` |
| `src/export_jmp.py` | Exports raw CSV and report tables to Excel for JMP import |
