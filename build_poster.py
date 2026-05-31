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
    "forecast": "#CC79A7",
    "comparison": "#E69F00",
    "panel_header": "#1f4e79",
    "ink": "#111827",
    "muted": "#6B7280",
    "rule": "#E5E7EB",
}

plots = {
    "overview": "plot01_daily_cases_deaths.png",
    "incidence": "plot07_forecast_two_periods.png",
    "vaccination": "plot04_vaccination_progress.png",
    "comparison": "plot08_germany_poland.png",
    "excess": "plot09_excess_mortality.png",
    "variants_forecast": "plot10_variants_heatmap.png",
}


def draw_contained_image(
    ax: plt.Axes, image, box: tuple[float, float, float, float]
) -> None:
    """Draw an image inside an axes-fraction box without stretching it."""
    left, bottom, width, height = box
    bbox = ax.get_position()
    axes_aspect = (bbox.width * ax.figure.get_figwidth()) / (
        bbox.height * ax.figure.get_figheight()
    )
    box_aspect = width * axes_aspect / height
    image_aspect = image.shape[1] / image.shape[0]

    if image_aspect > box_aspect:
        draw_width = width
        draw_height = width * axes_aspect / image_aspect
    else:
        draw_height = height
        draw_width = height * image_aspect / axes_aspect

    x0 = left + (width - draw_width) / 2
    y0 = bottom + (height - draw_height) / 2
    ax.imshow(
        image,
        extent=[x0, x0 + draw_width, y0, y0 + draw_height],
        aspect="auto",
        interpolation="lanczos",
    )


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

    fig = plt.figure(figsize=(33.1, 46.8), facecolor="white")
    grid = GridSpec(
        nrows=26,
        ncols=12,
        figure=fig,
        height_ratios=[
            1.35,
            1.35,  # larger header
            0.82,
            0.82,  # KPI band
            0.48,  # KPI-to-plots gap
            1,
            1,
            1,
            1,
            1,
            1,  # row 1
            0.55,  # row gap
            1,
            1,
            1,
            1,
            1,
            1,  # row 2
            0.55,  # row gap
            1,
            1,
            1,
            1,
            1,
            1,  # row 3
            0.20,  # footer
        ],
        hspace=0.00,
        wspace=0.46,
    )
    fig.subplots_adjust(left=0.048, right=0.952, top=0.972, bottom=0.045)

    header = fig.add_subplot(grid[0:2, :])
    header.axis("off")
    for x, width, color in [
        (0.00, 0.07, colors["cases"]),
        (0.08, 0.07, colors["deaths"]),
        (0.16, 0.07, colors["vaccination"]),
        (0.24, 0.07, colors["forecast"]),
        (0.32, 0.07, colors["comparison"]),
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
        0.64,
        "COVID-19 in Germany",
        fontsize=88,
        fontweight="bold",
        color=colors["ink"],
        ha="left",
        va="center",
    )
    header.text(
        0.0,
        0.34,
        "Descriptive & inferential analysis | 2020-2024",
        fontsize=36,
        color=colors["muted"],
        ha="left",
        va="center",
    )
    header.text(
        0.0,
        0.13,
        "Aleksandra Pawłowska · Karolina Winczewska",
        fontsize=24,
        color=colors["muted"],
        ha="left",
        va="center",
    )
    header.text(
        0.95,
        0.05,
        "Data source: Our World in Data",
        fontsize=20,
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
        ("Deaths", stats["deaths"], "confirmed deaths", colors["deaths"]),
        ("CFR", stats["cfr"], "deaths / confirmed cases", colors["forecast"]),
        (
            "Peak incidence",
            stats["peak_incidence"],
            stats["peak_incidence_date"],
            colors["comparison"],
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
            0.68,
            label,
            transform=stats_ax.transAxes,
            fontsize=22,
            fontweight="bold",
            color=colors["ink"],
            ha="left",
        )
        stats_ax.text(
            x + 0.014,
            0.39,
            value,
            transform=stats_ax.transAxes,
            fontsize=35,
            fontweight="bold",
            color=colors["ink"],
            ha="left",
        )
        stats_ax.text(
            x + 0.014,
            0.14,
            note,
            transform=stats_ax.transAxes,
            fontsize=17,
            color=colors["muted"],
            ha="left",
        )

    plot_cells = [
        ("overview", grid[5:11, 0:6]),
        ("incidence", grid[5:11, 6:12]),
        ("vaccination", grid[12:18, 0:6]),
        ("comparison", grid[12:18, 6:12]),
        ("excess", grid[19:25, 0:6]),
        ("variants_forecast", grid[19:25, 6:12]),
    ]

    plot_titles = {
        "overview": "COVID-19 Cases and Deaths",
        "incidence": "Forecast: Two Pandemic Periods",
        "vaccination": "Vaccination Rollout",
        "comparison": "Germany vs Poland Comparison",
        "excess": "Excess Mortality Analysis",
        "variants_forecast": "Variant Dominance",
    }

    for plot_key, cell in plot_cells:
        ax = fig.add_subplot(cell)
        ax.axis("off")

        ax.add_patch(
            Rectangle(
                (0, 0.94),
                1,
                0.06,
                transform=ax.transAxes,
                facecolor=colors["panel_header"],
                edgecolor=colors["panel_header"],
            )
        )

        ax.text(
            0.015,
            0.965,
            plot_titles[plot_key],
            transform=ax.transAxes,
            fontsize=24,
            fontweight="bold",
            color="white",
            ha="left",
            va="center",
        )

        image = plt.imread(figures_dir / plots[plot_key])
        draw_contained_image(ax, image, (0, 0, 1, 0.92))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

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
