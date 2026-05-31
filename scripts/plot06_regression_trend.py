"""Plot 06 - Doubling time per pandemic wave.

For each wave the growth phase (first 40 % of days) is fitted with an
OLS regression on log(new_cases_7day) to estimate the exponential growth
rate.  The doubling time T₂ = log(2) / slope is shown as a horizontal
bar chart — shorter bar means faster-spreading wave.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from scipy import stats

from utils import (
    apply_style,
    figures_dir,
    load_germany_daily,
    palette,
    save_figure,
    save_plotly_html,
    wave_periods,
)

INTERACTIVE_OUT = figures_dir / "plot06_regression_interactive.html"

# Waves used for regression (skip the final "Decline" plateau if present)
REGRESSION_WAVES = [k for k in wave_periods if k != "Decline"]

WAVE_COLORS = [
    palette["cases"],
    palette["deaths"],
    palette["vaccination"],
    palette["boosters"],
    "#E69F00",
]

X_AXIS_LIMIT = 150

# Reference lines
REF_FAST     = 7   # days  — "very fast"
REF_MODERATE = 14  # days  — "moderate"


def _fit_wave(
    df: pd.DataFrame, start: str, end: str, growth_fraction: float = 0.40
) -> tuple[float, float]:
    """Fit OLS on log(cases) for the growth phase of one wave.

    Args:
        df: Daily Germany DataFrame with date and new_cases_7day columns.
        start: Wave start date string (YYYY-MM-DD).
        end: Wave end date string (YYYY-MM-DD).
        growth_fraction: Fraction of wave days used as the growth phase.

    Returns:
        Tuple of (slope, intercept).  Returns (nan, nan) when data are
        insufficient or the wave is not growing.
    """
    mask = (df["date"] >= start) & (df["date"] <= end) & df["new_cases_7day"].gt(0)
    sub = df.loc[mask].copy()
    if len(sub) < 10:
        return float("nan"), float("nan")

    sub["day_num"] = (sub["date"] - sub["date"].iloc[0]).dt.days
    sub["log_cases"] = np.log(sub["new_cases_7day"])

    n_growth = max(10, int(len(sub) * growth_fraction))
    growth = sub.iloc[:n_growth]

    slope, intercept, *_ = stats.linregress(growth["day_num"], growth["log_cases"])
    return slope, intercept


def _collect_results(df: pd.DataFrame) -> list[dict]:
    """Compute slope and doubling time for every regression wave.

    Args:
        df: Daily Germany DataFrame.

    Returns:
        List of dicts with keys: wave, start, end, slope, doubling.
        Only waves with positive slope (growing phase) are included.
    """
    results = []
    for wave_name, (start, end) in wave_periods.items():
        if wave_name not in REGRESSION_WAVES:
            continue
        slope, _ = _fit_wave(df, start, end)
        if np.isnan(slope) or slope <= 0:
            continue
        doubling = np.log(2) / slope
        results.append({
            "wave":     wave_name,
            "start":    start,
            "end":      end,
            "slope":    slope,
            "doubling": doubling,
        })
    return results


def main() -> None:
    """Generate the doubling-time figure (static + interactive)."""
    df = load_germany_daily()
    results = _collect_results(df)

    if not results:
        print("No waves with positive growth slope found – skipping plot06.")
        return

    wave_names  = [r["wave"]     for r in results]
    doublings   = [r["doubling"] for r in results]
    slopes      = [r["slope"]    for r in results]
    colors      = [WAVE_COLORS[i % len(WAVE_COLORS)] for i in range(len(results))]

    fig, ax = plt.subplots(figsize=(18, max(7, len(results) * 1.4)))
    fig.suptitle(
        "Doubling Time of 7-Day Case Count",
        fontsize=30,
        fontweight="bold",
        color=palette["slate"],
        y=1.03,
    )

    bars = ax.barh(
        wave_names,
        doublings,
        color=colors,
        height=0.55,
        edgecolor="white",
        linewidth=0.8,
    )

    # Inline value labels
    for bar, d in zip(bars, doublings):
        ax.text(
            bar.get_width() + 0.4,
            bar.get_y() + bar.get_height() / 2,
            f"{d:.0f} d",
            va="center",
            ha="left",
            fontsize=14,
            color=palette["slate"],
        )

    # Reference lines
    ax.axvline(REF_FAST, color="#E69F00", linestyle="--", linewidth=1.6)
    ax.axvline(REF_MODERATE, color=palette["vaccination"], linestyle="--", linewidth=1.6)

    xform = ax.get_xaxis_transform()
    ax.text(REF_FAST, -0.04, str(REF_FAST), transform=xform,
            ha="center", va="top", fontsize=12, color="#E69F00", fontweight="bold")
    ax.text(REF_MODERATE, -0.04, str(REF_MODERATE), transform=xform,
            ha="center", va="top", fontsize=12, color=palette["vaccination"], fontweight="bold")

    ax.set_xlabel("Doubling time (days)")
    ax.set_xlim(0, X_AXIS_LIMIT)
    ax.invert_yaxis()   # top = earliest wave
    apply_style(ax, date_axis=False)
    fig.tight_layout()
    save_figure(fig, "plot06_regression_trend")

    _build_plotly(results)


def _build_plotly(results: list[dict]) -> None:
    """Save an interactive Plotly HTML horizontal bar chart.

    Args:
        results: List of wave dicts from _collect_results().
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("plotly not installed – skipping interactive HTML for plot06.")
        return

    wave_names = [r["wave"]     for r in results]
    doublings  = [r["doubling"] for r in results]
    slopes     = [r["slope"]    for r in results]
    colors     = [WAVE_COLORS[i % len(WAVE_COLORS)] for i in range(len(results))]
    periods    = [f"{r['start']} – {r['end']}" for r in results]

    hover_texts = [
        f"<b>{w}</b><br>"
        f"Period: {p}<br>"
        f"Doubling time: <b>{d:.1f} days</b><br>"
        f"Growth rate: {s:.4f} day⁻¹"
        for w, p, d, s in zip(wave_names, periods, doublings, slopes)
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=doublings,
        y=wave_names,
        orientation="h",
        marker_color=colors,
        marker_line_color="white",
        marker_line_width=0.8,
        text=[f"<b>{d:.0f} d</b>" for d in doublings],
        textposition="outside",
        cliponaxis=False,
        customdata=hover_texts,
        hovertemplate="%{customdata}<extra></extra>",
    ))

    # Reference lines
    x_max = max(doublings) * 1.22
    for val, color in [
        (REF_FAST, "#E69F00"),
        (REF_MODERATE, "#009E73"),
    ]:
        fig.add_vline(x=val, line_dash="dash", line_color=color, line_width=1.8)
        fig.add_annotation(
            x=val, xref="x",
            y=0, yref="paper",
            yanchor="top", yshift=-28,
            text=f"<b>{val}</b>",
            showarrow=False,
            font={"size": 13, "color": color},
        )

    fig.update_layout(
        title={
            "text": "How fast did each wave grow? — Doubling time per wave",
            "font": {"size": 17, "color": "#111827"},
            "x": 0.5, "xanchor": "center",
        },
        xaxis={
            "title": "Doubling time (days)",
            "range": [0, x_max],
            "showgrid": True,
            "gridcolor": "#E5E7EB",
        },
        yaxis={
            "autorange": "reversed",
            "tickfont": {"size": 14},
        },
        height=420,
        autosize=True,
        template="plotly_white",
        showlegend=False,
        margin={"l": 20, "r": 80, "t": 70, "b": 50},
    )

    save_plotly_html(fig, INTERACTIVE_OUT)


if __name__ == "__main__":
    main()
