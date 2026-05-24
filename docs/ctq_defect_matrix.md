# CTQ and Defect Matrix (Simulated Cover Glass)

> **Note:** Simulated manufacturing context for MQE portfolio and interview preparation. Values and limits are illustrative, not proprietary specifications.

## Purpose

This matrix links process steps to Critical-to-Quality characteristics (CTQs), common defects, likely root causes, measurement methods, and planned analysis methods. It supports structured root cause thinking during interviews.

**Phase 1 emphasis:** CNC chamfering and edge chipping rows are the primary investigation path.

---

## CTQ / Defect Matrix

| Process Step | CTQ | Common Defects | Possible Root Causes | Measurement Method | Analysis Method |
|--------------|-----|----------------|----------------------|--------------------|-----------------|
| Incoming Glass Inspection | Thickness | Thickness OOS, edge chip from handling | Supplier batch variation, storage/handling damage | Contact or optical thickness gauge | SPC on thickness; batch Pareto |
| Incoming Glass Inspection | Warpage | Bow / twist | Raw glass stress, storage orientation | Flatness plate / laser scan | Capability vs. flatness spec |
| Cutting / Laser Cutting | Thickness (edge zone) | Micro-crack, edge chip-out | Cut speed, laser power drift, dull wheel | Microscope + dimensional check | Stratify by cut machine; time-series SPC |
| Cutting / Laser Cutting | Chamfer Width (pre-CNC) | Oversize blank, kerf inconsistency | Fixture drift, program offset error | CMM / vision | Traceability to CNC incoming edge state |
| **CNC Contour / Chamfering** | **Chamfer Width** | **Chamfer too wide / narrow** | **Tool wear, coolant pressure low, fixture misalignment, program offset, machine spindle runout** | **Inline vision or CMM** | **SPC (X-bar/R), capability (Cp/Cpk), heatmap by Machine × Shift** |
| **CNC Contour / Chamfering** | **Chipping Size** | **Edge chip, burr, breakout** | **Worn tool, insufficient coolant, high feed rate, glass edge pre-damage, fixture vibration, operator setup error** | **Microscope / AOI (μm scale)** | **Pareto by defect type, root cause stratification (Tool, Machine, Shift), ML risk score** |
| CNC Contour / Chamfering | Thickness (local) | Feature oversize / undersize | Tool path error, thermal expansion, fixturing slip | CMM | Capability study; correlation with chipping |
| Edge Polishing | Chamfer Width | Under/over polish | Polish time, wheel wear, incoming chamfer variation | Vision / CMM | Before/after comparison; secondary SPC |
| Edge Polishing | Chipping Size | Re-exposed chip | Incoming CNC chip not removed, aggressive polish | Microscope / AOI | Trace back to CNC tool window |
| Cleaning | AOI Result (cosmetic) | Stain, particle | Incomplete rinse, dirty bath, handling | Visual / particle counter | Low priority Pareto in Phase 1 |
| Chemical Strengthening | CS (Compressive Stress) | Low CS | Bath chemistry drift, time/temperature OOS, edge damage accelerating exchange | Fragmentation or stress-optical method | SPC on CS; correlation with edge defects |
| Chemical Strengthening | DOL (Depth of Layer) | Low DOL | Bath age, immersion time, glass composition | Same as CS | Capability vs. spec; joint CS–DOL review |
| Chemical Strengthening | Warpage | Increased bow | Ion exchange stress imbalance, thin regions | Flatness scan | Regression vs. thickness and edge quality |
| Chemical Strengthening | Haze | Visible haze | Bath contamination, incomplete clean | Haze meter | Monitor only in Phase 1 |
| Coating / Printing | Haze | Coating haze | Coating thickness, cure profile | Haze meter | Deferred analysis |
| Coating / Printing | Contact Angle | Low hydrophobicity | Contamination, cure OOS | Goniometer | Deferred analysis |
| AOI Inspection | AOI Result | Edge chip, scratch, stain | Upstream CNC, handling, coating | Automated optical scanner | **Pareto of defect types; heatmap by Machine × Defect_Location** |
| AOI Inspection | Chipping Size | Edge chip (AOI-detected) | CNC tool wear window, fixture, coolant | AOI + microscope confirm | Link AOI fail to CNC traceability fields |
| AOI Inspection | Defect Location | Edge vs. corner vs. feature | Tool path, fixture, part orientation | AOI defect map | Defect location heatmap |
| OQC | Final Result | Mixed fail modes | Any upstream out-of-control condition | Sampling + CTQ checks | Yield trend; lot hold analysis |
| OQC | Thickness | Thickness OOS | Global process drift | Gauge R&R validated gauge | Capability summary |
| OQC | Warpage | Flatness fail | Strengthening + handling | Flatness scan | Secondary capability |
| ORT / Reliability | Final Result (ORT fail) | Edge-initiated fracture | Edge chip + low CS/DOL margin | Drop / thermal / abrasion test | Failure mode linkage narrative (limited N) |

---

## Phase 1 Investigation Priority

When investigating the **edge chipping spike**, work the matrix in this order:

1. **Pareto** on `Defect_Type` and `AOI_Result` — confirm edge chip dominance
2. **Traceability** — stratify `Chipping_Size_um` and `Chamfer_Width_mm` by `Machine_ID`, `Tool_ID`, `Fixture_ID`, `Shift`
3. **SPC** — control charts on chamfer and chipping; check for special cause vs. common cause
4. **Capability** — Cp/Cpk for chamfer width against spec limits
5. **Heatmap** — Machine × Shift (or Tool × Shift) defect rate
6. **Root cause hypothesis** — tool wear + coolant pressure interaction, fixture B bias, night shift setup drift
7. **ML risk (supporting)** — flag high-risk process windows; validate with engineering judgment

---

## Key CTQ Specifications (Illustrative)

These are **simulated** spec limits for data generation and capability analysis—not real product drawings.

| CTQ | Unit | Typical Target | Spec Range (illustrative) |
|-----|------|----------------|---------------------------|
| Chamfer Width | mm | 0.30 | 0.25 – 0.35 |
| Chipping Size | μm | ≤ 50 | Fail if > 80 |
| Thickness | mm | 0.55 | 0.53 – 0.57 |
| Warpage | mm | ≤ 0.05 | Fail if > 0.10 |
| CS | MPa | ≥ 750 | Fail if < 700 |
| DOL | μm | ≥ 40 | Fail if < 35 |
| Haze | % | ≤ 0.5 | Informational in Phase 1 |
| Contact Angle | ° | ≥ 110 | Informational in Phase 1 |
| AOI Result | pass/fail | Pass | Fail on any critical defect |

---

## Interview Talking Points

- **CTQ vs. defect:** CTQs are measurable outputs; defects are failure modes against those CTQs.
- **CNC chipping is often multi-factor:** Tool wear alone rarely explains a spike—look for coolant, fixture, and shift interaction.
- **AOI closes the loop:** Inline CNC measurements plus AOI defect location confirm whether the problem is edge-specific or feature-specific.
- **Do not over-index on ML:** Use risk scoring to prioritize review windows; confirm with traceability and SPC.
