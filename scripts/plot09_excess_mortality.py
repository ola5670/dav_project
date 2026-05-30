"""Plot 09 – Excess mortality in Germany.

Plots the OWID `excess_mortality` column (percentage deviation from the
2015-2019 baseline provided by the Human Mortality Database / WMD) as a
bar chart.  A horizontal reference band at ±5 % marks the expected range.
"""

import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import (
    add_event_annotations,
    apply_style,
    load_germany_daily,
    palette,
    save_figure,
    wave_periods,
    phase_colors,
)

BASELINE_BAND = 5.0  # ± percent considered "normal"


def main() -> None:
    """Generate the excess mortality bar chart."""
    df = load_germany_daily()

    # excess_mortality is weekly in OWID — keep non-NaN rows only
    em = df[["date", "excess_mortality"]].dropna(subset=["excess_mortality"]).copy()
    em = em[em["date"] >= "2020-01-01"].copy()

    if em.empty:
        print("No excess_mortality data available — skipping plot09.")
        return

    colors_bars = np.where(
        em["excess_mortality"] >= 0, palette["deaths"], palette["vaccination"]
    )

    fig, ax = plt.subplots(figsize=(18, 9))

    ax.bar(
        em["date"],
        em["excess_mortality"],
        width=5,
        color=colors_bars,
        alpha=0.78,
        linewidth=0,
    )

    # Baseline band
    ax.axhspan(
        -BASELINE_BAND,
        BASELINE_BAND,
        color=palette["neutral_light"],
        alpha=0.55,
        linewidth=0,
        label=f"Expected range (±{BASELINE_BAND:.0f} %)",
    )
    ax.axhline(0, color=palette["spine"], linewidth=1.0, linestyle="-")

    # Wave shading (light)
    ymin, ymax = ax.get_ylim()
    for name, (start, end) in wave_periods.items():
        ax.axvspan(
            pd.Timestamp(start),
            pd.Timestamp(end),
            color=phase_colors[name],
            alpha=0.28,
            linewidth=0,
        )
    ax.set_ylim(ymin, ymax)

    add_event_annotations(ax, ymax_fraction=0.92)

    apply_style(
        ax, "Excess Mortality in Germany (% Above 2015–2019 Baseline)", date_axis=True
    )
    ax.set_ylabel("Excess mortality (%)")
    ax.set_xlabel("Date")
    ax.set_xlim(pd.Timestamp("2020-01-01"), em["date"].max())

    # Custom legend patch
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=palette["deaths"], alpha=0.78, label="Above baseline"),
        Patch(facecolor=palette["vaccination"], alpha=0.78, label="Below baseline"),
        Patch(
            facecolor=palette["neutral_light"],
            alpha=0.55,
            label=f"Expected ±{BASELINE_BAND:.0f} %",
        ),
    ]
    ax.legend(handles=legend_elements, fontsize=14, loc="upper right")

    fig.tight_layout()
    save_figure(fig, "plot09_excess_mortality")


if __name__ == "__main__":
    main()
