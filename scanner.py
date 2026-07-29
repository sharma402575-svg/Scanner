"""
Core scanning engine.

Everything is built from ONE master table (build_master_table) computed
from a single data fetch per refresh. Every section on the page is a
filter/sort of that same table, so numbers never drift apart.

--- R Factor ---
R Factor = stock's % return over `lookback` periods
           - sector index's % return over the same period
  > 0  -> stock outperforming its sector (bullish tilt)
  < 0  -> stock underperforming its sector (bearish tilt)

--- Range Breakout / Breakdown ---
Breakout = today's close is ABOVE the highest close of the prior
           `breakout_period` days (excluding today)
Breakdown = today's close is BELOW the lowest close of the prior
            `breakout_period` days (excluding today)
A simple, standard definition of a price breaking out of its recent
trading range.

--- Trade Signal (composite) ---
A transparent points system, not a black box:
  +2 / -2   R Factor strongly above/below your threshold (sector strength)
  +1 / -1   Price above/below its 20-day moving average (trend)
  +1 / -1   RSI healthy (40-65) vs overbought (>75) or deeply oversold (<25)
  +1 / -1   Momentum score positive/negative with real volume behind it
  +1 / -1   Near 52-week high/low (trend continuation)
  +1 / -1   Range breakout / breakdown

Score >= 4   -> Strong Buy   | Score 2-3    -> Buy
Score -1..1  -> Hold
Score -3..-2 -> Sell         | Score <= -4  -> Strong Sell

Rules-based heuristic combining common technical factors — NOT financial
advice, and has no knowledge of news, fundamentals, or events.
"""

import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import yfinance as yf
from sectors import SECTOR_STOCKS, SECTOR_INDEX

IST = ZoneInfo("Asia/Kolkata")


# ---------- low-level helpers ----------

def _pct_return(series: pd.Series, periods: int) -> float:
    if len(series) < periods + 1:
        return np.nan
    return float((series.iloc[-1] / series.iloc[-periods - 1] - 1) * 100)


def _rsi(close: pd.Series, period: int = 14) -> float:
    if len(close) < period + 1:
        return np.nan
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean().iloc[-1]
    avg_loss = loss.rolling(period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    if len(close) < period + 1:
        return np.nan
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low, (high - prev_close).abs(), (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def all_tickers_flat():
    out = []
    for sector, stocks in SECTOR_STOCKS.items():
        for t in stocks:
            out.append((t, sector))
    return out


def fetch_history(tickers, period="1y", interval="1d"):
    """1y of daily bars — enough for 52-week high/low AND all shorter lookbacks."""
    return yf.download(
        tickers=tickers, period=period, interval=interval, group_by="ticker",
        auto_adjust=False, threads=True, progress=False,
    )


def _col(data, ticker, field):
    try:
        return data[ticker][field].dropna()
    except Exception:
        return pd.Series(dtype=float)


def data_freshness_from_raw(raw):
    """Dates in dd-mm-yyyy; 'today' and fetch time both reported in IST
    (Indian market time), regardless of what timezone the server runs in."""
    try:
        date_str = raw.index[-1].date().strftime("%d-%m-%Y")
    except Exception:
        date_str = "unknown"
    now_ist = datetime.datetime.now(IST)
    today_str = now_ist.strftime("%d-%m-%Y")
    return {"last_data_date": date_str, "today": today_str, "is_stale": date_str != today_str}


def _fetch_full_market():
    tickers = [t for t, _ in all_tickers_flat()] + list(SECTOR_INDEX.values())
    return fetch_history(tickers)


def _trade_signal(r_factor, above20, rsi, momentum_score, near_high, near_low,
                   breakout, breakdown, rs_bull_threshold, rs_bear_threshold):
    score = 0
    if r_factor is not None and not np.isnan(r_factor):
        if r_factor >= rs_bull_threshold:
            score += 2
        elif r_factor <= rs_bear_threshold:
            score -= 2
    if above20 is True:
        score += 1
    elif above20 is False:
        score -= 1
    if rsi is not None and not np.isnan(rsi):
        if 40 <= rsi <= 65:
            score += 1
        elif rsi > 75:
            score -= 1
        elif rsi < 25:
            score -= 1
    if momentum_score is not None and not np.isnan(momentum_score):
        if momentum_score > 1:
            score += 1
        elif momentum_score < -1:
            score -= 1
    if near_high:
        score += 1
    if near_low:
        score -= 1
    if breakout:
        score += 1
    if breakdown:
        score -= 1

    if score >= 4:
        label = "Strong Buy"
    elif score >= 2:
        label = "Buy"
    elif score <= -4:
        label = "Strong Sell"
    elif score <= -2:
        label = "Sell"
    else:
        label = "Hold"
    return score, label


# ---------- master table ----------

def build_master_table(lookback: int = 20, rs_bull_threshold: float = 2.0,
                        rs_bear_threshold: float = -2.0, breakout_period: int = 20, raw=None):
    if raw is None:
        raw = _fetch_full_market()

    sector_return = {}
    for sector, idx_ticker in SECTOR_INDEX.items():
        idx_close = _col(raw, idx_ticker, "Close")
        sector_return[sector] = _pct_return(idx_close, lookback)

    rows = []
    for t, sector in all_tickers_flat():
        close = _col(raw, t, "Close")
        high = _col(raw, t, "High")
        low = _col(raw, t, "Low")
        vol = _col(raw, t, "Volume")
        if close.empty or len(close) < 2:
            continue

        ltp = float(close.iloc[-1])
        day_high = float(high.iloc[-1]) if not high.empty else np.nan
        day_low = float(low.iloc[-1]) if not low.empty else np.nan
        chg_1d = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)

        stock_return = _pct_return(close, lookback)
        sec_ret = sector_return.get(sector, np.nan)
        r_factor = (stock_return - sec_ret
                    if not np.isnan(stock_return) and not np.isnan(sec_ret) else np.nan)

        ma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else np.nan
        above20 = bool(ltp > ma20) if not np.isnan(ma20) else None

        rsi = _rsi(close)
        atr = _atr(high, low, close)
        stop_long = round(ltp - 1.5 * atr, 2) if not np.isnan(atr) else None

        avg_vol20 = vol.iloc[-21:-1].mean() if len(vol) >= 21 else np.nan
        vol_surge = float(vol.iloc[-1] / avg_vol20) if avg_vol20 and avg_vol20 > 0 else np.nan

        roc5 = _pct_return(close, 5)
        momentum_score = (roc5 * min(vol_surge, 5)
                           if not np.isnan(roc5) and not np.isnan(vol_surge) else np.nan)

        high_52w = float(high.max()) if not high.empty else np.nan
        low_52w = float(low.min()) if not low.empty else np.nan
        pct_from_52w_high = ((ltp - high_52w) / high_52w * 100) if high_52w else np.nan
        pct_from_52w_low = ((ltp - low_52w) / low_52w * 100) if low_52w else np.nan
        near_52w_high = bool(pct_from_52w_high is not None and not np.isnan(pct_from_52w_high) and pct_from_52w_high >= -3)
        near_52w_low = bool(pct_from_52w_low is not None and not np.isnan(pct_from_52w_low) and pct_from_52w_low <= 3)

        at_day_high = bool(day_high and (day_high - ltp) / day_high <= 0.003)
        at_day_low = bool(day_low and (ltp - day_low) / day_low <= 0.003)

        # Range breakout / breakdown vs prior N-day close range (excluding today)
        breakout = breakdown = False
        range_high = range_low = None
        if len(close) > breakout_period:
            prior = close.iloc[-(breakout_period + 1):-1]
            range_high = float(prior.max())
            range_low = float(prior.min())
            breakout = bool(ltp > range_high)
            breakdown = bool(ltp < range_low)

        # 200-day EMA crossover — did price cross above/below it just now?
        ema_cross_up = ema_cross_down = False
        ema200_val = None
        if len(close) >= 201:
            ema200_series = close.ewm(span=200, adjust=False).mean()
            ema200_val = float(ema200_series.iloc[-1])
            prev_close_v = float(close.iloc[-2])
            prev_ema200 = float(ema200_series.iloc[-2])
            ema_cross_up = bool(prev_close_v <= prev_ema200 and ltp > ema200_val)
            ema_cross_down = bool(prev_close_v >= prev_ema200 and ltp < ema200_val)

        if r_factor is not None and not np.isnan(r_factor):
            if r_factor >= rs_bull_threshold and above20:
                trend_signal = "Bullish"
            elif r_factor <= rs_bear_threshold and above20 is False:
                trend_signal = "Bearish"
            else:
                trend_signal = "Neutral"
        else:
            trend_signal = "N/A"

        score, trade_signal = _trade_signal(
            r_factor, above20, rsi, momentum_score, near_52w_high, near_52w_low,
            breakout, breakdown, rs_bull_threshold, rs_bear_threshold,
        )

        rows.append({
            "Ticker": t.replace(".NS", ""),
            "Sector": sector,
            "LTP": round(ltp, 2),
            "% Chg (1d)": round(chg_1d, 2),
            f"%Chg ({lookback}d)": round(stock_return, 2) if not np.isnan(stock_return) else None,
            "R Factor": round(r_factor, 2) if r_factor is not None and not np.isnan(r_factor) else None,
            "Trend Signal": trend_signal,
            "RSI(14)": round(rsi, 2) if not np.isnan(rsi) else None,
            "ATR(14)": round(atr, 2) if not np.isnan(atr) else None,
            "Suggested Stop (long)": stop_long,
            "Vol Surge (x avg)": round(vol_surge, 2) if not np.isnan(vol_surge) else None,
            "Momentum Score": round(momentum_score, 2) if not np.isnan(momentum_score) else None,
            "52w High": round(high_52w, 2) if not np.isnan(high_52w) else None,
            "52w Low": round(low_52w, 2) if not np.isnan(low_52w) else None,
            "% From 52w High": round(pct_from_52w_high, 2) if not np.isnan(pct_from_52w_high) else None,
            "% From 52w Low": round(pct_from_52w_low, 2) if not np.isnan(pct_from_52w_low) else None,
            "Near 52w High": near_52w_high,
            "Near 52w Low": near_52w_low,
            "At Day High": at_day_high,
            "At Day Low": at_day_low,
            f"Range High ({breakout_period}d)": round(range_high, 2) if range_high else None,
            f"Range Low ({breakout_period}d)": round(range_low, 2) if range_low else None,
            "Breakout": breakout,
            "Breakdown": breakdown,
            "200 EMA": round(ema200_val, 2) if ema200_val is not None else None,
            "Crossed Above 200EMA": ema_cross_up,
            "Crossed Below 200EMA": ema_cross_down,
            "Score": score,
            "Trade Signal": trade_signal,
        })

    df = pd.DataFrame(rows)
    return df.reset_index(drop=True)


# ---------- views derived from the master table ----------

def view_most_bullish(df, n=15):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "R Factor", "Trend Signal", "Trade Signal"]
    return df[df["Trend Signal"] == "Bullish"].sort_values("% Chg (1d)", ascending=False).head(n)[cols].reset_index(drop=True)


def view_most_bearish(df, n=15):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "R Factor", "Trend Signal", "Trade Signal"]
    return df[df["Trend Signal"] == "Bearish"].sort_values("% Chg (1d)", ascending=True).head(n)[cols].reset_index(drop=True)


def view_momentum(df, n=15):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "Momentum Score", "Vol Surge (x avg)", "Trade Signal"]
    return df.sort_values("Momentum Score", ascending=False).head(n)[cols].reset_index(drop=True)


def view_gainers_losers(df, n=15):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "Trade Signal"]
    gainers = df.sort_values("% Chg (1d)", ascending=False).head(n)[cols].reset_index(drop=True)
    losers = df.sort_values("% Chg (1d)", ascending=True).head(n)[cols].reset_index(drop=True)
    return gainers, losers


def view_volume_surge(df, threshold=2.0, n=20):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "Vol Surge (x avg)", "Trade Signal"]
    sub = df[df["Vol Surge (x avg)"].fillna(0) >= threshold]
    return sub.sort_values("Vol Surge (x avg)", ascending=False).head(n)[cols].reset_index(drop=True)


def view_day_high_low(df, n=20):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "Trade Signal"]
    at_high = df[df["At Day High"]].sort_values("% Chg (1d)", ascending=False).head(n)[cols].reset_index(drop=True)
    at_low = df[df["At Day Low"]].sort_values("% Chg (1d)", ascending=True).head(n)[cols].reset_index(drop=True)
    return at_high, at_low


def view_52w_high_low(df, n=20):
    cols_h = ["Ticker", "Sector", "LTP", "% Chg (1d)", "52w High", "% From 52w High", "Trade Signal"]
    near_high = df[df["Near 52w High"]].sort_values("% From 52w High", ascending=False).head(n)[cols_h].reset_index(drop=True)
    cols_l = ["Ticker", "Sector", "LTP", "% Chg (1d)", "52w Low", "% From 52w Low", "Trade Signal"]
    near_low = df[df["Near 52w Low"]].sort_values("% From 52w Low", ascending=True).head(n)[cols_l].reset_index(drop=True)
    return near_high, near_low


def view_range_breakout(df, breakout_period=20, n=20):
    hcol, lcol = f"Range High ({breakout_period}d)", f"Range Low ({breakout_period}d)"
    cols_out = ["Ticker", "Sector", "LTP", "% Chg (1d)", hcol, "Trade Signal"]
    cols_down = ["Ticker", "Sector", "LTP", "% Chg (1d)", lcol, "Trade Signal"]
    breakout = df[df["Breakout"]].sort_values("% Chg (1d)", ascending=False).head(n)[cols_out].reset_index(drop=True)
    breakdown = df[df["Breakdown"]].sort_values("% Chg (1d)", ascending=True).head(n)[cols_down].reset_index(drop=True)
    return breakout, breakdown


def view_ema200_cross(df, n=20):
    cols = ["Ticker", "Sector", "LTP", "% Chg (1d)", "200 EMA", "Trade Signal"]
    up = df[df["Crossed Above 200EMA"]].sort_values("% Chg (1d)", ascending=False).head(n)[cols].reset_index(drop=True)
    down = df[df["Crossed Below 200EMA"]].sort_values("% Chg (1d)", ascending=True).head(n)[cols].reset_index(drop=True)
    return up, down


def view_sector_overview(df):
    agg = (
        df.groupby("Sector")
        .agg(**{
            "Avg R Factor": ("R Factor", "mean"),
            "Avg % Chg (1d)": ("% Chg (1d)", "mean"),
            "Avg Score": ("Score", "mean"),
            "Bullish Count": ("Trend Signal", lambda s: (s == "Bullish").sum()),
            "Bearish Count": ("Trend Signal", lambda s: (s == "Bearish").sum()),
            "Total Stocks": ("Ticker", "count"),
        })
        .reset_index()
    )
    agg["Avg R Factor"] = agg["Avg R Factor"].round(2)
    agg["Avg % Chg (1d)"] = agg["Avg % Chg (1d)"].round(2)
    agg["Avg Score"] = agg["Avg Score"].round(2)

    def _bias(row):
        if row["Avg R Factor"] > 1:
            return "Bullish"
        if row["Avg R Factor"] < -1:
            return "Bearish"
        return "Neutral"

    agg["Sector Bias"] = agg.apply(_bias, axis=1)
    return agg.sort_values("Avg R Factor", ascending=False).reset_index(drop=True)


def view_sector_detail(df, sector, lookback_col):
    cols = ["Ticker", "LTP", "% Chg (1d)", lookback_col, "R Factor", "Trend Signal",
            "RSI(14)", "Vol Surge (x avg)", "ATR(14)", "Suggested Stop (long)", "Trade Signal"]
    cols = [c for c in cols if c in df.columns]
    sub = df[df["Sector"] == sector].sort_values("R Factor", ascending=False)
    return sub[cols].reset_index(drop=True)


def overall_market_signal(df):
    if df.empty:
        return {"label": "N/A", "avg_score": 0, "pct_buy": 0, "pct_sell": 0,
                "pct_hold": 0, "total": 0}
    total = len(df)
    pct_buy = round((df["Trade Signal"].isin(["Buy", "Strong Buy"]).sum() / total) * 100, 1)
    pct_sell = round((df["Trade Signal"].isin(["Sell", "Strong Sell"]).sum() / total) * 100, 1)
    pct_hold = round(100 - pct_buy - pct_sell, 1)
    avg_score = round(df["Score"].mean(), 2)
    if avg_score >= 1.5:
        label = "Buy"
    elif avg_score <= -1.5:
        label = "Sell"
    else:
        label = "Neutral"
    return {"label": label, "avg_score": avg_score, "pct_buy": pct_buy,
            "pct_sell": pct_sell, "pct_hold": pct_hold, "total": total}


def alerts_summary(df, breakout_period=20):
    """Counts + top tickers for every 'special event' flag, for the flash
    panel shown beside the overall market signal."""
    def top_tickers(mask, n=5):
        return df.loc[mask, "Ticker"].head(n).tolist()

    items = [
        ("Breakout", df["Breakout"], "🚀"),
        ("Breakdown", df["Breakdown"], "🔻"),
        ("At Day High", df["At Day High"], "📍"),
        ("At Day Low", df["At Day Low"], "📍"),
        ("Near 52w High", df["Near 52w High"], "📅"),
        ("Near 52w Low", df["Near 52w Low"], "📅"),
    ]
    out = []
    for label, mask, icon in items:
        count = int(mask.sum())
        if count > 0:
            out.append({"label": label, "icon": icon, "count": count, "tickers": top_tickers(mask)})
    return out


def run_full_scan_bundle(lookback: int = 20, rs_bull_threshold: float = 2.0,
                          rs_bear_threshold: float = -2.0, vol_threshold: float = 2.0,
                          breakout_period: int = 20, top_n: int = 15):
    raw = _fetch_full_market()
    freshness = data_freshness_from_raw(raw)
    master = build_master_table(lookback=lookback, rs_bull_threshold=rs_bull_threshold,
                                 rs_bear_threshold=rs_bear_threshold,
                                 breakout_period=breakout_period, raw=raw)

    gainers, losers = view_gainers_losers(master, n=top_n)
    day_high, day_low = view_day_high_low(master, n=top_n)
    w52_high, w52_low = view_52w_high_low(master, n=top_n)
    breakout, breakdown = view_range_breakout(master, breakout_period=breakout_period, n=top_n)
    ema_up, ema_down = view_ema200_cross(master, n=top_n)
    sector_agg = view_sector_overview(master)
    lookback_col = f"%Chg ({lookback}d)"
    sector_detail = {s: view_sector_detail(master, s, lookback_col) for s in SECTOR_STOCKS}

    now_ist = datetime.datetime.now(IST)

    return {
        "freshness": freshness,
        "overall": overall_market_signal(master),
        "alerts": alerts_summary(master, breakout_period=breakout_period),
        "bullish": view_most_bullish(master, n=top_n),
        "bearish": view_most_bearish(master, n=top_n),
        "momentum": view_momentum(master, n=top_n),
        "gainers": gainers,
        "losers": losers,
        "surge": view_volume_surge(master, threshold=vol_threshold, n=top_n),
        "day_high": day_high,
        "day_low": day_low,
        "w52_high": w52_high,
        "w52_low": w52_low,
        "breakout": breakout,
        "breakdown": breakdown,
        "ema_up": ema_up,
        "ema_down": ema_down,
        "sector_agg": sector_agg,
        "sector_detail": sector_detail,
        "master": master,
        "fetched_at": now_ist.strftime("%d-%m-%Y %H:%M:%S IST"),
    }
