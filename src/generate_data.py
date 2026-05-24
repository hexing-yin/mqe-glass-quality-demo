"""
Synthetic cover glass manufacturing quality dataset generator.

All data produced by this script is SIMULATED for portfolio and interview use.
It does not represent real production data from any company or supplier.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# --- Configuration ---
RANDOM_SEED = 42
ROW_COUNT = 50_000

# Simulated CTQ limits (illustrative, not proprietary specs)
CHAMFER_TARGET_MM = 0.30
CHAMFER_LSL_MM = 0.25
CHAMFER_USL_MM = 0.35
CHIPPING_FAIL_UM = 80.0
THICKNESS_TARGET_MM = 0.70
THICKNESS_LSL_MM = 0.68
THICKNESS_USL_MM = 0.72
WARPAGE_FAIL_MM = 0.08
CS_FAIL_MPA = 700.0
DOL_FAIL_UM = 35.0

# Tool wear threshold where chipping risk begins to rise
TOOL_WEAR_RISK_PCT = 75.0

# Machines and fixtures with slightly elevated risk (for traceability demos)
HIGH_RISK_MACHINES = {"CNC-04", "CNC-06"}
HIGH_RISK_FIXTURES = {"FIX-B2", "FIX-C1"}
CHAMFER_BIAS_FIXTURES = {"FIX-B2"}  # tends to run wide on chamfer

PRODUCT_MODELS = ["CG-Model-A", "CG-Model-B", "CG-Model-C"]
LINE_IDS = ["LINE-01", "LINE-02"]
MACHINE_IDS = [f"CNC-{i:02d}" for i in range(1, 7)]
TOOL_IDS = [f"TOOL-{i:02d}" for i in range(1, 25)]
FIXTURE_IDS = [f"FIX-{letter}{num}" for letter in "ABC" for num in range(1, 4)]
OPERATOR_IDS = [f"OP-{i:03d}" for i in range(1, 31)]
SHIFTS = ["Day", "Swing", "Night"]

DEFECT_TYPES = [
    "Edge_Chipping",
    "Dimension_OOS",
    "Scratch",
    "Particle",
    "Warpage_OOS",
    "Strengthening_OOS",
    "None",
]
DEFECT_LOCATIONS = [
    "Edge",
    "Corner",
    "Camera_Hole",
    "Speaker_Slot",
    "Surface",
    "Full_Part",
    "None",
]

# Map defect type -> typical location (used when assigning defects)
DEFECT_LOCATION_MAP = {
    "Edge_Chipping": "Edge",
    "Dimension_OOS": "Full_Part",
    "Scratch": "Surface",
    "Particle": "Surface",
    "Warpage_OOS": "Full_Part",
    "Strengthening_OOS": "Full_Part",
    "None": "None",
}


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def generate_traceability(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Create lot, machine, tool, fixture, operator, and timestamp fields."""
    # Spread production over ~8 weeks starting Feb 2026
    start = pd.Timestamp("2026-02-01")
    end = pd.Timestamp("2026-03-31")
    process_seconds = rng.integers(0, int((end - start).total_seconds()), size=n)
    process_time = start + pd.to_timedelta(process_seconds, unit="s")

    # Lot IDs change roughly every few days
    lot_index = process_seconds // (3 * 24 * 3600)
    lot_ids = [f"LOT-2026-W{(i % 8) + 6:02d}-{'ABCD'[i % 4]}" for i in lot_index]

    return pd.DataFrame(
        {
            "Glass_ID": [f"GLS-2026-{i + 1:07d}" for i in range(n)],
            "Lot_ID": lot_ids,
            "Product_Model": rng.choice(PRODUCT_MODELS, size=n, p=[0.4, 0.4, 0.2]),
            "Raw_Glass_Batch": [f"RGB-{rng.integers(8000, 9999)}" for _ in range(n)],
            "Line_ID": rng.choice(LINE_IDS, size=n, p=[0.55, 0.45]),
            "Machine_ID": rng.choice(MACHINE_IDS, size=n),
            "Tool_ID": rng.choice(TOOL_IDS, size=n),
            "Fixture_ID": rng.choice(FIXTURE_IDS, size=n),
            "Operator_ID": rng.choice(OPERATOR_IDS, size=n),
            "Shift": rng.choice(SHIFTS, size=n, p=[0.45, 0.30, 0.25]),
            "Process_Time": process_time,
            "Inspection_Station": "AOI",
        }
    )


def generate_cnc_process(trace: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Simulate CNC process parameters with shift and machine effects."""
    n = len(trace)
    shift = trace["Shift"].to_numpy()
    machine = trace["Machine_ID"].to_numpy()

    # Tool life: most tools mid-life, some near end of life
    tool_life = rng.beta(a=2.5, b=2.0, size=n) * 100.0
    tool_life = np.clip(tool_life, 5.0, 98.0)

    spindle = rng.normal(24000, 300, size=n).astype(int)
    feed = rng.normal(850, 40, size=n)

    # Base coolant pressure ~3.2 bar; night shift slightly lower on average
    coolant = rng.normal(3.20, 0.12, size=n)
    coolant = np.where(shift == "Night", coolant - rng.normal(0.08, 0.04, size=n), coolant)
    coolant = np.where(machine == "CNC-04", coolant - 0.05, coolant)  # one problem machine
    coolant = np.clip(coolant, 2.5, 3.8)

    # Stability: fraction of nominal (1.0 = stable). Unstable when pressure drifts.
    stability = rng.normal(0.97, 0.04, size=n)
    stability = np.where(shift == "Night", stability - rng.normal(0.03, 0.02, size=n), stability)
    stability = np.where(coolant < 3.0, stability - 0.06, stability)
    stability = np.clip(stability, 0.75, 1.0)

    vacuum = rng.normal(-82.0, 3.0, size=n)  # fixture vacuum, kPa (negative gauge)
    vacuum = np.where(
        trace["Fixture_ID"].isin(HIGH_RISK_FIXTURES),
        vacuum + rng.normal(2.0, 1.0, size=n),
        vacuum,
    )

    return pd.DataFrame(
        {
            "Tool_Life_Pct": np.round(tool_life, 1),
            "Spindle_Speed_rpm": spindle,
            "Feed_Rate_mm_min": np.round(feed, 1),
            "Coolant_Pressure_bar": np.round(coolant, 2),
            "Coolant_Pressure_Stability": np.round(stability, 3),
            "Vacuum_Level_kPa": np.round(vacuum, 1),
        }
    )


def compute_chipping_risk(
    tool_life: np.ndarray,
    coolant: np.ndarray,
    stability: np.ndarray,
    machine: np.ndarray,
    fixture: np.ndarray,
    shift: np.ndarray,
    feed: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Return a unitless risk score (higher = more chipping).
    Risk rises around 75% tool life, especially with unstable coolant.
    """
    risk = rng.normal(0.0, 0.12, size=len(tool_life))

    # Tool wear effect kicks in at ~75%
    wear_factor = np.clip((tool_life - TOOL_WEAR_RISK_PCT) / 25.0, 0.0, 1.0)
    risk += wear_factor * 1.2

    # Low or unstable coolant amplifies wear-related chipping
    low_coolant = np.clip((3.15 - coolant) / 0.5, 0.0, 1.0)
    unstable = np.clip(1.0 - stability, 0.0, 0.25) / 0.25
    risk += wear_factor * low_coolant * 1.5
    risk += wear_factor * unstable * 1.8

    # Machine / fixture / shift (subtle, not exaggerated)
    risk += np.isin(machine, list(HIGH_RISK_MACHINES)).astype(float) * 0.25
    risk += np.isin(fixture, list(HIGH_RISK_FIXTURES)).astype(float) * 0.20
    risk += (shift == "Night").astype(float) * 0.10
    risk += np.clip((feed - 870) / 80.0, 0.0, 1.0) * 0.15

    return risk


def generate_ctqs(
    trace: pd.DataFrame,
    process: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate CTQ measurements driven by process conditions."""
    n = len(trace)
    tool_life = process["Tool_Life_Pct"].to_numpy()
    coolant = process["Coolant_Pressure_bar"].to_numpy()
    stability = process["Coolant_Pressure_Stability"].to_numpy()
    feed = process["Feed_Rate_mm_min"].to_numpy()
    machine = trace["Machine_ID"].to_numpy()
    fixture = trace["Fixture_ID"].to_numpy()
    shift = trace["Shift"].to_numpy()

    # Chamfer width: target 0.30 with mild drift as tool wears
    chamfer_drift = (tool_life - 50.0) / 100.0 * 0.04  # up to ~0.02 mm drift at high wear
    fixture_bias = np.where(np.isin(fixture, list(CHAMFER_BIAS_FIXTURES)), 0.015, 0.0)
    night_noise = np.where(shift == "Night", rng.normal(0, 0.004, size=n), 0.0)
    chamfer = (
        CHAMFER_TARGET_MM
        + chamfer_drift
        + fixture_bias
        + rng.normal(0, 0.008, size=n)
        + night_noise
    )

    # Chipping size (um): mostly zero; elevated tail when risk is high
    risk = compute_chipping_risk(
        tool_life, coolant, stability, machine, fixture, shift, feed, rng
    )

    chipping = np.zeros(n)
    # Low-level background measurement noise on most units
    chipping += rng.exponential(scale=2.5, size=n) * (rng.random(n) < 0.15)
    # Risk-driven chipping events (dominant NG mode in Phase 1)
    elevated = risk > 0.38
    chipping[elevated] += rng.exponential(scale=55, size=elevated.sum()) * (
        risk[elevated] - 0.25
    )
    # Extra tail when high wear meets unstable coolant
    high_wear_unstable = (tool_life >= TOOL_WEAR_RISK_PCT) & (stability < 0.92)
    chipping[high_wear_unstable] += rng.exponential(scale=40, size=high_wear_unstable.sum())
    chipping = np.clip(chipping, 0.0, None)
    chipping[chipping < 5] = 0.0  # below measurement noise -> zero

    # Thickness: tight unless dimension special cause
    thickness = rng.normal(THICKNESS_TARGET_MM, 0.004, size=n)
    thickness += np.where(fixture == "FIX-A3", rng.normal(0.006, 0.002, size=n), 0.0)

    # Warpage and strengthening (mostly OK, rare fails)
    warpage = np.abs(rng.normal(0.025, 0.012, size=n))
    warpage += (shift == "Night").astype(float) * rng.exponential(0.005, size=n)

    cs = rng.normal(785, 12, size=n)
    dol = rng.normal(46, 2.0, size=n)
    # Rare strengthening special cause (~0.15% of units)
    weak = rng.random(size=n) < 0.0015
    cs[weak] = rng.normal(665, 10, size=weak.sum())
    dol[weak] = rng.normal(31, 2, size=weak.sum())

    return pd.DataFrame(
        {
            "Chamfer_Width_mm": np.round(chamfer, 4),
            "Chipping_Size_um": np.round(chipping, 1),
            "Thickness_mm": np.round(thickness, 4),
            "Warpage_mm": np.round(warpage, 4),
            "CS_MPa": np.round(cs, 1),
            "DOL_um": np.round(dol, 1),
            "_chipping_risk": risk,  # internal only; dropped before save
        }
    )


def assign_defects(
    ctqs: pd.DataFrame,
    trace: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Determine defect type, location, AOI and final result from CTQs and risk."""
    n = len(ctqs)
    chamfer = ctqs["Chamfer_Width_mm"].to_numpy()
    chipping = ctqs["Chipping_Size_um"].to_numpy()
    thickness = ctqs["Thickness_mm"].to_numpy()
    warpage = ctqs["Warpage_mm"].to_numpy()
    cs = ctqs["CS_MPa"].to_numpy()
    dol = ctqs["DOL_um"].to_numpy()

    chipping_fail = chipping > CHIPPING_FAIL_UM
    chamfer_fail = (chamfer < CHAMFER_LSL_MM) | (chamfer > CHAMFER_USL_MM)
    thickness_fail = (thickness < THICKNESS_LSL_MM) | (thickness > THICKNESS_USL_MM)
    warpage_fail = warpage > WARPAGE_FAIL_MM
    strengthening_fail = (cs < CS_FAIL_MPA) | (dol < DOL_FAIL_UM)

    # Priority order for primary defect assignment (chipping dominant among NG)
    defect_type = np.full(n, "None", dtype=object)
    defect_location = np.full(n, "None", dtype=object)

    # Rare cosmetic fails (~0.6% of units)
    cosmetic = rng.random(n) < 0.006
    defect_type[cosmetic] = rng.choice(
        ["Scratch", "Particle"], size=cosmetic.sum(), p=[0.6, 0.4]
    )

    defect_type[warpage_fail] = "Warpage_OOS"
    defect_type[strengthening_fail] = "Strengthening_OOS"
    defect_type[thickness_fail | chamfer_fail] = "Dimension_OOS"
    defect_type[chipping_fail] = "Edge_Chipping"  # highest priority among NG

    for dtype, loc in DEFECT_LOCATION_MAP.items():
        mask = defect_type == dtype
        if dtype == "Edge_Chipping":
            # Vary edge defect location for heatmap analysis
            defect_location[mask] = rng.choice(
                ["Edge", "Corner", "Camera_Hole", "Speaker_Slot"],
                size=mask.sum(),
                p=[0.55, 0.20, 0.15, 0.10],
            )
        elif dtype == "Scratch":
            defect_location[mask] = rng.choice(["Surface", "Edge"], size=mask.sum())
        elif dtype == "Particle":
            defect_location[mask] = "Surface"
        else:
            defect_location[mask] = loc

    has_defect = defect_type != "None"
    aoi_result = np.where(has_defect, "Fail", "Pass")

    # Final result: NG if AOI fail OR key CTQ out of spec (even if AOI missed it)
    ctq_fail = (
        chipping_fail | chamfer_fail | thickness_fail | warpage_fail | strengthening_fail
    )
    final_result = np.where(has_defect | ctq_fail, "NG", "OK")

    return pd.DataFrame(
        {
            "Defect_Type": defect_type,
            "Defect_Location": defect_location,
            "AOI_Result": aoi_result,
            "Final_Result": final_result,
        }
    )


def generate_dataset(n: int = ROW_COUNT, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Build the full synthetic dataset."""
    rng = np.random.default_rng(seed)

    trace = generate_traceability(n, rng)
    process = generate_cnc_process(trace, rng)
    ctqs = generate_ctqs(trace, process, rng)
    defects = assign_defects(ctqs, trace, rng)

    df = pd.concat([trace, process, ctqs.drop(columns=["_chipping_risk"]), defects], axis=1)
    return df


def print_summary(df: pd.DataFrame, output_path: Path) -> None:
    """Print concise generation summary to stdout."""
    ok_count = (df["Final_Result"] == "OK").sum()
    ng_count = (df["Final_Result"] == "NG").sum()
    ng_rate = ng_count / len(df) * 100

    print("--- Synthetic dataset summary ---")
    print(f"Rows:        {len(df):,}")
    print(f"OK:          {ok_count:,}")
    print(f"NG:          {ng_count:,}")
    print(f"NG rate:     {ng_rate:.2f}%")
    print("Top defects (NG parts only):")
    ng_defects = df.loc[df["Final_Result"] == "NG", "Defect_Type"]
    for dtype, count in ng_defects.value_counts().head(5).items():
        print(f"  {dtype}: {count:,}")
    print(f"Output path: {output_path}")


def main() -> None:
    """Generate CSV and print summary."""
    root = project_root()
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_path = raw_dir / "cover_glass_synthetic.csv"
    df = generate_dataset()
    df.to_csv(output_path, index=False)
    print_summary(df, output_path)


if __name__ == "__main__":
    main()
