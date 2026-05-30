import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from utils import (
    add_event_annotations,
    apply_style,
    axis_limits,
    load_germany_daily,
    number_formatter,
    palette,
    phase_colors,
    save_figure,
    wave_periods,
)


def main() -> None:
    """Generate the cases and deaths time-series figure.

    The plot uses seven-day rates per 100,000 people and marks the highest
    observed case and death periods.
    """
    df = load_germany_daily()
    df = df[
        (df["date"] >= "2020-02-01")
        & (df["incidence_7day_per_100k"].notna())
        & (df["deaths_7day_per_100k"].notna())
    ].copy()

    fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
    fig.suptitle(
        "COVID-19 Cases and Deaths in Germany",
        fontsize=32,
        fontweight="bold",
        color=palette["slate"],
        y=0.99,
    )
    ax = axes[0]
    ax.plot(
        df["date"],
        df["incidence_7day_per_100k"],
        color=palette["cases"],
        linewidth=3.0,
    )
    ax.fill_between(
        df["date"],
        df["incidence_7day_per_100k"],
        color=palette["cases_fill"],
        alpha=0.18,
    )
    apply_style(ax)
    ymin, ymax = ax.get_ylim()
    for name, (start, end) in wave_periods.items():
        ax.axvspan(
            pd.Timestamp(start),
            pd.Timestamp(end),
            color=phase_colors[name],
            alpha=0.36,
            linewidth=0,
        )
    ax.set_ylim(*axis_limits["incidence_per_100k"])
    add_event_annotations(ax, ymax_fraction=0.95)
    ax.set_ylabel("Cases per 100,000 people")
    ax.yaxis.set_major_formatter(number_formatter())
    ax.set_xlim(pd.Timestamp("2020-02-01"), df["date"].max())
    peak_cases = df.loc[df["incidence_7day_per_100k"].idxmax()]
    ax.scatter(
        peak_cases["date"],
        peak_cases["incidence_7day_per_100k"],
        s=70,
        color=palette["cases"],
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
    )
    ax.annotate(
        f"Peak: {peak_cases['incidence_7day_per_100k']:.0f}",
        xy=(peak_cases["date"], peak_cases["incidence_7day_per_100k"]),
        xytext=(18, 18),
        textcoords="offset points",
        fontsize=13.5,
        color=palette["slate"],
        arrowprops={"arrowstyle": "-", "color": palette["muted"], "linewidth": 1.0},
    )

    ax = axes[1]
    ax.plot(
        df["date"],
        df["deaths_7day_per_100k"],
        color=palette["deaths"],
        linewidth=3.0,
    )
    ax.fill_between(
        df["date"],
        df["deaths_7day_per_100k"],
        color=palette["deaths_fill"],
        alpha=0.16,
    )
    apply_style(ax)
    ymin, ymax = ax.get_ylim()
    for name, (start, end) in wave_periods.items():
        ax.axvspan(
            pd.Timestamp(start),
            pd.Timestamp(end),
            color=phase_colors[name],
            alpha=0.36,
            linewidth=0,
        )
    ax.set_ylim(*axis_limits["deaths_per_100k"])
    add_event_annotations(ax, ymax_fraction=0.95)
    ax.set_ylabel("Deaths per 100,000 people")
    ax.set_xlabel("Date")
    ax.set_xlim(pd.Timestamp("2020-02-01"), df["date"].max())
    peak_deaths = df.loc[df["deaths_7day_per_100k"].idxmax()]
    ax.scatter(
        peak_deaths["date"],
        peak_deaths["deaths_7day_per_100k"],
        s=70,
        color=palette["deaths"],
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
    )
    ax.annotate(
        f"Peak: {peak_deaths['deaths_7day_per_100k']:.2f}",
        xy=(peak_deaths["date"], peak_deaths["deaths_7day_per_100k"]),
        xytext=(18, 18),
        textcoords="offset points",
        fontsize=13.5,
        color=palette["slate"],
        arrowprops={"arrowstyle": "-", "color": palette["muted"], "linewidth": 1.0},
    )

    fig.tight_layout(rect=[0, 0.035, 1, 0.96], h_pad=3.0)
    save_figure(fig, "plot01_daily_cases_deaths")


if __name__ == "__main__":
    main()
