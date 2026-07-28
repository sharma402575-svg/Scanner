"""
Core scanning engine.

R Factor  = stock's % return over `lookback` periods
            - sector index's % return over the same `lookback` periods

  R Factor > 0  -> stock is outperforming its sector (bullish tilt)
  R Factor < 0  -> stock is underperforming its sector (bearish tilt)

Momentum Score = short-term rate of change (5-day %) combined with a
volume-surge ratio (today's volume vs 20-day average volume). Used to
surface "high momentum" stocks regardless of sector.

Signal classification blends R Factor with trend confirmation
(price vs 20/50 day moving averages).
"""

import pandas as pd
import numpy as np
import yfinance as yf
from sectors import SECTOR_STOCKS, SECTOR_INDEX


# ---------- helpers ----------

def _pct_return(series: pd.Series, periods: int) -> float:
    if len(series) < periods + 1:
        return np.nan
    return float((series.iloc[-1] / series.iloc[-periods - 1] - 1) * 100)


def all_tickers_flat():
    """Every stock across every sector, deduplicated, with its sector tag."""
    out = []
    for sector, stocks in SECTOR_STOCKS.items():
        for t in stocks:
            out.append((t, sector))
    return out


def fetch_history(tickers, period="6mo", interval="1d"):
    """Download OHLC history for a list of tickers in one batched call."""
    data = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )
    return data


def _close_series(data, ticker):
    try:
        return data[ticker]["Close"].dropna()
    except Exception:
        return pd.Series(dtype=float)


def _volume_series(data, ticker):
    try:
        return data[ticker]["Volume"].dropna()
    except Exception:
        return pd.Series(dtype=float)


# ---------- sector-scoped scan ----------

def scan_sector(sector: str, lookback: int = 20, rs_bull_threshold: float = 2.0,
                 rs_bear_threshold: float = -2.0, raw=None):
    if sector not in SECTOR_STOCKS:
        raise ValueError(f"Unknown sector '{sector}'. Options: {list(SECTOR_STOCKS)}")

    stocks = SECTOR_STOCKS[sector]
    index_ticker = SECTOR_INDEX[sector]

    if raw is None:
        raw = fetch_history(stocks + [index_ticker])

    idx_close = _close_series(raw, index_ticker)
    sector_return = _pct_return(idx_close, lookback)

    rows = []
    for t in stocks:
        close = _close_series(raw, t)
        if close.empty:
            continue
        ltp = float(close.iloc[-1])
        stock_return = _pct_return(close, lookback)
        r_factor = (stock_return - sector_return
                    if not np.isnan(stock_return) and not np.isnan(sector_return)
                    else np.nan)

        ma20 = close.rolling(20).mean().iloc[-1]
        above20 = bool(ltp > ma20) if not np.isnan(ma20) else None

        if r_factor is not None and not np.isnan(r_factor):
            if r_factor >= rs_bull_threshold and above20:
                signal = "Bullish"
            elif r_factor <= rs_bear_threshold and above20 is False:
                signal = "Bearish"
            else:
                signal = "Neutral"
        else:
            signal = "N/A"

        rows.append({
            "Ticker": t.replace(".NS", ""),
            "Sector": sector,
            "LTP": round(ltp, 2),
            f"%Chg ({lookback}d)": round(stock_return, 2) if not np.isnan(stock_return) else None,
            "Sector %Chg": round(sector_return, 2) if not np.isnan(sector_return) else None,
            "R Factor": round(r_factor, 2) if r_factor is not None and not np.isnan(r_factor) else None,
            "Above 20DMA": above20,
            "Signal": signal,
        })

    df = pd.DataFrame(rows)
    if "R Factor" in df.columns:
        df = df.sort_values("R Factor", ascending=False, na_position="last")
    return df.reset_index(drop=True)


# ---------- full-market scans ----------

def _fetch_full_market():
    """One batched download covering every stock + every sector index."""
    tickers = [t for t, _ in all_tickers_flat()] + list(SECTOR_INDEX.values())
    return fetch_history(tickers)


def full_market_scan(lookback: int = 20, rs_bull_threshold: float = 2.0,
                      rs_bear_threshold: float = -2.0):
    """Run the R-Factor scan across every sector at once, return one big table."""
    raw = _fetch_full_market()
    frames = []
    for sector in SECTOR_STOCKS:
        frames.append(scan_sector(sector, lookback=lookback,
                                   rs_bull_threshold=rs_bull_threshold,
                                   rs_bear_threshold=rs_bear_threshold, raw=raw))
    full = pd.concat(frames, ignore_index=True)
    return full.sort_values("R Factor", ascending=False, na_position="last").reset_index(drop=True)


def most_bullish(n: int = 15, **kwargs) -> pd.DataFrame:
    df = full_market_scan(**kwargs)
    return df[df["Signal"] == "Bullish"].head(n).reset_index(drop=True)


def most_bearish(n: int = 15, **kwargs) -> pd.DataFrame:
    df = full_market_scan(**kwargs)
    bearish = df[df["Signal"] == "Bearish"].sort_values("R Factor", ascending=True)
    return bearish.head(n).reset_index(drop=True)


def top_gainers_losers(n: int = 15):
    """Rank the full stock universe by today's 1-day % change."""
    raw = _fetch_full_market()
    rows = []
    for t, sector in all_tickers_flat():
        close = _close_series(raw, t)
        vol = _volume_series(raw, t)
        if len(close) < 2:
            continue
        chg = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
        rows.append({
            "Ticker": t.replace(".NS", ""),
            "Sector": sector,
            "LTP": round(float(close.iloc[-1]), 2),
            "% Chg (1d)": round(chg, 2),
            "Volume": int(vol.iloc[-1]) if not vol.empty else None,
        })
    df = pd.DataFrame(rows).sort_values("% Chg (1d)", ascending=False)
    gainers = df.head(n).reset_index(drop=True)
    losers = df.sort_values("% Chg (1d)", ascending=True).head(n).reset_index(drop=True)
    return gainers, losers


def momentum_scan(n: int = 15, short_period: int = 5):
    """
    Momentum Score blends short-term price rate-of-change with a
    volume-surge ratio, so it favors stocks moving fast on real volume
    rather than just drifting up on thin trading.
    """
    raw = _fetch_full_market()
    rows = []
    for t, sector in all_tickers_flat():
        close = _close_series(raw, t)
        vol = _volume_series(raw, t)
        if len(close) < short_period + 1 or len(vol) < 21:
            continue
        roc = _pct_return(close, short_period)
        avg_vol20 = vol.iloc[-21:-1].mean()
        vol_surge = float(vol.iloc[-1] / avg_vol20) if avg_vol20 > 0 else np.nan
        if np.isnan(roc) or np.isnan(vol_surge):
            continue
        momentum_score = roc * min(vol_surge, 5)  # cap surge influence at 5x

        rows.append({
            "Ticker": t.replace(".NS", ""),
            "Sector": sector,
            "LTP": round(float(close.iloc[-1]), 2),
            f"ROC ({short_period}d) %": round(roc, 2),
            "Volume Surge (x avg)": round(vol_surge, 2),
            "Momentum Score": round(momentum_score, 2),
        })
    df = pd.DataFrame(rows).sort_values("Momentum Score", ascending=False)
    return df.head(n).reset_index(drop=True)


def sector_overview(lookback: int = 20):
    """
    Aggregate R Factor per sector -> which sectors are getting bullish
    vs bearish as a whole (not individual stocks).
    """
    df = full_market_scan(lookback=lookback)
    if df.empty:
        return df
    agg = (
        df.groupby("Sector")
        .agg(
            **{
                "Avg R Factor": ("R Factor", "mean"),
                "Bullish Count": ("Signal", lambda s: (s == "Bullish").sum()),
                "Bearish Count": ("Signal", lambda s: (s == "Bearish").sum()),
                "Total Stocks": ("Ticker", "count"),
            }
        )
        .reset_index()
    )
    agg["Avg R Factor"] = agg["Avg R Factor"].round(2)

    def _bias(row):
        if row["Avg R Factor"] > 1:
            return "Bullish"
        if row["Avg R Factor"] < -1:
            return "Bearish"
        return "Neutral"

    agg["Sector Bias"] = agg.apply(_bias, axis=1)
    return agg.sort_values("Avg R Factor", ascending=False).reset_index(drop=True)
