import numpy as np
import pandas as pd

from utils import (
    data_processed,
    data_raw,
    end_date,
    germany_iso,
    poland_iso,
    start_date,
    wave_periods,
)

owid_columns = [
    "iso_code",
    "continent",
    "location",
    "date",
    "population",
    "total_cases",
    "new_cases",
    "total_deaths",
    "new_deaths",
    "icu_patients",
    "hosp_patients",
    "people_vaccinated",
    "people_fully_vaccinated",
    "total_boosters",
    "reproduction_rate",
    "stringency_index",
    "excess_mortality",
]


def require_csv(path: str) -> None:
    """Validate that a local raw data file can be used as a CSV.

    Args:
        path: File name inside the raw data directory.

    Raises:
        FileNotFoundError: If the file is missing.
        RuntimeError: If the file looks like an HTML page instead of a CSV file.
    """
    file_path = data_raw / path
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} is missing.")
    first_bytes = file_path.read_bytes()[:100].lower()
    if b"<!doctype html" in first_bytes or b"<html" in first_bytes:
        raise RuntimeError(
            f"{file_path} looks like HTML, not CSV. Download the raw CSV again."
        )


def add_wave_labels(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    """Add pandemic phase labels based on fixed date ranges.

    Args:
        df: Data frame with a date column.
        date_column: Name of the column used to assign phases.

    Returns:
        A copy of the input data frame with a new `wave` column.
    """
    labelled = df.copy()
    labelled["wave"] = "Outside defined waves"
    for wave, (start, end) in wave_periods.items():
        inside_wave = labelled[date_column].between(
            pd.Timestamp(start), pd.Timestamp(end)
        )
        labelled.loc[inside_wave, "wave"] = wave
    return labelled


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Create indicators used by the plots and later analysis.

    Args:
        df: Filtered OWID data for Germany and Poland.

    Returns:
        Data frame with cleaned daily values, rolling rates, CFR, vaccination
        indicators and pandemic phase labels.
    """
    df = df.sort_values(["iso_code", "date"]).copy()
    cumulative_cols = [
        "total_cases",
        "total_deaths",
        "people_vaccinated",
        "people_fully_vaccinated",
        "total_boosters",
    ]
    for col in cumulative_cols:
        if col in df:
            df[col] = df.groupby("iso_code")[col].ffill()

    df["new_cases_clean"] = df["new_cases"].clip(lower=0)
    df["new_deaths_clean"] = df["new_deaths"].clip(lower=0)
    df["new_cases_7day"] = df.groupby("iso_code")["new_cases_clean"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["new_deaths_7day"] = df.groupby("iso_code")["new_deaths_clean"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["incidence_7day_per_100k"] = (
        df.groupby("iso_code")["new_cases_clean"].transform(
            lambda s: s.rolling(7, min_periods=1).sum()
        )
        / df["population"]
        * 100_000
    )
    df["deaths_7day_per_100k"] = (
        df.groupby("iso_code")["new_deaths_clean"].transform(
            lambda s: s.rolling(7, min_periods=1).sum()
        )
        / df["population"]
        * 100_000
    )
    df["cfr_percent"] = np.where(
        df["total_cases"] > 0,
        df["total_deaths"] / df["total_cases"] * 100,
        np.nan,
    )
    df["new_cases_log"] = np.log1p(df["new_cases_7day"])
    df["people_vaccinated_per_100"] = df["people_vaccinated"] / df["population"] * 100
    df["people_fully_vaccinated_per_100"] = (
        df["people_fully_vaccinated"] / df["population"] * 100
    )
    df["boosters_per_100"] = df["total_boosters"] / df["population"] * 100
    return add_wave_labels(df, "date")


def build_weekly(germany_daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily Germany data to weekly values.

    Args:
        germany_daily: Processed daily data for Germany.

    Returns:
        Weekly data set used for later comparisons, regressions and forecasts.
    """
    numeric_cols = [
        "new_cases_clean",
        "new_deaths_clean",
        "new_cases_7day",
        "new_deaths_7day",
        "incidence_7day_per_100k",
        "cfr_percent",
        "people_vaccinated_per_100",
        "people_fully_vaccinated_per_100",
        "boosters_per_100",
        "hosp_patients",
        "icu_patients",
        "excess_mortality",
    ]
    weekly = (
        germany_daily.set_index("date")[numeric_cols]
        .resample("W-SUN")
        .agg(
            {
                "new_cases_clean": "sum",
                "new_deaths_clean": "sum",
                "new_cases_7day": "mean",
                "new_deaths_7day": "mean",
                "incidence_7day_per_100k": "mean",
                "cfr_percent": "mean",
                "people_vaccinated_per_100": "last",
                "people_fully_vaccinated_per_100": "last",
                "boosters_per_100": "last",
                "hosp_patients": "mean",
                "icu_patients": "mean",
                "excess_mortality": "mean",
            }
        )
        .reset_index()
        .rename(columns={"date": "week"})
    )
    return add_wave_labels(weekly, "week")


def main() -> None:
    """Create the processed data files used in the project.

    The script reads the OWID data, keeps Germany and Poland, adds the derived
    indicators needed by the plots, and saves daily, weekly and comparison CSV files.
    """
    data_processed.mkdir(parents=True, exist_ok=True)
    require_csv("owid_covid_data.csv")
    raw = pd.read_csv(
        data_raw / "owid_covid_data.csv",
        usecols=owid_columns,
        parse_dates=["date"],
    )
    selected = raw[
        raw["iso_code"].isin([germany_iso, poland_iso])
        & (raw["date"] >= start_date)
        & (raw["date"] <= end_date)
    ].copy()
    selected = add_derived_columns(selected)

    germany_daily = selected[selected["iso_code"] == germany_iso].copy()
    compare_daily = selected[
        selected["iso_code"].isin([germany_iso, poland_iso])
    ].copy()
    germany_weekly = build_weekly(germany_daily)

    germany_daily.to_csv(data_processed / "germany_daily.csv", index=False)
    germany_weekly.to_csv(data_processed / "germany_weekly.csv", index=False)
    compare_daily.to_csv(data_processed / "germany_poland_compare.csv", index=False)

    print(f"Wrote {data_processed / 'germany_daily.csv'}")
    print(f"Wrote {data_processed / 'germany_weekly.csv'}")
    print(f"Wrote {data_processed / 'germany_poland_compare.csv'}")


if __name__ == "__main__":
    main()
