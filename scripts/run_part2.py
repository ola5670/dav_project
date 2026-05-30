"""Run the Part 2 analysis pipeline (inferential + comparison plots).

Usage::

    python scripts/run_part2.py

Runs plot06 through plot10 in order.  Assumes that processed data already
exists (run scripts/run_part1.py or scripts/01_clean_merge.py first).
"""

import runpy
from pathlib import Path

SCRIPTS = [
    "plot06_regression_trend.py",
    "plot07_forecast_two_periods.py",
    "plot08_germany_poland.py",
    "plot09_excess_mortality.py",
    "plot10_variants_heatmap.py",
]


def main() -> None:
    """Execute the Part 2 plot pipeline."""
    scripts_dir = Path(__file__).resolve().parent
    processed = scripts_dir.parents[0] / "data" / "processed" / "germany_daily.csv"
    if not processed.exists():
        raise FileNotFoundError(
            "Missing data/processed/germany_daily.csv.\n"
            "Run  python scripts/run_part1.py  first."
        )

    for script in SCRIPTS:
        print(f"\n=== Running {script} ===")
        runpy.run_path(str(scripts_dir / script), run_name="__main__")

    print("\n=== All Part 2 plots done ===")


if __name__ == "__main__":
    main()
