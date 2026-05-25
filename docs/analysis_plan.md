# Analysis Plan — Cover Glass Quality (Simulated)

> **Note:** This plan covers a portfolio-style MQE investigation using **synthetic data only**. ML supports the story; it is not the headline. Primary dataset: `data/raw/cover_glass_synthetic.csv`.

## Problem Statement

A high-volume cover glass line shows **increased edge chipping and chamfer width variation** after CNC contouring. Yield at AOI/OQC has dipped. The goal is to identify high-risk process windows, confirm root causes with data, and recommend preventive controls.

---

## Analysis Workflow Overview

```text
1. Defect signature (Pareto)                    ✅ src/pareto.py
        ↓
2. Root cause stratification                    ✅ src/stratify.py
        ↓
3. SPC — special vs. common cause             ✅ src/spc.py
        ↓
4. Process capability (Cp/Cpk)                ✅ src/capability.py
        ↓
5. Defect location heatmap                      ✅ src/heatmap.py
        ↓
6. ML risk screening (supporting)               ✅ src/ml_risk.py
        ↓
7. JMP export for live demo                     ✅ src/export_jmp.py
        ↓
8. Containment → Corrective → Preventive recommendations (narrative)
        ↓
9. JMP deep-dive (manual confirmatory analysis)
```

---

## Step-by-Step Plan

### Step 1 — Defect Signature (Pareto) ✅ Implemented

**Objective:** Confirm edge chip is the dominant fail mode and quantify yield impact.

**Inputs:** `Defect_Type`, `AOI_Result`, `Final_Result`, `Process_Time`

**Python (`src/pareto.py`):**
- Pareto chart of NG defect types (count and cumulative %)
- Export summary CSV and figure to `outputs/reports/` and `outputs/figures/`

**JMP (manual live demo):**
- Interactive Pareto with filtering by `Product_Model` and date range

---

### Step 2 — Root Cause Stratification ✅ Implemented

**Objective:** Narrow the problem to specific machines, fixtures, shifts, and process bins.

**Inputs:** `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`, `Tool_Life_Pct`, `Coolant_Pressure_Stability`, `Chipping_Size_um`, `Chamfer_Width_mm`

**Python (`src/stratify.py`):**
- Grouped fail rate summaries by machine, fixture, shift, tool life bin, coolant stability bin
- Interaction summaries (tool life × coolant, machine × fixture)
- Output: `outputs/reports/chipping_stratification_summary.csv`

**JMP (manual live demo):**
- Graph Builder: compare `Chipping_Size_um` across `Machine_ID`, `Fixture_ID`, `Shift`
- Tabulate fail rates by tool life and coolant stability bins

---

### Step 3 — SPC Control Charts ✅ Implemented

**Objective:** Detect special cause signals on key CTQs; distinguish drift from step change.

**Inputs:** `Chamfer_Width_mm`, `Chipping_Size_um`, `Process_Time`, `Machine_ID`

**Python (`src/spc.py`):**
- X-bar/R on chamfer width (CNC-04, subgroup n=5)
- I-MR on chipping size (CNC-04, latest 500 parts)
- Output: `outputs/reports/spc_*_summary.csv`, `outputs/figures/*_chart.png`

**JMP (manual live demo):**
- Control Chart Builder with automatic rule tagging

---

### Step 4 — Process Capability ✅ Implemented

**Objective:** Quantify whether chamfer width meets spec across normal vs high-risk windows.

**Inputs:** `Chamfer_Width_mm`, spec limits (LSL 0.25, target 0.30, USL 0.35 mm)

**Python (`src/capability.py`):**
- Cp, Cpk, Pp, Ppk by analysis group (all data, CNC-04, tool life bins, coolant bins, interactions)
- Output: `outputs/reports/capability_summary.csv`, `outputs/figures/chamfer_capability_distribution.png`

**JMP (manual live demo):**
- Process Capability platform with spec limit editor

---

### Step 5 — Defect Location Heatmap ✅ Implemented

**Objective:** Visualize where Edge_Chipping occurs on the part and by machine.

**Inputs:** `Machine_ID`, `Defect_Type`, `Defect_Location`

**Python (`src/heatmap.py`):**
- Location and machine summaries; Machine × Location heatmap
- Output: `outputs/reports/defect_location_summary.csv`, `outputs/figures/chipping_location_heatmap.png`

**JMP (manual live demo):**
- Graph Builder contingency plots by `Defect_Location`

---

### Step 6 — ML Risk Screening (Supporting) ✅ Implemented

**Objective:** Flag high-risk process windows for preventive review—not to replace engineering judgment. This is the **only** step that uses predictive ML models.

**Inputs:** `Tool_Life_Pct`, `Spindle_Speed_rpm`, `Feed_Rate_mm_min`, `Coolant_Pressure_bar`, `Coolant_Pressure_Stability`, `Vacuum_Level_kPa`, `Chamfer_Width_mm`, `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift` → target `Defect_Type == Edge_Chipping`

**Python (`src/ml_risk.py`):**
- Logistic regression (interpretable baseline) and random forest (nonlinear)
- Feature importance chart; high-risk window summary
- Output: `outputs/reports/ml_risk_model_summary.csv`, `outputs/reports/high_risk_windows.csv`, `outputs/figures/ml_feature_importance.png`

**Scope limits:**
- No deep learning; no claim of production deployment
- Present as "prioritization aid" in interview narrative

---

### Step 7 — JMP Export ✅ Implemented

**Objective:** Package Python outputs for manual JMP import during interview demo.

**Python (`src/export_jmp.py`):**
- Export workbook: `outputs/reports/jmp_export_cover_glass_quality.xlsx`
- Sheets: README, raw data sample, Pareto, stratification, SPC, capability, location, ML summaries

**JMP (manual / live demo only):**
- Import Excel workbook; all JMP work is interactive—not scripted from Python
- Recommended platforms: Distribution, Graph Builder, Fit Y by X, Control Chart Builder, Process Capability

---

### Step 8 — Recommendations and Yield Improvement Narrative

**Containment (immediate):**
- Hold lots from high-risk `Machine_ID + Tool_ID` window
- Increase sampling at AOI for affected shift

**Corrective action:**
- Replace worn tools above 75% life limit
- Restore coolant pressure setpoint on Night shift
- Re-qualify `FIX-B2`; adjust chamfer offset

**Preventive control:**
- SPC alerts on chamfer width with auto-stop rule
- Tool life hard stop at 75%
- Coolant pressure interlock log
- ML risk review queue (optional Streamlit dashboard — **not implemented**)

---

## Python vs. JMP Division of Labor

| Activity | Python | JMP |
|----------|--------|-----|
| Data generation & validation | ✅ Primary | — |
| Automated batch charts & reports | ✅ Primary | — |
| Pareto, SPC, capability, heatmap, ML | ✅ Primary | — |
| Data export for JMP | ✅ Primary (Excel workbook) | — |
| Interactive confirmatory analysis | — | ✅ Manual live demo only |
| Interview demo | Python pipeline + exported workbook | Live JMP walkthrough |
| Reproducible pipeline | ✅ Primary | Not scripted from Python |

---

## Implemented Code Modules

| Module | Output |
|--------|--------|
| `src/generate_data.py` | `data/raw/cover_glass_synthetic.csv` |
| `src/validate_data.py` | Validation report (stdout) |
| `src/pareto.py` | Pareto chart + CSV |
| `src/stratify.py` | Root cause stratification CSV |
| `src/spc.py` | SPC summaries + charts |
| `src/capability.py` | Capability summary + chart |
| `src/heatmap.py` | Location summary + heatmap |
| `src/ml_risk.py` | ML metrics + high-risk windows |
| `src/export_jmp.py` | JMP Excel workbook |

---

## Interview Positioning Flow

```text
Defect signature
    → Traceability (where / when / who)
        → SPC (special cause?)
            → Capability (spec margin?)
                → Root cause (tool, coolant, fixture, machine, shift)
                    → Containment (lot hold, sorting)
                        → Corrective action (fix the cause)
                            → Preventive control (SPC, interlocks, tool life)
                                → Yield improvement (measurable recovery)
```

**Key message:** ML enters **after** engineering traceability and SPC confirm the problem is real and localized—not before.

---

## Phase Boundaries

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | CNC chipping, chamfer, traceability, AOI yield, full Python pipeline, JMP export | **Complete** |
| Phase 2 | CS/DOL deep dive; coating CTQs (`Haze_pct`, `Contact_Angle_deg`); optional Streamlit dashboard | Planned |
| Phase 3 | ORT sampling (`ORT_Sampled`, `ORT_Result`); disposition flags (`Scrap_Flag`, `Rework_Flag`) | Planned |
| Phase 4 | Derived processing dataset in `data/processed/`; within-subgroup sigma for capability | Planned |

Do not expand into unrelated defect modes until Phase 1 narrative is complete.
