"""
Data layer: tries live yfinance first, falls back to synthetic GBM data
when network is unavailable (e.g. sandboxed CI environments).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Realistic calibrated parameters (annualised) for each ticker
# Based on approximate 2018-2026 historical behaviour
_GBM_PARAMS = {
    "SPY":     {"mu": 0.12,  "sigma": 0.17, "start": 260.0},
    "TLT":     {"mu": -0.02, "sigma": 0.14, "start": 122.0},
    "BTC-USD": {"mu": 0.40,  "sigma": 0.80, "start": 13_000.0},
    "QQQ":     {"mu": 0.15,  "sigma": 0.20, "start": 155.0},
}


def _gbm_series(ticker: str, dates: pd.DatetimeIndex) -> pd.Series:
    p = _GBM_PARAMS.get(ticker, {"mu": 0.10, "sigma": 0.20, "start": 100.0})
    n = len(dates)
    dt = 1 / 252
    rng = np.random.default_rng(seed=hash(ticker) % (2**32))
    drift = (p["mu"] - 0.5 * p["sigma"] ** 2) * dt
    shock = p["sigma"] * np.sqrt(dt) * rng.standard_normal(n)
    log_ret = drift + shock
    prices = p["start"] * np.exp(np.cumsum(log_ret))
    return pd.Series(prices, index=dates, name=ticker)


def _trading_days(start: str) -> pd.DatetimeIndex:
    end = datetime.today()
    all_days = pd.bdate_range(start=start, end=end)
    return all_days


def fetch_prices(ticker: str, start: str, offline: bool = False) -> pd.Series:
    if not offline:
        try:
            import yfinance as yf
            df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
            if df.empty:
                raise ValueError("empty")
            s = df["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.squeeze()
            return s.dropna().rename(ticker)
        except Exception:
            pass  # fall through to synthetic
    dates = _trading_days(start)
    return _gbm_series(ticker, dates)
