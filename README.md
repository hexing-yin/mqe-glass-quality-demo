# Cover Glass Manufacturing Quality Analytics

Simulated manufacturing quality analytics for a high-volume cover glass production line. This portfolio project demonstrates structured MQE problem solving—traceability, Pareto analysis, SPC, process capability, root cause stratification, and ML risk screening—using **synthetic data only**. It does not represent, and should not be read as, access to confidential data from Apple, Lens Technology, Corning, or any supplier.

---

## Manufacturing Problem

A cover glass line shows increased **edge chipping** and **chamfer width variation** after CNC contouring. AOI yield has dropped. The investigation asks: which machines, fixtures, tool-life windows, and coolant conditions drive the defect spike, and what preventive controls would an MQE recommend?

Phase 1 focus: **CNC-related edge chipping**—tool wear, coolant pressure stability, fixture effects, machine variation, and shift effects.

---

## Why This Matters for MQE / Brittle Materials

Cover glass is a brittle, high-volume precision process. Small shifts in tool wear or coolant delivery can produce edge-initiated defects that propagate through AOI, OQC, and reliability testing. This project mirrors how an MQE would work a real yield excursion:

- Confirm the **defect signature** before chasing noise
- Use **traceability** to localize the problem
- Apply **SPC and capability** to separate special cause from spec margin
- Stratify by **process physics** (tool life × coolant, machine, fixture)
- Use **ML for risk ranking / screening** (process inputs only), not automatic process control

---
## AI-Assisted Development Workflow

This project was developed using an AI-assisted engineering workflow. ChatGPT was used for project planning, MQE storyline development, statistical logic review, and interview-oriented explanation. Cursor was used as an AI-assisted IDE for Python implementation, debugging, refactoring, and project organization. Claude Code was used for larger multi-file edits, pipeline updates, and documentation improvements.

All key engineering decisions were reviewed and finalized manually, including the synthetic manufacturing scenario, traceability structure, statistical assumptions, SPC and capability methods, ML leakage-control decisions, and final MQE interpretation. AI tools were used to accelerate implementation, but the project logic, validation, and engineering conclusions were owned and checked by the author.

---

## JMP Interactive Review Layer

In addition to the reproducible Python pipeline, this project includes a JMP interactive review layer. The full 50,000-row synthetic unit-level dataset was imported into JMP and saved as a JMP data table under `outputs/jmp/`.

The JMP layer was used to create interactive review plots for:

- Chamfer-width CTQ distribution
- Tool-life × coolant-stability stratification for edge-chipping risk
- Edge-chipping p-chart / out-of-control subgroup review

This reflects a practical MQE workflow: Python is used for reproducible batch analytics, while JMP is used for interactive engineering review, quick filtering, visual confirmation, and live discussion with cross-functional teams.

Python remains the source of truth for data generation and reproducible calculations. JMP is used as an interactive review and visualization layer.

---

## Project Workflow

| Step | Module | Purpose |
|------|--------|---------|
| 1 | [`src/generate_data.py`](src/generate_data.py) | Generate 50,000 synthetic unit-level records with embedded special causes |
| 2 | [`src/validate_data.py`](src/validate_data.py) | Validate schema, ranges, and Phase 1 story assumptions |
| 3 | [`src/pareto.py`](src/pareto.py) | Rank NG defect modes; confirm Edge_Chipping dominance |
| 4 | [`src/stratify.py`](src/stratify.py) | Root cause stratification by machine, fixture, shift, tool life, coolant |
| 5 | [`src/spc.py`](src/spc.py) | X-bar/R (chamfer), I-MR (exploratory), and p-chart (Edge_Chipping rate) on CNC-04 |
| 6 | [`src/capability.py`](src/capability.py) | Cp/Cpk (within-subgroup) and Pp/Ppk (overall) for chamfer width |
| 7 | [`src/heatmap.py`](src/heatmap.py) | Edge_Chipping location patterns by machine and defect site |
| 8 | [`src/ml_risk.py`](src/ml_risk.py) | Pre-process ML risk ranking (process + traceability inputs only) |
| 9 | [`src/export_jmp.py`](src/export_jmp.py) | Export workbook for JMP import and live-demo analysis |

Planning documents: [`docs/process_map.md`](docs/process_map.md) · [`docs/analysis_plan.md`](docs/analysis_plan.md) · [`docs/data_dictionary.md`](docs/data_dictionary.md)

---

## Key Findings (Simulated Data)

| Metric | Result |
|--------|--------|
| Dataset size | 50,000 synthetic units |
| Overall NG rate | 3.85% |
| Dominant NG mode | Edge_Chipping — **80.95%** of NG parts |
| Highest-risk process window | High tool life + unstable coolant |
| Critical tool life + unstable coolant | **61.52%** actual Edge_Chipping rate |
| Low-risk baseline Cpk (chamfer) | **1.404** (within-subgroup; tool life < 75%, stable coolant) |
| High wear + unstable Cpk | **1.181** (within-subgroup; mean shift toward USL) |
| ML screening (no CTQ leakage) | ROC-AUC ~0.95; PR-AUC ~0.40; top inputs: `Tool_Life_Pct`, `Coolant_Pressure_Stability`, `Coolant_Pressure_bar` |

High-risk machines (`CNC-04`, `CNC-06`) and fixtures (`FIX-B2`, `FIX-C1`) show elevated chipping. Edge location dominates defect maps; corners and feature cutouts (camera hole, speaker slot) are secondary clusters.

ML ranks high-risk process windows using pre-inspection inputs only. It is a screening aid — not a production control system — and default 0.5 classification thresholds are suboptimal for rare defects; use predicted probabilities and PR-AUC instead.

---

## Repository Structure

```text
mqe-glass-quality-demo/
├── data/raw/
│   └── cover_glass_synthetic.csv   # 50k-row Phase 1 dataset (synthetic)
├── data/processed/            # Reserved for future derived datasets
├── docs/                      # Process map, CTQ matrix, data dictionary, analysis plan
├── outputs/
│   ├── figures/               # Python-generated Pareto, SPC, capability, heatmap, ML charts
│   ├── reports/               # CSV summaries and JMP export workbook
│   └── jmp/                   # JMP data table and JMP-generated review figures
├── src/                       # Analysis modules (see workflow above)
├── pyproject.toml
└── README.md
```

---

## How to Run

**Requirements:** Python 3.12+, [`uv`](https://docs.astral.sh/uv/)

```bash
uv sync

# One-command full pipeline
uv run python main.py

# Or run modules individually (step-by-step)
uv run python src/generate_data.py
uv run python src/validate_data.py
uv run python src/pareto.py
uv run python src/stratify.py
uv run python src/spc.py
uv run python src/capability.py
uv run python src/heatmap.py
uv run python src/ml_risk.py
uv run python src/export_jmp.py
```

`main.py` runs all steps in order and stops if any step fails. Individual scripts can be re-run after `generate_data.py` when you only need one analysis.

---

## Outputs

### Reports

| File | Description |
|------|-------------|
| [`outputs/reports/defect_pareto.csv`](outputs/reports/defect_pareto.csv) | NG defect Pareto table |
| [`outputs/reports/chipping_stratification_summary.csv`](outputs/reports/chipping_stratification_summary.csv) | Root cause stratification |
| [`outputs/reports/spc_chamfer_xbar_r_summary.csv`](outputs/reports/spc_chamfer_xbar_r_summary.csv) | Chamfer X-bar/R subgroups |
| [`outputs/reports/spc_chipping_imr_summary.csv`](outputs/reports/spc_chipping_imr_summary.csv) | Chipping I-MR values |
| [`outputs/reports/spc_chipping_p_chart_summary.csv`](outputs/reports/spc_chipping_p_chart_summary.csv) | Edge_Chipping p-chart subgroups |
| [`outputs/reports/capability_summary.csv`](outputs/reports/capability_summary.csv) | Process capability by group |
| [`outputs/reports/defect_location_summary.csv`](outputs/reports/defect_location_summary.csv) | Defect location summary |
| [`outputs/reports/ml_risk_model_summary.csv`](outputs/reports/ml_risk_model_summary.csv) | ML model comparison |
| [`outputs/reports/high_risk_windows.csv`](outputs/reports/high_risk_windows.csv) | High-risk process windows |
| [`outputs/reports/jmp_export_cover_glass_quality.xlsx`](outputs/reports/jmp_export_cover_glass_quality.xlsx) | JMP import workbook |

### Figures

| File | Description |
|------|-------------|
| [`outputs/figures/defect_pareto.png`](outputs/figures/defect_pareto.png) | Defect Pareto chart |
| [`outputs/figures/chamfer_xbar_r_chart.png`](outputs/figures/chamfer_xbar_r_chart.png) | Chamfer X-bar/R chart |
| [`outputs/figures/chipping_imr_chart.png`](outputs/figures/chipping_imr_chart.png) | Chipping I-MR chart (exploratory) |
| [`outputs/figures/spc_chipping_p_chart.png`](outputs/figures/spc_chipping_p_chart.png) | Edge_Chipping p-chart |
| [`outputs/figures/chamfer_capability_distribution.png`](outputs/figures/chamfer_capability_distribution.png) | Capability distribution comparison |
| [`outputs/figures/chipping_location_heatmap.png`](outputs/figures/chipping_location_heatmap.png) | Machine × location heatmap |
| [`outputs/figures/ml_feature_importance.png`](outputs/figures/ml_feature_importance.png) | ML feature importance |

### JMP Interactive Review Artifacts

| File | Description |
|------|-------------|
| [`outputs/jmp/cover_glass_units.jmp`](outputs/jmp/cover_glass_units.jmp) | JMP data table imported from the full 50,000-row synthetic unit-level dataset |
| [`outputs/jmp/figures/jmp_chamfer_distribution.png`](outputs/jmp/figures/jmp_chamfer_distribution.png) | JMP CTQ distribution review for chamfer width |
| [`outputs/jmp/figures/jmp_tool_life_coolant_stratification.png`](outputs/jmp/figures/jmp_tool_life_coolant_stratification.png) | JMP Graph Builder view of tool-life × coolant-stability edge-chipping risk |
| [`outputs/jmp/figures/jmp_edge_chipping_ooc_highlight.png`](outputs/jmp/figures/jmp_edge_chipping_ooc_highlight.png) | JMP review of out-of-control edge-chipping subgroups |
| [`outputs/jmp/figures/jmp_edge_chipping_p_chart_full.png`](outputs/jmp/figures/jmp_edge_chipping_p_chart_full.png) | JMP p-chart view with center line and control limits |

---

## Interview Positioning

Use this narrative when presenting the project:

```text
Defect signature
  → Traceability (where / when / who)
    → SPC (special cause?)
      → Capability (spec margin?)
        → Root cause (tool, coolant, fixture, machine, shift)
          → Containment (lot hold, sorting)
            → Corrective action (fix the cause)
              → Preventive control (SPC alerts, tool life stop, coolant interlock)
                → Yield improvement (measurable recovery)
```

**Python** handles reproducible data generation, batch analysis, SPC/capability calculations, and ML screening. **JMP** supports interactive engineering review during live demo. The full 50,000-row synthetic dataset was imported into JMP and saved as [`outputs/jmp/cover_glass_units.jmp`](outputs/jmp/cover_glass_units.jmp), with JMP-generated review figures under [`outputs/jmp/figures/`](outputs/jmp/figures/). A Streamlit dashboard is **not implemented** (optional Phase 2).

---

## Disclaimer

**All data in this repository is synthetic and simulated.** It is designed to be physically reasonable for cover glass manufacturing but does not represent real production data from Apple, Lens Technology, Corning, or any supplier. This project demonstrates analytical methodology and MQE thinking for portfolio and interview purposes only.
