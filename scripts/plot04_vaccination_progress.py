import matplotlib.pyplot as plt
import pandas as pd

from utils import (
    add_event_annotations,
    apply_style,
    axis_limits,
    end_date,
    load_germany_daily,
    palette,
    save_figure,
)


def main() -> None:
    """Generate the vaccination rollout figure.

    The plot shows first-dose, initial-protocol and booster coverage per 100
    people, with simple milestone annotations.
    """
    df = load_germany_daily()
    df = df[(df["date"] >= "2020-12-01") & (df["date"] <= end_date)].copy()

    fig, ax = plt.subplots(figsize=(18, 11))
    ax.fill_between(
        df["date"],
        df["people_fully_vaccinated_per_100"],
        color=palette["vaccination"],
        alpha=0.14,
    )
    ax.plot(
        df["date"],
        df["people_vaccinated_per_100"],
        color=palette["vaccination_alt"],
        linewidth=3.0,
        label="At least 1 dose",
    )
    ax.plot(
        df["date"],
        df["people_fully_vaccinated_per_100"],
        color=palette["vaccination"],
        linewidth=3.2,
        label="Initial protocol",
    )
    ax.plot(
        df["date"],
        df["boosters_per_100"],
        color=palette["boosters"],
        linewidth=3.0,
        label="Boosters",
    )
    apply_style(ax, "Vaccination Rollout in Germany")
    ax.set_xlim(pd.Timestamp("2020-12-01"), df["date"].max())
    ax.set_ylim(*axis_limits["percentage"])
    add_event_annotations(ax, ymax_fraction=0.94)
    ax.set_ylabel("People per 100 population")
    ax.set_xlabel("Date")
    milestones = [
        (
            "50% initial protocol",
            "people_fully_vaccinated_per_100",
            50,
            (18, -34),
            "top",
        ),
        ("Booster rollout", "boosters_per_100", 10, (16, 16), "bottom"),
    ]
    for label, column, threshold, offset, va in milestones:
        reached = df[df[column] >= threshold]
        if not reached.empty:
            row = reached.iloc[0]
            ax.scatter(
                row["date"],
                row[column],
                s=62,
                color=palette["slate"],
                edgecolor="white",
                linewidth=1.0,
                zorder=5,
            )
            ax.annotate(
                label,
                xy=(row["date"], row[column]),
                xytext=offset,
                textcoords="offset points",
                fontsize=13.5,
                color=palette["slate"],
                va=va,
                arrowprops={
                    "arrowstyle": "-",
                    "color": palette["muted"],
                    "linewidth": 1.0,
                },
            )
    ax.legend(loc="upper right", frameon=False, handlelength=2.8)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.88, bottom=0.12)
    save_figure(fig, "plot04_vaccination_progress")


if __name__ == "__main__":
    main()
