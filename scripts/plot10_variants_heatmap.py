"""Plot 10 – Variant dominance stackplot for Germany.

Uses the ECDC variant surveillance CSV (data/raw/ecdc_variants.csv).
Variants with < 2 % peak share are grouped into "Other".
The result is a stacked area chart showing the weekly percentage of each
variant among sequenced samples.
"""

import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/covid19-germany-matplotlib")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from utils import apply_style, data_raw, palette, save_figure

# Colour palette for major variants (WHO Greek-letter / Pango lineage)
VARIANT_COLORS = {
    "B.1.1.7": "#0072B2",  # Alpha
    "B.1.351": "#E69F00",  # Beta
    "P.1": "#009E73",  # Gamma
    "B.1.617.2": "#D55E00",  # Delta
    "B.1.1.529": "#CC79A7",  # Omicron (root)
    "BA.1": "#56B4E9",  # Omicron BA.1
    "BA.2": "#F0E442",  # Omicron BA.2
    "BA.4": "#999999",  # Omicron BA.4
    "BA.5": "#0072B2",  # Omicron BA.5 (reuse hue)
    "BA.2.75": "#D55E00",
    "BA.2.86": "#009E73",
    "BQ.1": "#E69F00",
    "XBB.1.5-like": "#CC79A7",
    "XBB.1.5-like+F456L": "#56B4E9",
    "Other": "#CCCCCC",
}

MIN_PEAK_SHARE = 2.0  # variants below this max share are folded into Other


def _parse_week(year_week: pd.Series) -> pd.Series:
    """Convert 'YYYY-WW' strings to Monday date of that ISO week.

    Args:
        year_week: Series of strings in 'YYYY-WW' format.

    Returns:
        Series of pandas Timestamps.
    """
    return pd.to_datetime(year_week + "-1", format="%Y-%W-%w")


def main() -> None:
    """Generate the variant dominance stackplot."""
    path = data_raw / "ecdc_variants.csv"
    if not path.exists():
        print(f"{path} not found — skipping plot10.")
        return

    raw = pd.read_csv(path)
    de = raw[raw["country"] == "Germany"].copy()

    # Keep GISAID source (more complete) where both exist
    if "GISAID" in de["source"].values:
        de = de[de["source"] == "GISAID"]

    de = de[de["valid_denominator"] == True].copy()
    de["week_date"] = _parse_week(de["year_week"])
    de = de[de["week_date"] >= "2020-12-01"].copy()

    # Pivot to wide format: rows = weeks, cols = variants
    pivot = de.pivot_table(
        index="week_date",
        columns="variant",
        values="percent_variant",
        aggfunc="sum",
    ).fillna(0)

    # Drop the generic "Other" column temporarily – we'll recompute it
    if "Other" in pivot.columns:
        pivot = pivot.drop(columns=["Other"])

    # Remove variants whose peak share never reaches MIN_PEAK_SHARE
    peak = pivot.max(axis=0)
    major = peak[peak >= MIN_PEAK_SHARE].index.tolist()
    minor_sum = pivot.drop(columns=major, errors="ignore").sum(axis=1)

    plot_df = pivot[major].copy()
    plot_df["Other"] = minor_sum

    # Normalise rows to 100 % (deal with rounding / missing weeks)
    row_sum = plot_df.sum(axis=1).replace(0, float("nan"))
    plot_df = plot_df.div(row_sum, axis=0).fillna(0) * 100

    # Order columns: most-dominant first (by total area), Other last
    col_order = plot_df.drop(columns="Other").sum().sort_values(
        ascending=False
    ).index.tolist() + ["Other"]
    plot_df = plot_df[col_order]

    colors = [VARIANT_COLORS.get(c, "#AAAAAA") for c in col_order]

    fig, ax = plt.subplots(figsize=(18, 9))

    ax.stackplot(
        plot_df.index,
        [plot_df[c] for c in col_order],
        labels=col_order,
        colors=colors,
        alpha=0.90,
        linewidth=0.3,
        edgecolor="white",
    )

    apply_style(ax, "SARS-CoV-2 variant dominance in Germany", date_axis=True)
    ax.set_ylabel("Share of sequenced samples (%)")
    ax.set_xlabel("Date")
    ax.set_ylim(0, 100)
    ax.set_xlim(plot_df.index.min(), plot_df.index.max())

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # Legend outside to the right
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles[::-1],
        labels[::-1],
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        fontsize=12,
        frameon=True,
        framealpha=0.92,
    )

    fig.tight_layout()
    save_figure(fig, "plot10_variants_heatmap")


if __name__ == "__main__":
    main()
