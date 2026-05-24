"""
Pareto analysis of defect types for NG cover glass units.

Pareto analysis is a core MQE tool: a small number of defect modes usually
account for most quality loss. Ranking fail modes by frequency helps the team
focus corrective action on the " vital few " instead of chasing noise.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Defect category used for OK units — not a real fail mode for Pareto
NO_DEFECT_LABEL = "None"


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, keep_default_na=False)


def build_pareto_table(ng_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build Pareto table: count, % of NG, cumulative %.
    Expects NG rows only, with 'None' already excluded.
    """
    counts = ng_df["Defect_Type"].value_counts().sort_values(ascending=False)
    total_ng = counts.sum()

    pareto = pd.DataFrame(
        {
            "Defect_Type": counts.index,
            "Count": counts.values,
            "Pct_of_NG": (counts.values / total_ng * 100).round(2),
        }
    )
    pareto["Cumulative_Pct"] = pareto["Pct_of_NG"].cumsum().round(2)
    return pareto


def plot_pareto(pareto: pd.DataFrame, output_path: Path) -> None:
    """Save bar chart (counts) with cumulative percentage line."""
    fig, ax1 = plt.subplots(figsize=(10, 6))

    x = range(len(pareto))
    bars = ax1.bar(x, pareto["Count"], color="steelblue", edgecolor="black", linewidth=0.5)
    ax1.set_xlabel("Defect Type")
    ax1.set_ylabel("Count (NG units)")
    ax1.set_title("Pareto Chart — Defect Types (NG Units, Simulated Data)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(pareto["Defect_Type"], rotation=30, ha="right")

    # Label bar tops for readability
    for bar, count in zip(bars, pareto["Count"]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{count:,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Cumulative percentage on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(
        list(x),
        pareto["Cumulative_Pct"],
        color="darkorange",
        marker="o",
        linewidth=2,
        label="Cumulative %",
    )
    ax2.set_ylabel("Cumulative % of NG")
    ax2.set_ylim(0, 105)
    ax2.axhline(y=80, color="gray", linestyle="--", linewidth=0.8, label="80% line")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_report(
    df: pd.DataFrame,
    pareto: pd.DataFrame,
    table_path: Path,
    figure_path: Path,
) -> None:
    """Print concise Pareto summary to stdout."""
    total_rows = len(df)
    ng_count = (df["Final_Result"] == "NG").sum()
    ng_rate = ng_count / total_rows * 100

    top = pareto.iloc[0]
    print("--- Defect Pareto Report (Simulated Data) ---")
    print(f"Total rows:              {total_rows:,}")
    print(f"Total NG:                {ng_count:,}")
    print(f"NG rate:                 {ng_rate:.2f}%")
    print(f"Top defect type:         {top['Defect_Type']}")
    print(f"Top defect count:        {int(top['Count']):,}")
    print(f"Top defect % of NG:      {top['Pct_of_NG']:.2f}%")
    print(f"Pareto table saved to:   {table_path}")
    print(f"Pareto chart saved to:   {figure_path}")


def main() -> None:
    root = project_root()
    data_path = default_data_path()
    table_path = root / "outputs" / "reports" / "defect_pareto.csv"
    figure_path = root / "outputs" / "figures" / "defect_pareto.png"

    df = load_data(data_path)

    # NG parts only; exclude OK placeholder defect label
    ng_df = df[(df["Final_Result"] == "NG") & (df["Defect_Type"] != NO_DEFECT_LABEL)]

    pareto = build_pareto_table(ng_df)

    table_path.parent.mkdir(parents=True, exist_ok=True)
    pareto.to_csv(table_path, index=False)

    plot_pareto(pareto, figure_path)
    print_report(df, pareto, table_path, figure_path)


if __name__ == "__main__":
    main()
