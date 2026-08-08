"""
Relative Rotation Graph (RRG) engine.

Classic RRG plots two derived series per sector, vs a benchmark (Nifty 50):
  - RS-Ratio     (x-axis): normalized relative strength — is the sector
                  outperforming or underperforming the benchmark, on a
                  scale centered at 100.
  - RS-Momentum  (y-axis): is that relative strength itself accelerating
                  or decelerating, also centered at 100.

Together they place each sector in one of four quadrants:
  Leading    (RS-Ratio > 100, RS-Momentum > 100)  — outperforming, and it's accelerating
  Weakening  (RS-Ratio > 100, RS-Momentum < 100)  — still outperforming, but losing steam
  Lagging    (RS-Ratio < 100, RS-Momentum < 100)  — underperforming, and still falling
  Improving  (RS-Ratio < 100, RS-Momentum > 100)  — underperforming, but turning up

Sectors classically rotate clockwise through these quadrants over time —
that rotation path (a "tail" of recent weeks) is the point of the chart.

Methodology note: the original JdK RS-Ratio/RS-Momentum formulas are
proprietary (Julius de Kempenaer / StockCharts). This uses the standard
open, publicly-documented approximation widely used in open-source RRG
implementations: a z-score-normalized RS-Ratio and a rate-of-change-based
RS-Momentum. It reproduces the same quadrant behavior and rotation
pattern, but exact coordinate values won't match a licensed StockCharts
RRG tick-for-tick.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from sectors import SECTOR_INDEX

BENCHMARK = "^NSEI"  # Nifty 50


def fetch_rrg_data(period="1y"):
    """Weekly closes for every sector index + the Nifty 50 benchmark."""
    tickers = list(SECTOR_INDEX.values()) + [BENCHMARK]
    raw = yf.download(tickers=tickers, period=period, interval="1d",
                       group_by="ticker", auto_adjust=False, threads=True, progress=False)
    weekly = {}
    for t in tickers:
        try:
            close = raw[t]["Close"].dropna()
            weekly[t] = close.resample("W-FRI").last().dropna()
        except Exception:
            continue
    return weekly


def compute_rs_ratio_momentum(sector_close: pd.Series, benchmark_close: pd.Series,
                               ratio_window: int = 10, momentum_window: int = 4):
    """
    RS-Ratio: z-score of the relative-strength line (sector/benchmark),
    rescaled to center at 100.
    RS-Momentum: rate of change of RS-Ratio over `momentum_window` periods,
    also rescaled to center at 100.
    """
    df = pd.DataFrame({"sector": sector_close, "bench": benchmark_close}).dropna()
    if len(df) < ratio_window + momentum_window + 2:
        return None

    rs = df["sector"] / df["bench"] * 100
    rs_sma = rs.rolling(ratio_window).mean()
    rs_std = rs.rolling(ratio_window).std()
    rs_ratio = 100 + (rs - rs_sma) / rs_std.replace(0, np.nan)

    rs_momentum = 100 + (rs_ratio.diff(momentum_window) / rs_ratio.shift(momentum_window)) * 100

    out = pd.DataFrame({"rs_ratio": rs_ratio, "rs_momentum": rs_momentum}).dropna()
    return out if not out.empty else None


def quadrant(rs_ratio, rs_momentum):
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading"
    if rs_ratio >= 100 and rs_momentum < 100:
        return "Weakening"
    if rs_ratio < 100 and rs_momentum < 100:
        return "Lagging"
    return "Improving"


def build_rrg(tail_length: int = 8, ratio_window: int = 10, momentum_window: int = 4):
    """
    Returns {sector: DataFrame(rs_ratio, rs_momentum)} with the last
    `tail_length` weekly points per sector, for plotting rotation tails.
    """
    weekly = fetch_rrg_data()
    bench = weekly.get(BENCHMARK)
    if bench is None or bench.empty:
        return {}

    result = {}
    for sector, idx_ticker in SECTOR_INDEX.items():
        sc = weekly.get(idx_ticker)
        if sc is None or sc.empty:
            continue
        computed = compute_rs_ratio_momentum(sc, bench, ratio_window, momentum_window)
        if computed is None:
            continue
        result[sector] = computed.tail(tail_length).reset_index(drop=True)
    return result


def latest_quadrant_summary(rrg_data: dict):
    """One row per sector: latest RS-Ratio, RS-Momentum, and quadrant."""
    rows = []
    for sector, df in rrg_data.items():
        if df.empty:
            continue
        last = df.iloc[-1]
        rows.append({
            "Sector": sector,
            "RS-Ratio": round(float(last["rs_ratio"]), 2),
            "RS-Momentum": round(float(last["rs_momentum"]), 2),
            "Quadrant": quadrant(last["rs_ratio"], last["rs_momentum"]),
        })
    return pd.DataFrame(rows).sort_values("Sector").reset_index(drop=True)
