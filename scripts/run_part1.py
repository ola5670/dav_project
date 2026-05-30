import runpy
from pathlib import Path

scripts = [
    "01_clean_merge.py",
    "plot01_daily_cases_deaths.py",
    "plot02_7day_incidence.py",
    "plot03_cfr_over_time.py",
    "plot04_vaccination_progress.py",
    "plot05_wave_phases.py",
]


def main() -> None:
    """Run the current reproducible analysis pipeline.

    The pipeline rebuilds processed data and regenerates all static figures used
    in the current poster version.
    """
    scripts_dir = Path(__file__).resolve().parent
    raw_data = scripts_dir.parents[0] / "data" / "raw" / "owid_covid_data.csv"
    if not raw_data.exists():
        raise FileNotFoundError(
            "Missing data/raw/owid_covid_data.csv.\n"
            "Download it manually using the commands in README.md."
        )

    for script in scripts:
        print(f"\n=== Running {script} ===")
        runpy.run_path(str(scripts_dir / script), run_name="__main__")


if __name__ == "__main__":
    main()
