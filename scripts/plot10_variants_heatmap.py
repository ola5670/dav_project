"""Plot 10 – Variant dominance stackplot for Germany.

Uses the ECDC variant surveillance CSV (data/raw/ecdc_variants.csv).
Variants are grouped by WHO variant family (Alpha, Beta/Gamma, Delta,
Omicron sub-lineages) to keep the chart readable.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from utils import apply_style, data_raw, figures_dir, save_figure, save_plotly_html

INTERACTIVE_OUT = figures_dir / "plot10_variants_interactive.html"

VARIANT_GROUPS = {
    "Alpha (B.1.1.7)":          ["B.1.1.7"],
    "Beta / Gamma":              ["B.1.351", "P.1"],
    "Delta (B.1.617.2)":        ["B.1.617.2"],
    "Omicron BA.1":              ["B.1.1.529", "BA.1"],
    "Omicron BA.2":              ["BA.2", "BA.2.75", "BA.2.86"],
    "Omicron BA.4 / BA.5":      ["BA.4", "BA.5"],
    "Late Omicron (BQ / XBB)":  ["BQ.1", "XBB.1.5-like", "XBB.1.5-like+F456L"],
}

GROUP_COLORS = {
    "Alpha (B.1.1.7)":          "#5B9EC9",   # muted blue
    "Beta / Gamma":              "#E8B96A",   # muted amber
    "Delta (B.1.617.2)":        "#E07D4B",   # muted orange
    "Omicron BA.1":              "#D49BBF",   # muted pink
    "Omicron BA.2":              "#4AAF96",   # muted green
    "Omicron BA.4 / BA.5":      "#84C8F0",   # muted light blue
    "Late Omicron (BQ / XBB)":  "#C8C068",   # muted olive-yellow
    "Other":                     "#C8C8C8",   # light gray
}


def _parse_week(year_week: pd.Series) -> pd.Series:
    """Convert 'YYYY-WW' strings to Monday date of that ISO week."""
    return pd.to_datetime(year_week + "-1", format="%Y-%W-%w")


def _prepare_data() -> tuple[pd.DataFrame, list[str], list[str]] | None:
    """Load and aggregate ECDC variant data into WHO family groups.

    Returns:
        Tuple of (group_df, col_order, colors) or None if data is missing.
    """
    path = data_raw / "ecdc_variants.csv"
    if not path.exists():
        print(f"{path} not found — skipping plot10.")
        return None

    raw = pd.read_csv(path)
    de = raw[raw["country"] == "Germany"].copy()

    if "GISAID" in de["source"].values:
        de = de[de["source"] == "GISAID"]

    de = de[de["valid_denominator"] == True].copy()
    de["week_date"] = _parse_week(de["year_week"])
    de = de[de["week_date"] >= "2020-12-01"].copy()

    pivot = de.pivot_table(
        index="week_date",
        columns="variant",
        values="percent_variant",
        aggfunc="sum",
    ).fillna(0)

    if "Other" in pivot.columns:
        pivot = pivot.drop(columns=["Other"])

    group_df = pd.DataFrame(index=pivot.index)
    assigned = set()
    for group_name, members in VARIANT_GROUPS.items():
        cols = [c for c in members if c in pivot.columns]
        if cols:
            group_df[group_name] = pivot[cols].sum(axis=1)
            assigned.update(cols)
        else:
            group_df[group_name] = 0.0

    remaining = [c for c in pivot.columns if c not in assigned]
    group_df["Other"] = pivot[remaining].sum(axis=1) if remaining else 0.0

    row_sum = group_df.sum(axis=1).replace(0, float("nan"))
    group_df = group_df.div(row_sum, axis=0).fillna(0) * 100
    group_df = group_df.loc[:, group_df.max() > 0]

    col_order = [g for g in list(VARIANT_GROUPS.keys()) + ["Other"] if g in group_df.columns]
    colors = [GROUP_COLORS.get(c, "#AAAAAA") for c in col_order]

    return group_df, col_order, colors


def _build_static(group_df: pd.DataFrame, col_order: list[str], colors: list[str]) -> None:
    """Save a static matplotlib stackplot PNG."""
    fig, ax = plt.subplots(figsize=(18, 11))

    ax.stackplot(
        group_df.index,
        [group_df[c] for c in col_order],
        labels=col_order,
        colors=colors,
        alpha=0.90,
        linewidth=0.4,
        edgecolor="white",
    )

    apply_style(ax, "SARS-CoV-2 variant dominance in Germany", date_axis=True)
    ax.set_ylabel("Share of sequenced samples (%)")
    ax.set_xlabel("Date")
    ax.set_ylim(0, 100)
    ax.set_xlim(group_df.index.min(), group_df.index.max())

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

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


SHORT_LABELS = {
    "Alpha (B.1.1.7)":          "Alpha",
    "Beta / Gamma":              "Beta/Gamma",
    "Delta (B.1.617.2)":        "Delta",
    "Omicron BA.1":              "Omicron BA.1",
    "Omicron BA.2":              "Omicron BA.2",
    "Omicron BA.4 / BA.5":      "Omicron BA.4/5",
    "Late Omicron (BQ / XBB)":  "Late Omicron",
    "Other":                     "Other",
}


def _build_plotly(group_df: pd.DataFrame, col_order: list[str], colors: list[str]) -> None:
    """Save an interactive Plotly stacked area chart with on-band labels."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("plotly not installed – skipping interactive HTML for plot10.")
        return

    dates = group_df.index.astype(str).tolist()
    fig = go.Figure()

    for group, color in zip(col_order, colors):
        values = group_df[group].round(1).tolist()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            name=SHORT_LABELS.get(group, group),
            stackgroup="one",
            mode="none",
            fillcolor=color,
            line={"width": 0.4, "color": "white"},
            hovertemplate="<b>%{fullData.name}</b><br>%{x}<br>%{y:.1f} %<extra></extra>",
        ))

    # Place text labels directly on each band at its widest point
    dark_bands = {"Late Omicron (BQ / XBB)", "Beta / Gamma", "Omicron BA.4 / BA.5"}
    cumsum = pd.Series(0.0, index=group_df.index)
    for group, color in zip(col_order, colors):
        band_top = cumsum + group_df[group]
        band_mid = (cumsum + band_top) / 2
        peak_date = group_df[group].idxmax()
        peak_pct = group_df.loc[peak_date, group]

        if peak_pct >= 8:
            text_color = "#111827" if group in dark_bands else "white"
            fig.add_annotation(
                x=str(peak_date)[:10],
                y=float(band_mid.loc[peak_date]),
                text=SHORT_LABELS.get(group, group),
                showarrow=False,
                font={"size": 12, "color": text_color, "family": "DejaVu Sans"},
                bgcolor="rgba(255,255,255,0.25)",
                borderpad=3,
            )

        cumsum = band_top

    fig.update_layout(
        title={
            "text": "SARS-CoV-2 variant dominance in Germany",
            "font": {"size": 17, "color": "#111827"},
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis={
            "title": "Date",
            "showgrid": True,
            "gridcolor": "#E5E7EB",
            "tickformat": "%b %Y",
            "nticks": 16,
        },
        yaxis={
            "title": "Share of sequenced samples (%)",
            "range": [0, 100],
            "showgrid": True,
            "gridcolor": "#E5E7EB",
        },
        hovermode="x unified",
        showlegend=False,
        height=480,
        autosize=True,
        template="plotly_white",
        margin={"l": 60, "r": 20, "t": 50, "b": 50},
    )

    save_plotly_html(fig, INTERACTIVE_OUT)


def main() -> None:
    """Generate the variant dominance stackplot (static + interactive)."""
    result = _prepare_data()
    if result is None:
        return
    group_df, col_order, colors = result
    _build_static(group_df, col_order, colors)
    _build_plotly(group_df, col_order, colors)


if __name__ == "__main__":
    main()
