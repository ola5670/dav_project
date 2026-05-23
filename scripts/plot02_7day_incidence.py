import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from utils import (
    add_event_annotations,
    apply_style,
    load_germany_daily,
    number_formatter,
    palette,
    phase_colors,
    save_figure,
    wave_periods,
)


def main() -> None:
    """Generate the seven-day incidence figure.

    The plot shows confirmed cases per 100,000 people with pandemic phase bands
    and annotations for the largest observed incidence peak.
    """
    df = load_germany_daily()
    df = df[
        (df["date"] >= "2020-02-01")
        & (df["incidence_7day_per_100k"].notna())
    ].copy()

    fig, ax = plt.subplots(figsize=(18, 11))
    apply_style(ax, "Seven-day incidence in Germany")

    ax.fill_between(
        df["date"],
        df["incidence_7day_per_100k"],
        color=palette["cases_fill"],
        alpha=0.18,
        zorder=2,
    )
    ax.plot(
        df["date"],
        df["incidence_7day_per_100k"],
        color=palette["cases"],
        linewidth=3.0,
        zorder=3,
    )
    ymin, ymax = ax.get_ylim()
    for name, (start, end) in wave_periods.items():
        ax.axvspan(
            pd.Timestamp(start),
            pd.Timestamp(end),
            color=phase_colors[name],
            alpha=0.35,
            linewidth=0,
        )
    ax.set_ylim(ymin, ymax)
    add_event_annotations(ax, ymax_fraction=0.94)
    ax.set_xlim(pd.Timestamp("2020-02-01"), df["date"].max())
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Cases per 100k")
    ax.set_xlabel("Date")
    ax.yaxis.set_major_formatter(number_formatter())
    peaks = df.nlargest(3, "incidence_7day_per_100k").sort_values("date")
    for _, row in peaks.iterrows():
        ax.scatter(
            row["date"],
            row["incidence_7day_per_100k"],
            s=68,
            color=palette["cases"],
            edgecolor="white",
            linewidth=1.1,
            zorder=5,
        )
    highest = df.loc[df["incidence_7day_per_100k"].idxmax()]
    ax.annotate(
        f"Omicron peak\n{highest['incidence_7day_per_100k']:.0f} per 100k",
        xy=(highest["date"], highest["incidence_7day_per_100k"]),
        xytext=(38, -24),
        textcoords="offset points",
        fontsize=14,
        color=palette["slate"],
        arrowprops={"arrowstyle": "-", "color": palette["muted"], "linewidth": 1.0},
    )
    fig.tight_layout()
    save_figure(fig, "plot02_7day_incidence")


if __name__ == "__main__":
    main()
