# Cover Glass Process Map (Simulated)

> **Note:** This document describes a **simulated** high-volume cover glass production flow for portfolio and interview use. It does not represent confidential supplier or customer data.

## Overview

This project models a typical cover glass line for mobile or tablet applications. The primary quality story is **increased edge chipping and dimension variation** observed after CNC contouring / chamfering. Other process steps provide context, downstream CTQ checks, and traceability—but **Phase 1 analysis focuses on CNC and edge chipping**.

## Process Flow

```text
Incoming Glass Inspection
        ↓
Cutting / Laser Cutting
        ↓
CNC Contour / Drilling / Chamfering   ← Phase 1 focus
        ↓
Edge Polishing
        ↓
Cleaning
        ↓
Chemical Strengthening (Ion Exchange)
        ↓
Coating / Printing (optional)
        ↓
AOI Inspection
        ↓
OQC
        ↓
ORT / Reliability Testing
```

---

## Process Steps

### 1. Incoming Glass Inspection

**What happens:** Raw glass sheets or pre-cut blanks are received and inspected for surface quality, thickness uniformity, and batch traceability before entering production.

**Typical defects:** Scratches, bubbles, inclusions, thickness out-of-spec, edge damage from handling.

**MQE focus:** Verify incoming material control, batch linkage (`Raw_Glass_Batch`), and whether upstream glass variation contributes to downstream CNC or strengthening issues.

**Phase 1 relevance:** Supporting context only—not the primary defect mode.

---

### 2. Cutting / Laser Cutting

**What happens:** Glass is cut to near-net shape using mechanical scribe-and-break, wheel cutting, or laser cutting depending on product geometry.

**Typical defects:** Micro-cracks at cut edge, edge chip-out, dimensional oversize/undersize, kerf inconsistency.

**MQE focus:** Cut edge quality affects CNC tool load and chipping risk. Track `Line_ID`, `Machine_ID`, and cut-to-CNC cycle time.

**Phase 1 relevance:** Secondary stratification factor if cut edge quality correlates with CNC chipping.

---

### 3. CNC Contour / Drilling / Chamfering ⭐ Primary Focus

**What happens:** CNC machines perform contour milling, hole drilling, and chamfering to final edge geometry. Coolant is applied for thermal control and chip evacuation. Tools and fixtures wear over time.

**Typical defects:** **Edge chipping**, chamfer width variation, oversize/undersize features, burrs, drill breakout, tool mark defects.

**MQE focus (Phase 1):**
- **Tool wear** (`Tool_ID`, tool life counter)
- **Coolant pressure** and flow stability
- **Fixture effects** (`Fixture_ID`, clamping repeatability)
- **Machine-to-machine variation** (`Machine_ID`)
- **Shift / operator effects** (`Shift`, `Operator_ID`)
- **Traceability** from glass ID through lot, machine, tool, and time window

This step is where the main project story begins: elevated chipping and chamfer variation trigger SPC alerts, Pareto review, and root cause stratification.

---

### 4. Edge Polishing

**What happens:** Chamfered edges may be fine-polished to reduce roughness and improve cosmetic and strength performance.

**Typical defects:** Under-polish (visible tool marks), over-polish (chamfer width drift), edge chip re-exposure, contamination.

**MQE focus:** Confirm whether CNC chipping is masked or worsened by polishing. Secondary CTQ: chamfer width after polish.

**Phase 1 relevance:** Downstream effect on chamfer CTQ; not the primary root cause layer.

---

### 5. Cleaning

**What happens:** Parts are washed to remove coolant, polishing slurry, and particulates before strengthening or coating.

**Typical defects:** Residual contamination, water spots, particle re-deposition, handling nick.

**MQE focus:** Cleaning rarely drives CNC chipping but can affect coating and AOI yield. Track as a confounding factor in traceability.

**Phase 1 relevance:** Low priority for initial analysis.

---

### 6. Chemical Strengthening (Ion Exchange)

**What happens:** Glass is immersed in a molten salt bath (typically KNO₃) to create a compressive stress (CS) layer and depth of layer (DOL) via ion exchange.

**Typical defects:** Low CS/DOL, warpage increase, haze, bath contamination effects, thermal shock crack.

**MQE focus:** CS and DOL are critical CTQs. Edge chips from CNC can become crack initiation sites during strengthening or drop test.

**Phase 1 relevance:** Downstream CTQ monitoring; link edge defects to ORT risk in later phases.

---

### 7. Coating / Printing (Optional)

**What happens:** Anti-fingerprint, anti-reflective, or decorative coatings may be applied; some products include ink printing.

**Typical defects:** Coating voids, haze increase, contact angle drift, print misregistration.

**MQE focus:** Cosmetic and functional CTQs (`Haze`, `Contact_Angle`). Not central to the CNC chipping story in Phase 1.

**Phase 1 relevance:** Included in dataset for completeness; minimal analysis depth initially.

---

### 8. AOI Inspection

**What happens:** Automated optical inspection scans for edge chips, scratches, stains, and dimensional anomalies.

**Typical defects:** Edge chip (AOI-detected), scratch, stain, particle, dimensional fail.

**MQE focus:** AOI provides **defect signature** and location (`Defect_Type`, `Defect_Location`). Compare AOI results to inline CNC-era measurements for traceability closure.

**Phase 1 relevance:** Primary defect detection gate; feeds Pareto and heatmap analysis.

---

### 9. OQC (Outgoing Quality Control)

**What happens:** Final sampling or 100% check for critical CTQs before shipment: thickness, warpage, cosmetic grade, and spot-check dimensional verification.

**Typical defects:** Mixed defect modes from any upstream step; lot-level hold conditions.

**MQE focus:** `Final_Result` and lot disposition. Confirm containment effectiveness after corrective actions.

**Phase 1 relevance:** Yield summary and validation of improvement actions.

---

### 10. ORT / Reliability Testing

**What happens:** Sampled units undergo drop test, thermal cycling, abrasion, or chemical resistance per product specification.

**Typical defects:** Edge-initiated fracture, CS/DOL marginal failures, coating delamination.

**MQE focus:** Links edge quality to field reliability. Used in interview narrative to show **preventive control** rationale—not primary dataset focus in Phase 1.

**Phase 1 relevance:** Referenced in recommendations; limited rows in synthetic dataset.

---

## Phase 1 Scope Summary

| Area | Priority |
|------|----------|
| CNC edge chipping | **Primary** |
| Chamfer width variation | **Primary** |
| Tool wear, coolant, fixture, machine, shift | **Primary** |
| Traceability (Glass → Lot → Machine → Tool) | **Primary** |
| AOI / OQC yield impact | **Secondary** |
| CS / DOL / warpage | **Monitor** |
| Coating / haze / contact angle | **Deferred** |
| ORT failures | **Narrative only** |

## Intended Analysis Entry Point

When yield drops or SPC signals fire on `Chipping_Size_um` or `Chamfer_Width_mm`, the MQE workflow starts at **CNC traceability stratification**, not at unrelated downstream defect modes.
