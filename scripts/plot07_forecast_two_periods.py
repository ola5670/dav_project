"""Plot 07 - Short-term forecasts using Holt-Winters exponential smoothing.

Two separate forecasts are made:
  Period A: training on Wave 2 growth, forecasting 30 days ahead.
  Period B: training on Wave 5 (Omicron) growth, forecasting 30 days ahead.

statsmodels ExponentialSmoothing (Holt-Winters) is used because it is
more robust to the data gaps present in the COVID time series than ARIMA.
A 90 % confidence interval is estimated from the in-sample residual std.
"""
import warnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from utils import (
    apply_style,
    axis_limits,
    load_germany_daily,
    number_formatter,
    palette,
    save_figure,
)

warnings.filterwarnings("ignore")

FORECAST_HORIZON = 30  # days

# (label, training window start, training window end)
PERIODS = [
    ("Wave 2 — 2020/21 winter", "2020-10-01", "2020-12-15"),
    ("Wave 5 — Omicron 2022", "2022-01-01", "2022-03-15"),
]


def _forecast(
    series: pd.Series,
    horizon: int = FORECAST_HORIZON,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Fit Holt-Winters and produce a point forecast with a 90 % CI.

    Args:
        series: Daily smoothed case counts indexed by date.
        horizon: Number of days to forecast ahead.

    Returns:
        Tuple of (point forecast, lower CI bound, upper CI bound) as Series
        indexed by future dates.
    """
    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal=None,
        initialization_method="estimated",
    ).fit(optimized=True)

    forecast = model.forecast(horizon)
    residuals = model.resid
    sigma = residuals.std()
    z = 1.645  # 90 % one-sided
    lower = forecast - z * sigma * np.sqrt(np.arange(1, horizon + 1))
    upper = forecast + z * sigma * np.sqrt(np.arange(1, horizon + 1))
    lower = lower.clip(lower=0)
    return forecast, lower, upper


def main() -> None:
    """Generate the two-period forecast figure."""
    df = load_germany_daily()

    fig, axes = plt.subplots(1, 2, figsize=(22, 10))
    fig.suptitle(
        "Short-Term Forecasts: Holt-Winters Exponential Smoothing",
        fontsize=30,
        fontweight="bold",
        color=palette["slate"],
        y=1.01,
    )

    colors = [palette["cases"], palette["vaccination_alt"]]

    for ax, (label, train_start, train_end), color in zip(axes, PERIODS, colors):
        mask_train = (df["date"] >= train_start) & (df["date"] <= train_end)
        train_df = df.loc[mask_train, ["date", "incidence_7day_per_100k"]].dropna()

        if len(train_df) < 14:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes)
            apply_style(ax, label)
            continue

        series = train_df.set_index("date")["incidence_7day_per_100k"]
        series.index = pd.DatetimeIndex(series.index)

        last_train = series.index[-1]
        future_idx = pd.date_range(
            last_train + pd.Timedelta(days=1), periods=FORECAST_HORIZON, freq="D"
        )

        point, lower, upper = _forecast(series)
        point.index = future_idx
        lower.index = future_idx
        upper.index = future_idx

        actual_end = pd.Timestamp(train_end) + pd.Timedelta(days=FORECAST_HORIZON + 10)
        mask_context = (df["date"] >= pd.Timestamp(train_start) - pd.Timedelta(days=14)) & \
                       (df["date"] <= actual_end)
        ctx = df.loc[mask_context, ["date", "incidence_7day_per_100k"]].dropna()

        ax.plot(
            ctx["date"], ctx["incidence_7day_per_100k"],
            color=palette["neutral"], linewidth=2.2, label="Observed", zorder=3
        )

        # Highlight training window
        ax.axvspan(
            pd.Timestamp(train_start), last_train,
            color=color, alpha=0.07, label="Training window"
        )

        # Forecast + CI
        ax.plot(future_idx, point, color=color, linewidth=2.8, linestyle="--",
                label="Forecast", zorder=4)
        ax.fill_between(
            future_idx, lower, upper,
            color=color, alpha=0.22, label="90 % CI"
        )

        # Vertical divider at forecast start
        ax.axvline(last_train, color=palette["muted"], linewidth=1.2, linestyle=":")

        apply_style(ax, label, date_axis=True)
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        ax.set_ylabel("7-day incidence per 100 000")
        ax.set_ylim(*axis_limits["incidence_per_100k"])
        ax.yaxis.set_major_formatter(number_formatter())
        ax.legend(fontsize=13, loc="upper left")

    fig.tight_layout()
    save_figure(fig, "plot07_forecast_two_periods")


if __name__ == "__main__":
    main()
