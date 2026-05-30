import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import seaborn as sns

from utils import (
    axis_limits,
    apply_style,
    load_germany_daily,
    palette,
    save_figure,
    wave_periods,
)


def main() -> None:
    """Generate the incidence distribution figure by pandemic phase.

    The plot compares the distribution of seven-day incidence values across the
    fixed analysis periods used in the project.
    """
    df = load_germany_daily()
    order = list(wave_periods.keys())
    wave_df = df[df["wave"].isin(order)].copy()

    fig, ax = plt.subplots(figsize=(18, 11))
    sns.violinplot(
        data=wave_df,
        x="incidence_7day_per_100k",
        y="wave",
        order=order,
        ax=ax,
        color=palette["neutral_light"],
        inner=None,
        linewidth=0,
        cut=0,
    )
    sns.boxplot(
        data=wave_df,
        x="incidence_7day_per_100k",
        y="wave",
        order=order,
        ax=ax,
        width=0.26,
        color=palette["cases"],
        showcaps=True,
        boxprops={
            "facecolor": palette["cases"],
            "alpha": 0.72,
            "edgecolor": palette["slate"],
            "linewidth": 1.2,
        },
        whiskerprops={"color": palette["slate"], "linewidth": 1.2},
        capprops={"color": palette["slate"], "linewidth": 1.2},
        medianprops={"color": "white", "linewidth": 2.0},
        flierprops={
            "marker": "o",
            "markersize": 3,
            "markerfacecolor": palette["muted"],
            "markeredgecolor": "none",
            "alpha": 0.35,
        },
    )
    sns.stripplot(
        data=wave_df.sample(min(len(wave_df), 260), random_state=7),
        x="incidence_7day_per_100k",
        y="wave",
        order=order,
        ax=ax,
        color=palette["muted"],
        alpha=0.20,
        size=2.4,
        jitter=0.20,
    )
    apply_style(
        ax,
        "Incidence by pandemic phase",
        date_axis=False,
    )
    ax.set_xlabel("Seven-day incidence per 100,000 people")
    ax.set_ylabel("Pandemic phase")
    ax.set_xlim(*axis_limits["incidence_per_100k"])
    fig.tight_layout()
    save_figure(fig, "plot05_wave_phases")


if __name__ == "__main__":
    main()
