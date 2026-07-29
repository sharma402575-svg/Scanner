"""
Sector Trade Scanner — Home page (Live Scanner)

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from sectors import SECTOR_STOCKS
from scanner import run_full_scan_bundle

st.set_page_config(page_title="Sector Trade Scanner", layout="wide", page_icon="📊")

# ---------------------------------------------------------------------
# Settings persist across refresh/auto-refresh AND across a real browser
# reload by storing them in the URL's query string. Reloading the page,
# or sharing the URL, keeps whatever settings were last used.
# ---------------------------------------------------------------------
qp = st.query_params


def _qp_num(name, default, cast=float):
    val = qp.get(name)
    if val is None:
        return default
    try:
        return cast(val)
    except (TypeError, ValueError):
        return default


with st.sidebar:
    st.header("Settings")
    lookback = st.slider("R Factor lookback (trading days)", 5, 60, _qp_num("lookback", 20, int))
    bull_th = st.slider("Bullish R Factor threshold (%)", 0.0, 10.0, _qp_num("bull_th", 2.0), 0.5)
    bear_th = st.slider("Bearish R Factor threshold (%)", -10.0, 0.0, _qp_num("bear_th", -2.0), 0.5)
    breakout_period = st.slider("Range breakout lookback (days)", 5, 60, _qp_num("breakout", 20, int))
    top_n = st.slider("How many rows per list", 5, 30, _qp_num("topn", 15, int))
    vol_th = st.slider("Volume surge threshold (x avg)", 1.5, 10.0, _qp_num("volth", 2.0), 0.5)
    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=bool(_qp_num("auto", 0, int)))
    interval_options = [1, 2, 5, 10, 15]
    default_interval = _qp_num("interval", 5, int)
    default_idx = interval_options.index(default_interval) if default_interval in interval_options else 2
    interval_min = st.selectbox("Refresh every", interval_options, index=default_idx,
                                 disabled=not auto_refresh, format_func=lambda x: f"{x} min")
    st.divider()
    st.caption("Data: Yahoo Finance (delayed ~15-20 min). NSE stocks. Times shown in IST.")
    st.markdown("**How Trade Signal is calculated**")
    st.caption(
        "Points: R Factor vs sector (±2), trend vs 20DMA (±1), RSI zone (±1), "
        "momentum+volume (±1), 52w high/low proximity (±1), range breakout/"
        "breakdown (±1). Score ≥4 Strong Buy, ≥2 Buy, ≤-4 Strong Sell, ≤-2 "
        "Sell, else Hold. Rules-based heuristic — not financial advice."
    )

# Sync current settings back into the URL so a reload/share keeps them.
st.query_params["lookback"] = str(lookback)
st.query_params["bull_th"] = str(bull_th)
st.query_params["bear_th"] = str(bear_th)
st.query_params["breakout"] = str(breakout_period)
st.query_params["topn"] = str(top_n)
st.query_params["volth"] = str(vol_th)
st.query_params["auto"] = str(int(auto_refresh))
st.query_params["interval"] = str(interval_min)

if auto_refresh:
    st_autorefresh(interval=interval_min * 60 * 1000, key="auto_refresh_timer")

st.title("📊 Sector Trade Scanner — Live Scanner")


def style_row(val):
    if val in ("Bullish", "Up", "Buy", "Strong Buy", "Strongly Bullish", True):
        return "color: #16a34a; font-weight: 600"
    if val in ("Bearish", "Down", "Sell", "Strong Sell", "Strongly Bearish"):
        return "color: #b91c1c; font-weight: 600"
    return ""


def show(df: pd.DataFrame, style_cols=("Trend Signal", "Trade Signal", "Sector Bias", "Direction", "Bias")):
    """
    Renders a table in a FIXED order (whatever the scan already sorted
    it by — most gainers/most bearish/etc. on top) with no interactive
    column-sorting, so the order can never get scrambled by clicking a
    header. Values shown to 2 decimals.
    """
    if df is None or df.empty:
        st.info("No matches right now.")
        return
    df2 = df.reset_index(drop=True).copy()
    present = [c for c in style_cols if c in df2.columns]
    numeric_cols = df2.select_dtypes(include="number").columns.tolist()
    styler = df2.style.format(precision=2, subset=numeric_cols) if numeric_cols else df2.style
    if present:
        style_fn = getattr(styler, "map", None) or styler.applymap
        styler = style_fn(style_row, subset=present)
    hide_fn = getattr(styler, "hide", None)
    styler = hide_fn(axis="index") if hide_fn else styler.hide_index()
    st.table(styler)


col_btn, _ = st.columns([1, 4])
with col_btn:
    manual_refresh = st.button("🔄 Refresh all data", type="primary")

should_run = manual_refresh or auto_refresh or "bundle" not in st.session_state
if should_run:
    with st.spinner("Fetching live data and running all scans..."):
        st.session_state["bundle"] = run_full_scan_bundle(
            lookback=lookback, rs_bull_threshold=bull_th, rs_bear_threshold=bear_th,
            vol_threshold=vol_th, breakout_period=breakout_period, top_n=top_n,
        )

bundle = st.session_state.get("bundle")
if not bundle:
    st.info("Click **Refresh all data** to load the scanner.")
    st.stop()

f = bundle["freshness"]
if f["is_stale"]:
    st.warning(
        f"⚠️ Data as of **{f['last_data_date']}** (today is {f['today']}) · "
        f"last fetched {bundle['fetched_at']}. Stale is expected right after "
        f"market close — Yahoo can take a few hours to sync the final bar."
    )
else:
    st.success(f"✅ Data as of **{f['last_data_date']}** · last fetched {bundle['fetched_at']}")
if auto_refresh:
    st.caption(f"Auto-refreshing every {interval_min} min.")

st.caption(
    "R Factor = stock's return minus its sector index's return. Trade Signal "
    "is a rules-based heuristic (see sidebar) — not financial advice."
)

st.divider()
st.header("🚀 Most bullish / bearish (whole market)")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Bullish")
    show(bundle["bullish"])
with c2:
    st.subheader("Bearish")
    show(bundle["bearish"])

st.divider()
st.header("📐 200 EMA crossovers")
st.caption("Stocks that just crossed above/below their 200-day EMA — a widely-watched long-term trend flip.")
c11, c12 = st.columns(2)
with c11:
    st.subheader("Crossed above (bullish)")
    show(bundle["ema_up"])
with c12:
    st.subheader("Crossed below (bearish)")
    show(bundle["ema_down"])

st.divider()
st.header("🔥 High momentum stocks")
st.caption("Ranked by short-term rate-of-change combined with volume surge.")
show(bundle["momentum"])

st.divider()
st.header("📈 Gainers & losers (today)")
c3, c4 = st.columns(2)
with c3:
    st.subheader("Top gainers")
    show(bundle["gainers"])
with c4:
    st.subheader("Top losers")
    show(bundle["losers"])

st.divider()
st.header("⚡ Live volume surge alerts")
st.caption("Stocks trading at an unusual multiple of their 20-day average volume right now.")
show(bundle["surge"])

st.divider()
st.header("📍 Day high / day low stocks")
st.caption("Stocks trading at (or within 0.3% of) their day's high or low.")
c5, c6 = st.columns(2)
with c5:
    st.subheader("At day high")
    show(bundle["day_high"])
with c6:
    st.subheader("At day low")
    show(bundle["day_low"])

st.divider()
st.header("📅 52-week high / low")
st.caption("Stocks within 3% of their 52-week high or low.")
c7, c8 = st.columns(2)
with c7:
    st.subheader("Near 52w high")
    show(bundle["w52_high"])
with c8:
    st.subheader("Near 52w low")
    show(bundle["w52_low"])

st.divider()
st.header("📦 Range breakout / breakdown")
st.caption(f"Close breaking above/below its prior {breakout_period}-day range.")
c9, c10 = st.columns(2)
with c9:
    st.subheader("Breakout")
    show(bundle["breakout"])
with c10:
    st.subheader("Breakdown")
    show(bundle["breakdown"])

st.divider()
st.header("🧭 Sector overview")
st.caption("Expand a sector to see every stock in it with its own R Factor, trend and trade signal.")
show(bundle["sector_agg"])
for sector in bundle["sector_agg"]["Sector"]:
    stocks_in_sector = len(SECTOR_STOCKS[sector])
    shown = len(bundle["sector_detail"][sector])
    with st.expander(f"{sector} — {shown}/{stocks_in_sector} stocks"):
        show(bundle["sector_detail"][sector])
