"""
Michael Gayed 200-SMA strategy extended for a stocks + Bitcoin portfolio.

Stock sleeve (50%):
  SPY above 200 SMA  → hold SPY  (risk-on)
  SPY below 200 SMA  → hold TLT  (risk-off / bonds)

BTC sleeve (50%):
  BTC above 200 SMA  → hold BTC
  BTC below 200 SMA  → hold cash (0% return, capital preservation)
"""

import pandas as pd
from datetime import datetime, timedelta
from config import SMA_PERIOD


def get_signal(ticker: str, period: int = SMA_PERIOD, offline: bool = False) -> dict:
    from data import fetch_prices
    # calendar days needed: trading days ≈ calendar days * 5/7, so multiply by 1.5 + buffer
    calendar_days = int(period * 1.5) + 90
    start = (datetime.today() - timedelta(days=calendar_days)).strftime("%Y-%m-%d")
    close = fetch_prices(ticker, start=start, offline=offline)

    if len(close) < period:
        raise ValueError(f"Not enough data for {ticker} ({len(close)} days, need {period})")

    sma = close.rolling(period).mean()
    price = float(close.iloc[-1])
    sma_val = float(sma.iloc[-1])
    pct = (price - sma_val) / sma_val * 100

    prev_price = float(close.iloc[-2])
    prev_sma = float(sma.iloc[-2])
    crossed_above = (prev_price < prev_sma) and (price >= sma_val)
    crossed_below = (prev_price > prev_sma) and (price <= sma_val)

    return {
        "ticker": ticker,
        "price": price,
        "sma200": sma_val,
        "pct_vs_sma": pct,
        "signal": "RISK_ON" if price > sma_val else "RISK_OFF",
        "crossed_above": crossed_above,
        "crossed_below": crossed_below,
        "as_of": close.index[-1].date(),
        "live": not offline,
    }


def current_allocation(spy_signal: dict, btc_signal: dict) -> dict:
    from config import STOCK_TICKER, DEFENSIVE_TICKER, BTC_TICKER, STOCK_ALLOCATION, BTC_ALLOCATION
    stock_pos = STOCK_TICKER if spy_signal["signal"] == "RISK_ON" else DEFENSIVE_TICKER
    btc_pos = BTC_TICKER if btc_signal["signal"] == "RISK_ON" else "CASH"
    return {
        "stock_sleeve": {"ticker": stock_pos, "weight": STOCK_ALLOCATION},
        "btc_sleeve": {"ticker": btc_pos, "weight": BTC_ALLOCATION},
    }
