from pathlib import Path
import os

import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "figure.facecolor": "white",
        "axes.titlesize": 30,
        "axes.labelsize": 23,
        "xtick.labelsize": 17,
        "ytick.labelsize": 17,
        "legend.fontsize": 17,
        "axes.titleweight": "normal",
        "axes.labelcolor": "#1f2937",
        "xtick.color": "#374151",
        "ytick.color": "#374151",
        "savefig.dpi": 320,
    }
)

project_root = Path(__file__).resolve().parents[1]
data_raw = project_root / "data" / "raw"
data_processed = project_root / "data" / "processed"
figures_dir = project_root / "output" / "figures"

germany_iso = "DEU"
poland_iso = "POL"
start_date = "2020-01-01"
end_date = "2024-12-31"

wave_periods = {
    "Wave 1": ("2020-03-01", "2020-06-30"),
    "Wave 2": ("2020-10-01", "2021-02-28"),
    "Wave 3": ("2021-03-01", "2021-06-30"),
    "Wave 4": ("2021-10-01", "2022-01-31"),
    "Wave 5 (Omicron)": ("2022-02-01", "2022-06-30"),
    "Decline": ("2022-07-01", "2024-12-31"),
}

phase_colors = {
    "Wave 1": "#f3f4f6",
    "Wave 2": "#eceff3",
    "Wave 3": "#f3f4f6",
    "Wave 4": "#eceff3",
    "Wave 5 (Omicron)": "#e5e7eb",
    "Decline": "#f7f7f7",
}

palette = {
    "background": "#ffffff",
    "cases": "#0072B2",
    "cases_fill": "#0072B2",
    "deaths": "#D55E00",
    "deaths_fill": "#D55E00",
    "vaccination": "#009E73",
    "vaccination_alt": "#56B4E9",
    "boosters": "#CC79A7",
    "neutral": "#9CA3AF",
    "neutral_light": "#F3F4F6",
    "slate": "#111827",
    "muted": "#6B7280",
    "grid": "#D1D5DB",
    "spine": "#9CA3AF",
}

annotation_events = [
    ("First lockdown", "2020-03-22"),
    ("Vaccine rollout", "2020-12-27"),
    ("Omicron emergence", "2021-12-01"),
]


def load_germany_daily() -> pd.DataFrame:
    """Load the processed daily Germany data.

    Returns:
        Daily Germany data with the `date` column parsed as dates.

    Raises:
        FileNotFoundError: If the processed CSV file has not been created yet.
    """
    path = data_processed / "germany_daily.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run scripts/01_clean_merge.py first."
        )
    return pd.read_csv(path, parse_dates=["date"])


def apply_style(ax: plt.Axes, title: str | None = None, date_axis: bool = True) -> None:
    """Apply the shared style used in all static plots.

    Args:
        ax: Matplotlib axis to format.
        title: Optional plot title.
        date_axis: Whether the x-axis should be formatted as calendar years.
    """
    ax.set_facecolor(palette["background"])
    ax.grid(True, axis="y", color=palette["grid"], linewidth=0.9, alpha=0.55)
    ax.grid(False, axis="x")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(palette["spine"])
    ax.spines["bottom"].set_color(palette["spine"])
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(colors=palette["slate"], labelsize=17, length=4, width=0.8)
    if date_axis:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if title:
        ax.set_title(
            title,
            loc="center",
            fontsize=30,
            fontweight="bold",
            pad=26,
            color=palette["slate"],
        )


def add_event_annotations(ax: plt.Axes, ymax_fraction: float = 0.92) -> None:
    """Annotate selected pandemic events on a time-series plot.

    Args:
        ax: Matplotlib axis with a date x-axis.
        ymax_fraction: Vertical position of labels as a fraction of the y-axis range.
    """
    ymin, ymax = ax.get_ylim()
    y = ymin + (ymax - ymin) * ymax_fraction
    xmin, xmax = ax.get_xlim()
    for label, date in annotation_events:
        x = pd.Timestamp(date)
        x_num = mdates.date2num(x)
        if x_num < xmin or x_num > xmax:
            continue
        ax.axvline(x, color=palette["neutral"], linewidth=1.1, linestyle=":", alpha=0.8)
        ax.text(
            x,
            y,
            label,
            rotation=90,
            ha="right",
            va="top",
            fontsize=12.5,
            color=palette["muted"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.8},
        )


def number_formatter() -> FuncFormatter:
    """Create a compact number formatter for plot axes.

    Returns:
        Matplotlib formatter that writes large values as `k` or `M`.
    """
    def _format(value: float, _pos: int) -> str:
        """Format one tick value.

        Args:
            value: Numeric tick value.
            _pos: Tick position passed by Matplotlib and not used here.

        Returns:
            Short human-readable tick label.
        """
        value_abs = abs(value)
        if value_abs >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value_abs >= 1_000:
            scaled = value / 1_000
            return f"{scaled:.0f}k" if scaled.is_integer() else f"{scaled:.1f}k"
        return f"{value:.0f}"

    return FuncFormatter(_format)


def save_figure(fig: plt.Figure, name: str) -> None:
    """Save a plot as PNG and SVG.

    Args:
        fig: Matplotlib figure to save.
        name: Base file name without extension.
    """
    figures_dir.mkdir(parents=True, exist_ok=True)
    png_path = figures_dir / f"{name}.png"
    svg_path = figures_dir / f"{name}.svg"
    fig.savefig(png_path, dpi=320, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {png_path.relative_to(project_root)}")
    print(f"Saved {svg_path.relative_to(project_root)}")


def save_plotly_html(plotly_fig, path) -> None:
    """Save a Plotly figure as a self-contained, responsive HTML file.

    Injects CSS so the chart fills 100 % of its iframe container and has no
    scrollbars — required for the srcdoc-embedded Reveal.js slides.

    Args:
        plotly_fig: A ``plotly.graph_objects.Figure`` instance.
        path: Destination ``pathlib.Path`` (parent dirs are created).
    """
    responsive_css = (
        "html,body{width:100%;height:100%;margin:0;padding:0;overflow:hidden;}"
        ".js-plotly-plot,.plot-container{width:100%!important;height:100%!important;}"
    )
    html = plotly_fig.to_html(
        full_html=True,
        include_plotlyjs="cdn",
        config={"responsive": True, "displaylogo": False},
    )
    html = html.replace("</head>", f"<style>{responsive_css}</style></head>", 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    print(f"Saved {path.relative_to(project_root)}")
