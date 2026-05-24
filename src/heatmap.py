"""
Defect location heatmap analysis for Edge_Chipping.

Where a chip appears on the part (edge, corner, camera hole, speaker slot)
narrows the root cause. Edge-heavy patterns point to contour/chamfer tooling;
feature-specific clusters suggest hole-drilling or fixture orientation issues.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

EDGE_CHIP_DEFECT = "Edge_Chipping"


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, keep_default_na=False)


def summarize_location(
    df: pd.DataFrame,
    chips: pd.DataFrame,
    group_cols: list[str],
    group_type: str,
    denominator_col: str | None = None,
) -> pd.DataFrame:
    """
    Summarize Edge_Chipping count and rate for one grouping.

    Rate = Edge_Chipping_Count / Total_Count * 100.
    For interaction groups, Total_Count uses denominator_col (e.g. Machine_ID).
    """
    if len(group_cols) == 1:
        col = group_cols[0]
        counts = chips.groupby(col, observed=False).size().rename("Edge_Chipping_Count")
        summary = counts.reset_index()
        summary["Group_Value"] = summary[col].astype(str)
        summary = summary.drop(columns=[col])
        # Location rates are vs all parts; machine/fixture rates use group totals
        if col == "Defect_Location":
            summary["Total_Count"] = len(df)
        else:
            totals = df.groupby(col, observed=False).size().rename("Total_Count").reset_index()
            totals["Group_Value"] = totals[col].astype(str)
            summary = summary.merge(totals[["Group_Value", "Total_Count"]], on="Group_Value", how="left")
    else:
        denom_col = denominator_col or group_cols[0]
        totals = df.groupby(denom_col, observed=False).size().rename("Total_Count").reset_index()
        counts = (
            chips.groupby(group_cols, observed=False)
            .size()
            .rename("Edge_Chipping_Count")
            .reset_index()
        )
        summary = counts.merge(totals, on=denom_col, how="left")
        summary["Group_Value"] = summary[group_cols[0]].astype(str)
        for col in group_cols[1:]:
            summary["Group_Value"] = summary["Group_Value"] + " | " + summary[col].astype(str)

    summary["Edge_Chipping_Count"] = summary["Edge_Chipping_Count"].astype(int)
    summary["Edge_Chipping_Rate"] = (
        summary["Edge_Chipping_Count"] / summary["Total_Count"] * 100
    ).round(2)
    summary["Group_Type"] = group_type

    return summary[
        ["Group_Type", "Group_Value", "Total_Count", "Edge_Chipping_Count", "Edge_Chipping_Rate"]
    ]


def build_location_summary(df: pd.DataFrame, chips: pd.DataFrame) -> pd.DataFrame:
    """Build combined location summary for all requested groupings."""
    parts = [
        summarize_location(df, chips, ["Defect_Location"], "Defect_Location"),
        summarize_location(df, chips, ["Machine_ID"], "Machine_ID"),
        summarize_location(
            df,
            chips,
            ["Machine_ID", "Defect_Location"],
            "Machine_ID_x_Defect_Location",
            denominator_col="Machine_ID",
        ),
        summarize_location(
            df,
            chips,
            ["Fixture_ID", "Defect_Location"],
            "Fixture_ID_x_Defect_Location",
            denominator_col="Fixture_ID",
        ),
    ]
    return pd.concat(parts, ignore_index=True)


def build_heatmap_matrix(chips: pd.DataFrame) -> pd.DataFrame:
    """Pivot Edge_Chipping counts: rows=Machine_ID, columns=Defect_Location."""
    matrix = pd.crosstab(chips["Machine_ID"], chips["Defect_Location"])
    # Consistent row/column order for readable chart
    matrix = matrix.sort_index(axis=0).sort_index(axis=1)
    return matrix


def plot_heatmap(matrix: pd.DataFrame, output_path: Path) -> None:
    """Save annotated heatmap-style figure using matplotlib imshow."""
    fig, ax = plt.subplots(figsize=(10, 6))

    data = matrix.to_numpy()
    im = ax.imshow(data, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)

    ax.set_xlabel("Defect Location")
    ax.set_ylabel("Machine ID")
    ax.set_title("Edge_Chipping Count by Machine and Location (Simulated Data)")

    # Annotate each cell with count
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            value = int(data[row, col])
            text_color = "white" if value > data.max() * 0.6 else "black"
            ax.text(col, row, str(value), ha="center", va="center", color=text_color, fontsize=9)

    fig.colorbar(im, ax=ax, label="Edge_Chipping Count")
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_report(summary: pd.DataFrame, chips: pd.DataFrame, csv_path: Path, fig_path: Path) -> None:
    """Print concise location analysis summary to stdout."""
    print("--- Defect Location Report (Simulated Data) ---")
    print(f"Total Edge_Chipping:     {len(chips):,}")
    print()

    by_location = summary[summary["Group_Type"] == "Defect_Location"].sort_values(
        "Edge_Chipping_Count", ascending=False
    )
    print("Top 5 Defect_Location counts:")
    for _, row in by_location.head(5).iterrows():
        print(f"  {row['Group_Value']}: {int(row['Edge_Chipping_Count']):,}")
    print()

    by_combo = summary[summary["Group_Type"] == "Machine_ID_x_Defect_Location"].sort_values(
        "Edge_Chipping_Count", ascending=False
    )
    print("Top Machine_ID + Defect_Location combinations:")
    for _, row in by_combo.head(5).iterrows():
        print(
            f"  {row['Group_Value']}: {int(row['Edge_Chipping_Count']):,} "
            f"({row['Edge_Chipping_Rate']:.2f}% of machine parts)"
        )
    print()
    print(f"Summary table:           {csv_path}")
    print(f"Heatmap figure:          {fig_path}")


def main() -> None:
    root = project_root()
    csv_path = root / "outputs" / "reports" / "defect_location_summary.csv"
    fig_path = root / "outputs" / "figures" / "chipping_location_heatmap.png"

    df = load_data(default_data_path())
    chips = df[df["Defect_Type"] == EDGE_CHIP_DEFECT].copy()

    summary = build_location_summary(df, chips)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(csv_path, index=False)

    matrix = build_heatmap_matrix(chips)
    plot_heatmap(matrix, fig_path)

    print_report(summary, chips, csv_path, fig_path)


if __name__ == "__main__":
    main()
