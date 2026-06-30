from __future__ import annotations

import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "code" / "outputs" / "model_scores.csv"
FIGURES = ROOT / "figures"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    }
)


def read_rows() -> list[dict[str, str]]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    rows = read_rows()
    labels = [row["route"] for row in rows]
    scores = [float(row["validation_score"]) for row in rows]
    drops = [float(row["sensitivity_drop"]) for row in rows]
    x = range(len(labels))

    FIGURES.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), constrained_layout=True)
    colors = ["#767676", "#3775BA", "#0F4D92"]

    axes[0].bar(x, scores, color=colors, width=0.62)
    axes[0].set_xticks(list(x), labels, rotation=20, ha="right")
    axes[0].set_ylabel("Validation score")
    axes[0].set_ylim(0.65, 0.9)
    axes[0].set_title("Proposed route improves validation")
    axes[0].text(-0.15, 1.05, "a", transform=axes[0].transAxes, fontweight="bold")

    axes[1].bar(x, drops, color=colors, width=0.62)
    axes[1].set_xticks(list(x), labels, rotation=20, ha="right")
    axes[1].set_ylabel("Sensitivity drop")
    axes[1].set_ylim(0, 0.22)
    axes[1].set_title("Robustness loss remains smaller")
    axes[1].text(-0.15, 1.05, "b", transform=axes[1].transAxes, fontweight="bold")

    output = FIGURES / "fig_model_score_comparison"
    fig.savefig(f"{output}.svg", bbox_inches="tight")
    fig.savefig(f"{output}.pdf", bbox_inches="tight")
    fig.savefig(f"{output}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
