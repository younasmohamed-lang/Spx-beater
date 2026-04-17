#!/usr/bin/env python3
"""
SPX-Beater Portfolio Manager
Portfolio: $10k for a 6-year-old (target age 18 = 12-year horizon)
Strategy : Michael Gayed 200-SMA + BTC 200-SMA sleeves
"""

import argparse
import numpy as np

from config import (
    INITIAL_VALUE, STOCK_ALLOCATION, BTC_ALLOCATION,
    STOCK_TICKER, DEFENSIVE_TICKER, BTC_TICKER,
    YEARS_TO_TARGET, CURRENT_AGE, TARGET_AGE, BACKTEST_START,
)
from strategy import get_signal, current_allocation

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# ── formatting helpers ────────────────────────────────────────────────────────

def _tbl(rows, headers):
    if HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="rounded_outline", floatfmt=".2f")
    lines = ["  ".join(str(h).ljust(18) for h in headers)]
    lines.append("-" * (20 * len(headers)))
    for r in rows:
        lines.append("  ".join(str(c).ljust(18) for c in r))
    return "\n".join(lines)


def _pct(v):
    return f"{v:+.2f}%"


def _dollar(v):
    return f"${v:,.0f}"


def _bar(v, total=20, width=25):
    filled = int(round(min(abs(v), total) / total * width))
    return "█" * filled + "░" * (width - filled)


# ── sections ──────────────────────────────────────────────────────────────────

def section_signals(offline: bool):
    print("\n" + "=" * 62)
    print("  CURRENT MARKET SIGNALS  (Michael Gayed 200-SMA)")
    if offline:
        print("  [DEMO MODE — synthetic data, not live prices]")
    print("=" * 62)

    spy_sig = get_signal(STOCK_TICKER, offline=offline)
    btc_sig = get_signal(BTC_TICKER, offline=offline)

    rows = [
        [
            "SPY (stocks)",
            _dollar(spy_sig["price"]),
            _dollar(spy_sig["sma200"]),
            _pct(spy_sig["pct_vs_sma"]),
            spy_sig["signal"],
            "hold SPY" if spy_sig["signal"] == "RISK_ON" else f"rotate → {DEFENSIVE_TICKER}",
        ],
        [
            "BTC",
            _dollar(btc_sig["price"]),
            _dollar(btc_sig["sma200"]),
            _pct(btc_sig["pct_vs_sma"]),
            btc_sig["signal"],
            "hold BTC" if btc_sig["signal"] == "RISK_ON" else "move → CASH",
        ],
    ]

    print(_tbl(rows, ["Asset", "Price", "200 SMA", "vs SMA", "Signal", "Action"]))

    for sig, label in [(spy_sig, "SPY"), (btc_sig, "BTC")]:
        if sig["crossed_above"]:
            print(f"\n  *** {label} just CROSSED ABOVE 200 SMA — BUY signal ***")
        if sig["crossed_below"]:
            print(f"\n  *** {label} just CROSSED BELOW 200 SMA — DEFENSIVE signal ***")

    return spy_sig, btc_sig


def section_allocation(spy_sig: dict, btc_sig: dict):
    alloc = current_allocation(spy_sig, btc_sig)
    stock_ticker = alloc["stock_sleeve"]["ticker"]
    btc_ticker = alloc["btc_sleeve"]["ticker"]

    print("\n" + "=" * 62)
    print("  RECOMMENDED ALLOCATION  (today)")
    print("=" * 62)
    rows = [
        ["Stock sleeve", "50%", stock_ticker,
         _dollar(INITIAL_VALUE * STOCK_ALLOCATION),
         "TLT bonds (risk-off)" if stock_ticker == "TLT" else "SPY equities (risk-on)"],
        ["BTC sleeve", "50%", btc_ticker,
         _dollar(INITIAL_VALUE * BTC_ALLOCATION),
         "CASH / stablecoin" if btc_ticker == "CASH" else "Bitcoin (risk-on)"],
    ]
    print(_tbl(rows, ["Sleeve", "Weight", "Hold", "$ of $10k", "Status"]))


def section_backtest(offline: bool, show_chart: bool = False):
    print("\n" + "=" * 62)
    print(f"  BACKTEST  ({BACKTEST_START} → today)")
    if offline:
        print("  [DEMO MODE — synthetic GBM data]")
    print("=" * 62)
    if not offline:
        print("  Fetching data … (this may take 20–30 s)")

    import backtest
    result = backtest.run(offline=offline)

    s = result["strategy"]
    b = result["benchmark"]

    rows = [
        ["Strategy (200-SMA)",
         _dollar(s["final_value"]), _pct(s["total_return_pct"]),
         _pct(s["cagr"] * 100), _pct(s["max_drawdown"] * 100), f"{s['sharpe']:.2f}"],
        ["SPY buy-and-hold",
         _dollar(b["final_value"]), _pct(b["total_return_pct"]),
         _pct(b["cagr"] * 100), _pct(b["max_drawdown"] * 100), f"{b['sharpe']:.2f}"],
    ]
    print(_tbl(rows, ["", "$10k grew to", "Total Ret", "CAGR", "Max DD", "Sharpe"]))

    print(f"\n  Stock sleeve in TLT (bonds) : {result['pct_in_tlt']:.1f}% of trading days")
    print(f"  BTC sleeve in cash          : {result['pct_btc_cash']:.1f}% of trading days")
    print(f"  Backtest length             : {result['n_years']:.1f} years")

    beat = "BEATS" if s["cagr"] > b["cagr"] else "TRAILS"
    delta = (s["cagr"] - b["cagr"]) * 100
    print(f"\n  Strategy {beat} SPY by {abs(delta):.2f}% per year (annualised alpha)")

    if show_chart:
        _plot_backtest(result)

    return result


def section_projection(strat_cagr: float):
    print("\n" + "=" * 62)
    print(f"  PROJECTION to age {TARGET_AGE}  ({YEARS_TO_TARGET}-year horizon from age {CURRENT_AGE})")
    print("=" * 62)

    scenarios = [
        ("Conservative  (8% CAGR)", 0.08),
        ("SPY avg       (10% CAGR)", 0.10),
        ("Moderate      (12% CAGR)", 0.12),
        ("Strategy (backtest CAGR)", strat_cagr),
        ("Aggressive    (18% CAGR)", 0.18),
    ]

    rows = []
    for label, cagr in scenarios:
        value = INITIAL_VALUE * (1 + cagr) ** YEARS_TO_TARGET
        mult = value / INITIAL_VALUE
        rows.append([label, _pct(cagr * 100), _dollar(value), f"{mult:.1f}x",
                     _bar(cagr * 100)])
    print(_tbl(rows, ["Scenario", "CAGR", "Value at 18", "Multiple", "Progress bar"]))

    print(f"\n  Starting capital : {_dollar(INITIAL_VALUE)}")
    print(f"  Compounding years: {YEARS_TO_TARGET}  ({CURRENT_AGE} → {TARGET_AGE})")


def section_rules():
    print("\n" + "=" * 62)
    print("  PLAYBOOK  (print and keep)")
    print("=" * 62)
    rules = [
        "1. CHECK signals once a week (e.g. every Sunday evening).",
        "",
        "2. STOCK SLEEVE (50%):",
        "   • SPY closes ABOVE 200-SMA  → hold / buy SPY.",
        "   • SPY closes BELOW 200-SMA  → sell SPY, buy TLT (bonds).",
        "   • Reverse when SPY reclaims 200-SMA.",
        "",
        "3. BTC SLEEVE (50%):",
        "   • BTC closes ABOVE 200-SMA  → hold / buy BTC.",
        "   • BTC closes BELOW 200-SMA  → sell BTC, park in stablecoin",
        "     or money-market ETF (SGOV / USDM).",
        "   • Re-enter BTC once price is back above 200-SMA.",
        "",
        "4. REBALANCE back to 50 / 50 (stocks : BTC) once per year",
        "   (e.g. on your son's birthday each October).",
        "",
        "5. DO NOT rebalance on every SMA crossover — only swap the",
        "   position of the affected sleeve.",
        "",
        "6. TAX: Aim to hold positions > 12 months (long-term cap gains).",
        "",
        "7. DE-RISK GLIDE PATH:",
        "   Age 15 → shift to 60% stocks / 30% BTC / 10% bonds.",
        "   Age 17 → shift to 70% stocks / 20% BTC / 10% bonds.",
        "   Age 18 → decide together with your son what to do with it.",
    ]
    for r in rules:
        print("  " + r)


# ── chart ─────────────────────────────────────────────────────────────────────

def _plot_backtest(result: dict):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                        gridspec_kw={"height_ratios": [3, 1]})
        fig.suptitle("SPX-Beater: 200-SMA Strategy vs SPY Buy-and-Hold", fontsize=14)

        strat = result["strat_values"]
        bench = result["bench_values"]

        ax1.plot(strat.index, strat.values, label="200-SMA Strategy", color="#2ecc71", lw=1.8)
        ax1.plot(bench.index, bench.values, label="SPY Buy-and-Hold", color="#3498db",
                 lw=1.5, alpha=0.8)
        ax1.set_ylabel("Portfolio Value ($)")
        ax1.legend()
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax1.grid(alpha=0.3)

        rel = (strat / bench - 1) * 100
        colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in rel.values]
        ax2.bar(rel.index, rel.values, color=colors, width=1, alpha=0.7)
        ax2.axhline(0, color="black", lw=0.8)
        ax2.set_ylabel("vs SPY (%)")
        ax2.set_xlabel("Date")
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax2.grid(alpha=0.3)

        plt.tight_layout()
        path = "backtest_chart.png"
        plt.savefig(path, dpi=150)
        print(f"\n  Chart saved → {path}")
    except Exception as e:
        print(f"\n  Chart skipped: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SPX-Beater: 200-SMA portfolio manager for your son's $10k"
    )
    parser.add_argument("--backtest", action="store_true",
                        help="Run historical backtest (~30 s with live data)")
    parser.add_argument("--chart", action="store_true",
                        help="Save backtest chart to backtest_chart.png (needs --backtest)")
    parser.add_argument("--demo", action="store_true",
                        help="Use synthetic data (no internet required)")
    parser.add_argument("--no-rules", action="store_true",
                        help="Skip the strategy playbook section")
    args = parser.parse_args()

    offline = args.demo

    print("\n" + "█" * 62)
    print("  SPX-BEATER  |  $10k → Age 18 Portfolio Manager")
    print("  Strategy: Michael Gayed 200-SMA + BTC 200-SMA")
    print("█" * 62)

    spy_sig, btc_sig = section_signals(offline=offline)
    section_allocation(spy_sig, btc_sig)

    strat_cagr = 0.13  # fallback placeholder

    if args.backtest or args.demo:
        result = section_backtest(offline=offline, show_chart=args.chart)
        strat_cagr = result["strategy"]["cagr"]
    else:
        print("\n  (Run with --backtest for historical performance, --demo for offline mode)")

    section_projection(strat_cagr)

    if not args.no_rules:
        section_rules()

    print("\n" + "=" * 62 + "\n")


if __name__ == "__main__":
    main()
