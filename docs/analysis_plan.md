# Analysis Plan — Cover Glass Quality (Simulated)

> **Note:** This plan covers a portfolio-style MQE investigation using **synthetic data only**. ML supports the story; it is not the headline.

## Problem Statement

A high-volume cover glass line shows **increased edge chipping and chamfer width variation** after CNC contouring. Yield at AOI/OQC has dipped. The goal is to identify high-risk process windows, confirm root causes with data, and recommend preventive controls.

---

## Analysis Workflow Overview

```text
1. Defect signature (Pareto + yield trend)
        ↓
2. Traceability stratification (Machine, Tool, Fixture, Shift)
        ↓
3. SPC — special vs. common cause
        ↓
4. Process capability (Cp/Cpk)
        ↓
5. Defect heatmap (Machine × Shift, location map)
        ↓
6. Root cause hypothesis + confirmation
        ↓
7. ML risk prediction (supporting)
        ↓
8. Containment → Corrective → Preventive recommendations
        ↓
9. JMP deep-dive (optional confirmatory analysis)
```

---

## Step-by-Step Plan

### Step 1 — Defect Signature (Pareto)

**Objective:** Confirm edge chip is the dominant fail mode and quantify yield impact.

**Inputs:** `Defect_Type`, `Defect_Count`, `AOI_Result`, `Final_Result`, `Process_Time`

**Python (`src/pareto.py`):**
- Pareto chart of defect types (count and cumulative %)
- Weekly yield trend
- Export summary CSV and figure to `outputs/figures/`

**JMP:**
- Interactive Pareto with filtering by `Product_Model` and date range
- Quick what-if: exclude one defect type to see residual yield

---

### Step 2 — Traceability Stratification

**Objective:** Narrow the problem to specific machines, tools, fixtures, or shifts.

**Inputs:** `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`, `Operator_ID`, `Chipping_Size_um`, `Chamfer_Width_mm`

**Python:**
- Box plots / summary tables: median chipping and chamfer by stratification factor
- Fail rate by `Machine_ID × Tool_ID`
- Identify top 3 high-risk combinations

**JMP:**
- Graph Builder: `Chipping_Size_um` Y vs. `Machine_ID` X, color by `Shift`
- Tabulate mean fail rate by `Fixture_ID`

---

### Step 3 — SPC Control Charts

**Objective:** Detect special cause signals on key CTQs; distinguish drift from step change.

**Inputs:** `Chamfer_Width_mm`, `Chipping_Size_um`, `Process_Time`, subgroup by `Machine_ID` or daily lot

**Python (`src/spc.py`):**
- X-bar / R (or I-MR for individual measurements) on chamfer width
- Individual chart on chipping size (or defect rate p-chart by shift)
- Highlight points outside control limits or Nelson rules (simplified)
- Figures saved to `outputs/figures/`

**JMP:**
- Control Chart Builder with automatic rule tagging
- Compare Phase I (baseline) vs. Phase II (after corrective action — simulated second period if added later)

---

### Step 4 — Process Capability

**Objective:** Quantify whether the process meets chamfer and thickness specifications.

**Inputs:** `Chamfer_Width_mm`, `Thickness_mm`, spec limits (from CTQ matrix)

**Python (`src/capability.py`):**
- Cp, Cpk, Pp, Ppk for chamfer width
- Capability histogram with spec lines
- Report table to `outputs/reports/`

**JMP:**
- Process Capability platform with normal fit and spec limit editor
- Compare capability before vs. after filtering to best machine only

---

### Step 5 — Defect Heatmap

**Objective:** Visualize spatial and organizational patterns of defects.

**Inputs:** `Machine_ID`, `Shift`, `Defect_Type`, `Defect_Location`, `Tool_ID`

**Python (`src/heatmap.py`):**
- 2D heatmap: fail rate by Machine × Shift
- Defect location breakdown (edge long side, corner, hole perimeter)
- Optional: Tool wear bin × chipping fail rate

**JMP:**
- Heatmap via Tabulate + Graph Builder contingency plots

---

### Step 6 — Root Cause Stratification

**Objective:** Form and test hypotheses aligned with CNC physics using descriptive, engineering-focused summaries—not predictive modeling.

**Hypotheses to test (simulated ground truth expected in data):**
1. **Tool wear:** `Tool_Life_Pct` ≥ 75% correlates with higher `Chipping_Size_um`
2. **Coolant pressure:** Low `Coolant_Pressure_bar` on `Shift` = Night
3. **Fixture effect:** `Fixture_ID` = FIX-B2 shows chamfer width bias
4. **Machine variation:** `Machine_ID` = CNC-04 elevated edge chip rate vs. fleet median
5. **Interaction:** High `Tool_Life_Pct` + low `Coolant_Pressure_bar` → disproportionate chipping

**Python:**
- Grouped fail rate summaries by `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`
- Box plots of `Chipping_Size_um` and `Chamfer_Width_mm` by those factors
- Stratified Pareto of `Defect_Type` within top suspect machines or shifts
- Summaries by `Tool_Wear_Bin` (≥ 75% vs. below) and `Coolant_Pressure_bar` quartile
- Cross-tabs: `Machine_ID × Shift`, `Tool_ID × Tool_Wear_Bin`, `Fixture_ID × Chamfer_Width_mm` mean
- Document findings in `outputs/reports/root_cause_summary.md`

**JMP (manual live demo — see Step 8):**
- Graph Builder: compare `Chipping_Size_um` across `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`
- Tabulate fail rates by `Tool_Wear_Bin` and coolant pressure quartile

---

### Step 7 — Simple ML Risk Prediction (Supporting)

**Objective:** Flag high-risk process windows for preventive review—not to replace engineering judgment. This is the **only** step that uses logistic regression or other ML models.

**Inputs:** `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`, `Tool_Life_Pct`, `Coolant_Pressure_bar`, `Spindle_Speed_rpm`, `Feed_Rate_mm_min` → target `Chipping_Fail` or high `Chipping_Size_um`

**Python (`src/ml_risk.py`):**
- Train/test split with fixed seed
- Model: logistic regression or random forest (interpretable feature importance)
- Example formula: `Chipping_Fail ~ Tool_Life_Pct + Coolant_Pressure_bar + Machine_ID + Tool_ID + Fixture_ID + Shift + Spindle_Speed_rpm + Feed_Rate_mm_min`
- Output: `Risk_Score` per unit, precision/recall at useful threshold
- Feature importance bar chart

**Scope limits:**
- No deep learning
- No claim of production deployment
- Present as "prioritization aid" in interview narrative

**JMP (manual live demo — see Step 8):**
- Optional score validation: overlay `Risk_Score` on Graph Builder using exported data

---

### Step 8 — JMP Export Workflow

**Objective:** Enable confirmatory analysis and interview demo in JMP.

**Python:**
- Export analysis-ready dataset to `outputs/reports/cover_glass_jmp_export.xlsx` or CSV (via `openpyxl` / pandas)
- Include data dictionary sheet and spec limits sheet
- Column types formatted for JMP import

**JMP (manual / live demo only):**
- Import the exported CSV or Excel file; all JMP work is done interactively during interview prep or live demo
- No JMP scripts are generated from Python—JMP complements the reproducible Python pipeline, not replaces it
- Typical platforms: Control Chart Builder, Process Capability, Fit Model, Graph Builder, Partition

---

### Step 9 — Recommendations and Yield Improvement Narrative

**Containment (immediate):**
- Hold lots from high-risk `Machine_ID + Tool_ID` window
- Increase sampling at AOI for affected shift

**Corrective action:**
- Replace/worn tools above life limit
- Restore coolant pressure setpoint on Night shift
- Re-qualify `FIX-B2`; adjust chamfer offset

**Preventive control:**
- SPC alerts on chamfer width with auto-stop rule
- Tool life hard stop at 75% (aligned with elevated chipping risk threshold)
- Coolant pressure interlock log
- ML risk score dashboard (future Streamlit phase) for engineering review queue

**Expected yield improvement (simulated):**
- Document projected fail rate reduction after actions in report appendix

---

## Python vs. JMP Division of Labor

| Activity | Python | JMP |
|----------|--------|-----|
| Data generation & validation | ✅ Primary | — |
| Automated batch charts & reports | ✅ Primary | — |
| Pareto, SPC, capability scripts | ✅ Primary | — |
| Root cause stratification (descriptive) | ✅ Primary | — |
| ML risk model training | ✅ Primary | — |
| Data export for JMP | ✅ Primary (CSV/Excel) | — |
| Interactive confirmatory analysis | — | ✅ Manual live demo only |
| Effect screening & interactions | — | ✅ Manual (Fit Model, Partition) |
| Interview demo | Notebooks + Streamlit (later) | Live walkthrough on imported export |
| Reproducible pipeline | ✅ Primary | Not scripted from Python |

---

## Planned Code Modules (Future — Not in Scope Yet)

| Module | Output |
|--------|--------|
| `src/generate_data.py` | 50k-row synthetic CSV |
| `src/validate_data.py` | Schema and range checks |
| `src/pareto.py` | Pareto chart + yield trend |
| `src/spc.py` | Control charts |
| `src/capability.py` | Cp/Cpk report |
| `src/heatmap.py` | Machine × Shift heatmap |
| `src/ml_risk.py` | Risk score model |
| `app/app.py` | Streamlit dashboard (later phase) |

---

## Interview Positioning Flow

Use this sequence when presenting the project:

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

**Key message:** Data science (ML) enters **after** engineering traceability and SPC confirm the problem is real and localized—not before.

---

## Phase Boundaries

| Phase | Scope |
|-------|-------|
| **Phase 1 (current plan)** | CNC chipping, chamfer, traceability, AOI yield |
| Phase 2 | CS/DOL correlation with edge defects; strengthening SPC |
| Phase 3 | Coating CTQs, ORT sampling analysis |
| Phase 4 | Streamlit app and live demo polish |

Do not expand into unrelated defect modes until Phase 1 narrative is complete.
