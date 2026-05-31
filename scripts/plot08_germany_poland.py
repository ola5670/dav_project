"""Plot 08 - Germany vs Poland: 7-day incidence and deaths per 100k.

Produces an interactive Plotly figure with two facets (cases / deaths)
saved as a self-contained HTML file for the presentation, and a static
PNG + SVG via matplotlib for the poster.
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from utils import (
    add_event_annotations,
    apply_style,
    axis_limits,
    data_processed,
    figures_dir,
    number_formatter,
    palette,
    phase_colors,
    project_root,
    save_figure,
    save_plotly_html,
    wave_periods,
)

HTML_OUT = (
    project_root / "output" / "figures" / "plot08_germany_poland_interactive.html"
)

COUNTRY_COLORS = {
    "Germany": palette["cases"],
    "Poland": palette["deaths"],
}


def _load_compare() -> pd.DataFrame:
    """Load and validate the Germany-Poland comparison CSV.

    Returns:
        DataFrame with columns: date, location, incidence_7day_per_100k,
        deaths_7day_per_100k.

    Raises:
        FileNotFoundError: If the processed CSV is missing.
    """
    path = data_processed / "germany_poland_compare.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run scripts/01_clean_merge.py first."
        )
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[df["date"] >= "2020-02-01"].copy()
    return df


def _build_plotly(df: pd.DataFrame) -> None:
    """Save an animated racing bar-chart HTML (7-day incidence per 100k).

    Each frame is one week.  Bars are sorted by value so Germany and Poland
    swap positions whenever their incidence ranking changes.  A Play/Pause
    button and a date slider let the viewer control the animation.

    Args:
        df: Comparison DataFrame with both countries.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("plotly not installed – skipping interactive HTML output.")
        return

    metric = "incidence_7day_per_100k"
    metric_label = "7-day incidence per 100 000"

    df_anim = df[df["date"] >= "2020-03-01"].copy()

    # Sample every 7 days → ~240 frames for 2020-2024
    all_dates = sorted(df_anim["date"].unique())
    sampled = [d for i, d in enumerate(all_dates) if i % 7 == 0]

    # Fixed x-axis range so bars don't cause scale jumps
    x_max = df_anim[metric].max(skipna=True) * 1.12

    bar_colors = {c: col for c, col in COUNTRY_COLORS.items()}

    def _frame_data(date):
        sub = df_anim[df_anim["date"] == date][["location", metric]].copy()
        sub[metric] = sub[metric].fillna(0)
        sub = sub.sort_values(metric, ascending=True)  # ascending → top bar = winner
        countries = sub["location"].tolist()
        values = sub[metric].tolist()
        colors = [bar_colors.get(c, "#888") for c in countries]
        labels = [f"  {v:.1f}" for v in values]
        return countries, values, colors, labels

    # All-time peak per country
    peaks = {}
    for country in COUNTRY_COLORS:
        sub = df_anim[df_anim["location"] == country]
        if sub[metric].notna().any():
            peak_idx = sub[metric].idxmax()
            peaks[country] = {
                "value": float(sub.loc[peak_idx, metric]),
                "date": str(sub.loc[peak_idx, "date"])[:10],
            }
    peak_dates = {c: info["date"] for c, info in peaks.items()}

    peak_annotations_by_country = {
        c: {
            "x": 0.99,
            "y": 0.99 - i * 0.30,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "right",
            "yanchor": "top",
            "text": (
                f"<b>★ Peak {c}</b><br>"
                f"{info['value']:.0f} per 100 000<br>"
                f"<span style='font-size:10px'>{info['date']}</span>"
            ),
            "font": {"size": 12, "color": COUNTRY_COLORS[c]},
            "showarrow": False,
            "bgcolor": "rgba(255,255,255,0.92)",
            "borderpad": 5,
            "bordercolor": COUNTRY_COLORS[c],
            "borderwidth": 2,
        }
        for i, (c, info) in enumerate(peaks.items())
    }

    frames = []
    for date in sampled:
        fc, fv, fcolors, flabels = _frame_data(date)
        date_str = str(date)[:10]

        bar_line_colors = [
            "#FFD700" if peak_dates.get(c) == date_str else "white"
            for c in fc
        ]
        bar_line_widths = [
            3 if peak_dates.get(c) == date_str else 0.5
            for c in fc
        ]

        is_peak = any(info["date"] == date_str for info in peaks.values())
        repeats = 4 if is_peak else 1

        peak_annots = [
            peak_annotations_by_country[c]
            for c, info in peaks.items()
            if info["date"] == date_str
        ]

        for r in range(repeats):
            frame_name = date_str if r == 0 else f"{date_str}_{r}"
            # Peak annotation shows only in the first freeze frame, then disappears forever
            frame_annots = peak_annots if r == 0 else []
            frames.append(
                go.Frame(
                    data=[
                        go.Bar(
                            x=fv,
                            y=fc,
                            orientation="h",
                            marker_color=fcolors,
                            marker_line_color=bar_line_colors,
                            marker_line_width=bar_line_widths,
                            text=flabels,
                            textposition="outside",
                            cliponaxis=False,
                            hovertemplate="<b>%{y}</b><br>"
                            + metric_label
                            + ": %{x:.1f}<extra></extra>",
                        )
                    ],
                    name=frame_name,
                    layout=go.Layout(
                        annotations=[
                            {
                                "x": 0.99,
                                "y": 0.08,
                                "xref": "paper",
                                "yref": "paper",
                                "xanchor": "right",
                                "yanchor": "bottom",
                                "text": f"<b>{date_str}</b>",
                                "font": {"size": 20, "color": "#9CA3AF"},
                                "showarrow": False,
                            }
                        ] + frame_annots
                    ),
                )
            )

    init_countries, init_values, init_colors, init_labels = _frame_data(sampled[0])
    init_date_str = str(sampled[0])[:10]

    fig = go.Figure(
        data=[
            go.Bar(
                x=init_values,
                y=init_countries,
                orientation="h",
                marker_color=init_colors,
                marker_line_color="white",
                marker_line_width=0.5,
                text=init_labels,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>"
                + metric_label
                + ": %{x:.1f}<extra></extra>",
            )
        ],
        frames=frames,
    )

    # Slider: show label only every 8th step (~every 2 months) to avoid overlap
    # Only one slider step per unique date — repeated frames share the same step,
    # so the slider dot stays still during a freeze.
    unique_steps = []
    for f in frames:
        if "_" not in f.name:  # r=0 frames have plain "YYYY-MM-DD" names
            unique_steps.append({
                "args": [
                    [f.name],
                    {
                        "frame": {"duration": 120, "redraw": True},
                        "mode": "immediate",
                        "transition": {"duration": 80},
                    },
                ],
                "label": f.name[:7] if len(unique_steps) % 26 == 0 else "",
                "method": "animate",
            })
    slider_steps = unique_steps

    fig.update_layout(
        title={
            "text": "COVID-19 Race: Germany vs Poland — weekly incidence per 100 000",
            "font": {"size": 17, "color": "#111827"},
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis={
            "title": metric_label,
            "range": [0, x_max],
            "showgrid": True,
            "gridcolor": "#E5E7EB",
        },
        yaxis={
            "tickfont": {"size": 16, "color": "#111827"},
            "automargin": True,
        },
        height=420,
        autosize=True,
        template="plotly_white",
        showlegend=False,
        margin={"l": 20, "r": 80, "t": 70, "b": 110},
        annotations=[
            {
                "x": 0.99,
                "y": 0.08,
                "xref": "paper",
                "yref": "paper",
                "xanchor": "right",
                "yanchor": "bottom",
                "text": f"<b>{init_date_str}</b>",
                "font": {"size": 20, "color": "#9CA3AF"},
                "showarrow": False,
            }
        ],
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0.5,
                "y": -0.28,
                "xanchor": "center",
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "▶  Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 120, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 80, "easing": "linear"},
                            },
                        ],
                    },
                    {
                        "label": "⏸  Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "steps": slider_steps,
                "x": 0.0,
                "len": 1.0,
                "currentvalue": {
                    "prefix": "Week: ",
                    "font": {"size": 12},
                    "xanchor": "center",
                    "visible": True,
                    "offset": 10,
                },
                "tickcolor": "white",  # hide individual tick marks
                "minorticklen": 0,
                "ticklen": 0,
                "pad": {"b": 5, "t": 40},
                "transition": {"duration": 80},
                "bgcolor": "#E5E7EB",
                "bordercolor": "#9CA3AF",
                "borderwidth": 1,
            }
        ],
    )

    # Ensure the figure starts at frame 0 (first week of first wave)
    fig.update(layout_sliders=[{"active": 0}])

    save_plotly_html(fig, HTML_OUT)


def _build_static(df: pd.DataFrame) -> None:
    """Save a static matplotlib PNG.

    Args:
        df: Comparison DataFrame with both countries.
    """
    fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
    fig.suptitle(
        "COVID-19: Germany vs Poland (2020-2024)",
        fontsize=30,
        fontweight="bold",
        color=palette["slate"],
        y=1.01,
    )

    metrics = [
        (
            "incidence_7day_per_100k",
            "7-day incidence per 100 000",
            axis_limits["incidence_per_100k"],
        ),
        (
            "deaths_7day_per_100k",
            "7-day deaths per 100 000",
            axis_limits["deaths_per_100k"],
        ),
    ]

    for ax, (col, ylabel, ylim) in zip(axes, metrics):
        for name, (start, end) in wave_periods.items():
            ax.axvspan(
                pd.Timestamp(start),
                pd.Timestamp(end),
                color=phase_colors[name],
                alpha=0.36,
                linewidth=0,
                zorder=0,
            )

        for country, color in COUNTRY_COLORS.items():
            sub = df[df["location"] == country].sort_values("date")
            valid = sub.dropna(subset=[col])

            ax.plot(
                valid["date"],
                valid[col],
                color=color,
                linewidth=3.0,
                label=country,
                zorder=3,
            )

            ax.fill_between(
                valid["date"],
                valid[col],
                0,
                color=color,
                alpha=0.16,
                zorder=2,
            )

        apply_style(ax, date_axis=True)
        ax.set_ylim(*ylim)
        ax.set_xlim(pd.Timestamp("2020-02-01"), df["date"].max())
        ax.set_ylabel(ylabel)
        ax.yaxis.set_major_formatter(number_formatter())
        add_event_annotations(ax, ymax_fraction=0.95)
        ax.legend(fontsize=15)

    axes[1].set_xlabel("Date")

    fig.tight_layout(rect=[0, 0.035, 1, 0.96], h_pad=3.0)
    save_figure(fig, "plot08_germany_poland")


def main() -> None:
    """Generate Germany vs Poland comparison figures (static + interactive)."""
    df = _load_compare()
    _build_static(df)
    _build_plotly(df)


if __name__ == "__main__":
    main()
