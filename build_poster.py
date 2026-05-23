from pathlib import Path
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle


project_root = Path(__file__).resolve().parent
figures_dir = project_root / "output" / "figures"
poster_path = project_root / "output" / "poster.pdf"
daily_data_path = project_root / "data" / "processed" / "germany_daily.csv"

colors = {
    "cases": "#0072B2",
    "deaths": "#D55E00",
    "vaccination": "#009E73",
    "ink": "#111827",
    "muted": "#6B7280",
    "rule": "#E5E7EB",
}

plots = {
    "overview": "plot01_daily_cases_deaths.png",
    "incidence": "plot02_7day_incidence.png",
    "vaccination": "plot04_vaccination_progress.png",
    "cfr": "plot03_cfr_over_time.png",
    "waves": "plot05_wave_phases.png",
}


def load_poster_stats() -> dict[str, str]:
    """Read headline statistics displayed on the poster.

    Returns:
        Dictionary with formatted values for the poster summary row.

    Raises:
        FileNotFoundError: If the processed Germany data file is missing.
    """
    if not daily_data_path.exists():
        raise FileNotFoundError(
            "Run `python3 scripts/run_part1.py` before building the poster."
        )

    df = pd.read_csv(daily_data_path, parse_dates=["date"])
    latest = df.dropna(subset=["total_cases", "total_deaths"]).iloc[-1]
    daily = df[df["incidence_7day_per_100k"].notna()]
    peak_incidence = daily.loc[daily["incidence_7day_per_100k"].idxmax()]

    return {
        "cases": f"{int(round(latest['total_cases'])):,}".replace(",", " "),
        "deaths": f"{int(round(latest['total_deaths'])):,}".replace(",", " "),
        "cfr": f"{latest['cfr_percent']:.2f}%",
        "vaccinated": f"{latest['people_vaccinated_per_100']:.1f}%",
        "fully": f"{latest['people_fully_vaccinated_per_100']:.1f}%",
        "last_total_date": latest["date"].strftime("%d %b %Y"),
        "last_daily_date": daily["date"].max().strftime("%d %b %Y"),
        "peak_incidence": f"{peak_incidence['incidence_7day_per_100k']:.0f}",
        "peak_incidence_date": peak_incidence["date"].strftime("%d %b %Y"),
    }


def main() -> None:
    """Build the A0 poster from generated figures.

    The script checks that all required figures exist, reads summary statistics
    from the processed data and saves the final PDF poster in `output/`.

    Raises:
        FileNotFoundError: If one of the required figure files is missing.
    """
    missing = [name for name in plots.values() if not (figures_dir / name).exists()]
    if missing:
        missing_list = "\n".join(f"- output/figures/{name}" for name in missing)
        raise FileNotFoundError(
            "Cannot build poster because required figures are missing.\n"
            "Run `python3 scripts/run_part1.py` first.\n"
            f"Missing files:\n{missing_list}"
        )

    stats = load_poster_stats()
    poster_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(46.8, 33.1), facecolor="white")
    grid = GridSpec(
        nrows=14,
        ncols=12,
        figure=fig,
        height_ratios=[0.95, 0.85, 0.9, 0.9, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
        hspace=0.35,
        wspace=0.32,
    )
    fig.subplots_adjust(left=0.035, right=0.975, top=0.965, bottom=0.045)

    header = fig.add_subplot(grid[0:2, :])
    header.axis("off")
    for x, width, color in [
        (0.00, 0.16, colors["cases"]),
        (0.17, 0.08, colors["deaths"]),
        (0.26, 0.08, colors["vaccination"]),
    ]:
        header.add_patch(
            Rectangle(
                (x, 0.88),
                width,
                0.06,
                transform=header.transAxes,
                color=color,
            )
        )
    header.text(
        0.0,
        0.58,
        "COVID-19 in Germany",
        fontsize=72,
        fontweight="bold",
        color=colors["ink"],
        ha="left",
        va="center",
    )
    header.text(
        0.0,
        0.20,
        "Descriptive analysis, pandemic waves and vaccination rollout | 2020-2024",
        fontsize=25,
        color=colors["muted"],
        ha="left",
        va="center",
    )
    header.text(
        1.0,
        0.20,
        "Data source: Our World in Data",
        fontsize=21,
        color=colors["muted"],
        ha="right",
        va="center",
    )

    stats_ax = fig.add_subplot(grid[2:4, :])
    stats_ax.axis("off")
    kpis = [
        (
            "Confirmed cases",
            stats["cases"],
            f"to {stats['last_total_date']}",
            colors["cases"],
        ),
        ("Deaths", stats["deaths"], f"CFR {stats['cfr']}", colors["deaths"]),
        (
            "Peak incidence",
            stats["peak_incidence"],
            stats["peak_incidence_date"],
            colors["cases"],
        ),
        (
            "Vaccinated",
            stats["vaccinated"],
            f"{stats['fully']} fully vaccinated",
            colors["vaccination"],
        ),
    ]
    card_width = 1 / len(kpis)
    for idx, (label, value, note, color) in enumerate(kpis):
        x = idx * card_width
        width = card_width - 0.012
        stats_ax.add_patch(
            Rectangle(
                (x, 0.10),
                width,
                0.80,
                transform=stats_ax.transAxes,
                facecolor="white",
                edgecolor=colors["rule"],
                linewidth=1.2,
            )
        )
        stats_ax.add_patch(
            Rectangle(
                (x, 0.84),
                width,
                0.06,
                transform=stats_ax.transAxes,
                facecolor=color,
                edgecolor=color,
            )
        )
        stats_ax.text(
            x + 0.014,
            0.64,
            label,
            transform=stats_ax.transAxes,
            fontsize=16,
            fontweight="bold",
            color=colors["ink"],
            ha="left",
        )
        stats_ax.text(
            x + 0.014,
            0.37,
            value,
            transform=stats_ax.transAxes,
            fontsize=28,
            fontweight="bold",
            color=colors["ink"],
            ha="left",
        )
        stats_ax.text(
            x + 0.014,
            0.17,
            note,
            transform=stats_ax.transAxes,
            fontsize=11.5,
            color=colors["muted"],
            ha="left",
        )

    plot_cells = [
        ("overview", grid[4:9, 0:6]),
        ("incidence", grid[4:9, 6:12]),
        ("vaccination", grid[9:13, 0:4]),
        ("cfr", grid[9:13, 4:8]),
        ("waves", grid[9:13, 8:12]),
    ]
    for plot_key, cell in plot_cells:
        ax = fig.add_subplot(cell)
        ax.axis("off")
        ax.imshow(plt.imread(figures_dir / plots[plot_key]))

    fig.text(
        0.035,
        0.018,
        f"Daily case/death reporting used for rolling rates is available through {stats['last_daily_date']}; "
        f"cumulative totals continue through {stats['last_total_date']}. "
        "All figures are reproducible from the Python scripts in scripts/.",
        fontsize=12,
        color=colors["muted"],
        ha="left",
    )

    fig.savefig(poster_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {poster_path}")


if __name__ == "__main__":
    main()
