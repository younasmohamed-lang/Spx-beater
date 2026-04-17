"""
Backtest: Gayed 200-SMA strategy (SPY+BTC sleeves) vs SPY buy-and-hold.
Avoids lookahead bias by using previous day's SMA signal.
"""

import pandas as pd
import numpy as np
from config import (
    STOCK_TICKER, DEFENSIVE_TICKER, BTC_TICKER,
    SMA_PERIOD, BACKTEST_START, RISK_FREE_RATE, INITIAL_VALUE,
    STOCK_ALLOCATION, BTC_ALLOCATION,
)


def run(start: str = BACKTEST_START, initial: float = INITIAL_VALUE,
        offline: bool = False) -> dict:
    from data import fetch_prices

    spy = fetch_prices(STOCK_TICKER, start=start, offline=offline)
    tlt = fetch_prices(DEFENSIVE_TICKER, start=start, offline=offline)
    btc = fetch_prices(BTC_TICKER, start=start, offline=offline)

    raw = pd.DataFrame({"SPY": spy, "TLT": tlt, "BTC": btc}).dropna()
    raw["SPY_SMA"] = raw["SPY"].rolling(SMA_PERIOD).mean()
    raw["BTC_SMA"] = raw["BTC"].rolling(SMA_PERIOD).mean()
    prices = raw.dropna().copy()

    ret = prices[["SPY", "TLT", "BTC"]].pct_change().dropna()
    prices = prices.loc[ret.index]

    # Previous-day signals (no lookahead)
    spy_on = prices["SPY"].shift(1) > prices["SPY_SMA"].shift(1)
    btc_on = prices["BTC"].shift(1) > prices["BTC_SMA"].shift(1)

    stock_ret = spy_on * ret["SPY"] + (~spy_on) * ret["TLT"]
    btc_ret = btc_on * ret["BTC"]  # cash = 0% when BTC below SMA

    strat_ret = STOCK_ALLOCATION * stock_ret + BTC_ALLOCATION * btc_ret
    bench_ret = ret["SPY"]

    strat_val = (1 + strat_ret).cumprod() * initial
    bench_val = (1 + bench_ret).cumprod() * initial

    n_years = len(strat_ret) / 252

    def cagr(series):
        return (series.iloc[-1] / initial) ** (1 / n_years) - 1

    def max_dd(val_series):
        peak = val_series.cummax()
        return float(((val_series - peak) / peak).min())

    def sharpe(r):
        excess = r - RISK_FREE_RATE / 252
        return float(np.sqrt(252) * excess.mean() / excess.std())

    pct_in_tlt = float((~spy_on).mean() * 100)
    pct_btc_cash = float((~btc_on).mean() * 100)

    return {
        "strat_values": strat_val,
        "bench_values": bench_val,
        "strat_returns": strat_ret,
        "bench_returns": bench_ret,
        "n_years": n_years,
        "pct_in_tlt": pct_in_tlt,
        "pct_btc_cash": pct_btc_cash,
        "live": not offline,
        "strategy": {
            "final_value": float(strat_val.iloc[-1]),
            "total_return_pct": float((strat_val.iloc[-1] / initial - 1) * 100),
            "cagr": float(cagr(strat_val)),
            "max_drawdown": max_dd(strat_val),
            "sharpe": sharpe(strat_ret),
        },
        "benchmark": {
            "final_value": float(bench_val.iloc[-1]),
            "total_return_pct": float((bench_val.iloc[-1] / initial - 1) * 100),
            "cagr": float(cagr(bench_val)),
            "max_drawdown": max_dd(bench_val),
            "sharpe": sharpe(bench_ret),
        },
    }
