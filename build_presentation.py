"""Build the Reveal.js HTML presentation.

Usage::

    python build_presentation.py

The script:
1. Reads headline statistics from the processed Germany CSV.
2. Embeds four interactive Plotly HTML files inline (plot01, plot04, plot06, plot08).
3. Renders ``templates/presentation_template.html`` via Jinja2.
4. Writes the result to ``output/presentation.html``.

The output is a single static file — no local server required.
"""
from pathlib import Path
import os
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import pandas as pd

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError as exc:
    sys.exit(
        "Jinja2 is required to build the presentation.\n"
        "Install it with:  pip install jinja2\n"
        f"Original error: {exc}"
    )

project_root     = Path(__file__).resolve().parent
templates_dir    = project_root / "templates"
output_dir       = project_root / "output"
figures_dir      = output_dir / "figures"
data_processed   = project_root / "data" / "processed"
presentation_out = output_dir / "presentation.html"

DAILY_CSV = data_processed / "germany_daily.csv"

# Mapping: template variable name → HTML file in figures/
INTERACTIVE_FILES = {
    "interactive_plot01": figures_dir / "plot01_daily_cases_deaths_interactive.html",
    "interactive_plot04": figures_dir / "plot04_vaccination_interactive.html",
    "interactive_plot06": figures_dir / "plot06_regression_interactive.html",
    "interactive_plot08": figures_dir / "plot08_germany_poland_interactive.html",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_stats() -> dict[str, str]:
    """Read headline statistics shown on the title slide.

    Returns:
        Dict with formatted numeric strings for key indicators.

    Raises:
        FileNotFoundError: If the processed CSV does not exist.
    """
    if not DAILY_CSV.exists():
        raise FileNotFoundError(
            f"{DAILY_CSV} not found.\n"
            "Run  python scripts/01_clean_merge.py  first."
        )
    df = pd.read_csv(DAILY_CSV, parse_dates=["date"])
    latest = df.dropna(subset=["total_cases", "total_deaths"]).iloc[-1]
    daily  = df[df["incidence_7day_per_100k"].notna()]

    def _fmt_int(v: float) -> str:
        return f"{int(round(v)):,}".replace(",", " ")  # narrow no-break space

    return {
        "cases":           _fmt_int(latest["total_cases"]),
        "deaths":          _fmt_int(latest["total_deaths"]),
        "cfr":             f"{latest['cfr_percent']:.2f} %",
        "vaccinated":      f"{latest['people_vaccinated_per_100']:.1f} %",
        "fully":           f"{latest['people_fully_vaccinated_per_100']:.1f} %",
        "last_total_date": latest["date"].strftime("%d %b %Y"),
        "last_daily_date": daily["date"].max().strftime("%d %b %Y"),
    }


def _load_interactive_charts() -> dict[str, str | None]:
    """Load all Plotly HTML files into a dict for template rendering.

    Returns:
        Dict mapping template variable names to HTML strings (or None if missing).
    """
    result: dict[str, str | None] = {}
    for var, path in INTERACTIVE_FILES.items():
        if path.exists():
            result[var] = path.read_text(encoding="utf-8")
        else:
            result[var] = None
            print(f"INFO: {path.name} not found — slide will use static PNG fallback.")
    return result


def _check_figures() -> list[str]:
    """Return names of expected static PNG figures that are missing.

    Returns:
        List of missing file names relative to figures_dir.
    """
    required = [
        "plot01_daily_cases_deaths.png",
        "plot02_7day_incidence.png",
        "plot03_cfr_over_time.png",
        "plot04_vaccination_progress.png",
        "plot05_wave_phases.png",
        "plot06_regression_trend.png",
        "plot07_forecast_two_periods.png",
        "plot08_germany_poland.png",
        "plot09_excess_mortality.png",
        "plot10_variants_heatmap.png",
    ]
    return [name for name in required if not (figures_dir / name).exists()]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Render and save the HTML presentation."""
    missing = _check_figures()
    if missing:
        print(
            "WARNING: the following figures are missing and will appear as "
            "broken images in the presentation:\n"
            + "\n".join(f"  output/figures/{f}" for f in missing)
        )

    stats = _load_stats()
    interactive = _load_interactive_charts()

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=False,   # we embed raw Plotly HTML divs
    )
    template = env.get_template("presentation_template.html")

    html = template.render(
        title="COVID-19 in Germany — DAV Project",
        authors="DAV Project Group",
        course="Data Analysis &amp; Visualisation",
        date="2025",
        stats=stats,
        **interactive,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    presentation_out.write_text(html, encoding="utf-8")
    size_mb = presentation_out.stat().st_size / 1_048_576
    print(f"Saved {presentation_out.relative_to(project_root)}  ({size_mb:.1f} MB)")
    print("Open output/presentation.html in a browser to view the presentation.")
    print(f"Slides: 14  |  Interactive Plotly charts embedded: "
          f"{sum(1 for v in interactive.values() if v is not None)}/4")


if __name__ == "__main__":
    main()
