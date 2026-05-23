import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from utils import (
    add_event_annotations,
    apply_style,
    end_date,
    load_germany_daily,
    palette,
    phase_colors,
    save_figure,
    wave_periods,
)


def main() -> None:
    """Generate the case fatality ratio figure.

    The plot compares the cumulative CFR with a simple 28-day smoothed trend to
    make the long-term pattern easier to read.
    """
    df = load_germany_daily()
    df = df[
        (df["date"] >= "2020-04-01")
        & (df["date"] <= end_date)
        & (df["total_cases"] >= 10_000)
    ].copy()
    df["cfr_smooth"] = df["cfr_percent"].rolling(28, min_periods=7).mean()

    fig, ax = plt.subplots(figsize=(18, 11))
    ax.plot(
        df["date"],
        df["cfr_percent"],
        color=palette["neutral"],
        linewidth=1.6,
        alpha=0.38,
        label="Cumulative CFR",
    )
    ax.plot(
        df["date"],
        df["cfr_smooth"],
        color=palette["deaths"],
        linewidth=3.2,
        label="28-day smoothed CFR",
    )
    apply_style(ax, "Case fatality ratio")
    ymin, ymax = ax.get_ylim()
    for name, (start, end) in wave_periods.items():
        ax.axvspan(
            pd.Timestamp(start),
            pd.Timestamp(end),
            color=phase_colors[name],
            alpha=0.30,
            linewidth=0,
        )
    ax.set_ylim(ymin, ymax)
    add_event_annotations(ax, ymax_fraction=0.95)
    ax.set_xlim(pd.Timestamp("2020-04-01"), df["date"].max())
    ax.set_ylabel("Deaths / confirmed cases")
    ax.set_xlabel("Date")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(lambda value, _pos: f"{value:.0f}%")
    ax.legend(loc="upper right", frameon=False, handlelength=2.8)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.88, bottom=0.12)
    save_figure(fig, "plot03_cfr_over_time")


if __name__ == "__main__":
    main()
