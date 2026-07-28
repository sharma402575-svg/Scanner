"""
Sector Trade Scanner — Streamlit dashboard

Run with:
    streamlit run app.py

Requires:
    pip install -r requirements.txt
"""

import streamlit as st
import pandas as pd
from sectors import SECTOR_STOCKS
from scanner import (
    scan_sector, full_market_scan, most_bullish, most_bearish,
    top_gainers_losers, momentum_scan, sector_overview,
)

st.set_page_config(page_title="Sector Trade Scanner", layout="wide")

st.title("📊 Sector Trade Scanner")
st.caption(
    "R Factor = stock's return minus its sector index's return over the "
    "same period. Positive = beating the sector (bullish tilt), "
    "negative = lagging it (bearish tilt)."
)

with st.sidebar:
    st.header("Settings")
    lookback = st.slider("R Factor lookback (trading days)", 5, 60, 20)
    bull_th = st.slider("Bullish R Factor threshold (%)", 0.0, 10.0, 2.0, 0.5)
    bear_th = st.slider("Bearish R Factor threshold (%)", -10.0, 0.0, -2.0, 0.5)
    top_n = st.slider("How many rows per list", 5, 30, 15)
    st.caption("Data: Yahoo Finance (delayed ~15 min). NSE stocks.")


def style_signal(val):
    if val == "Bullish":
        return "color: #16a34a; font-weight: 600"
    if val == "Bearish":
        return "color: #dc2626; font-weight: 600"
    return ""


def show(df: pd.DataFrame, signal_col: str = "Signal"):
    if df.empty:
        st.info("No data returned — try again in a moment (Yahoo Finance may be rate-limiting).")
        return
    if signal_col in df.columns:
        st.dataframe(df.style.applymap(style_signal, subset=[signal_col]),
                     use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🚀 Most Bullish / Bearish", "🔥 Momentum", "📈 Gainers & Losers",
     "🧭 Sector Overview", "🔍 Single Sector"]
)

with tab1:
    st.subheader("Most Bullish Stocks (whole market)")
    if st.button("Run", key="bullish_btn"):
        with st.spinner("Scanning..."):
            df = most_bullish(n=top_n, lookback=lookback,
                               rs_bull_threshold=bull_th, rs_bear_threshold=bear_th)
            show(df)

    st.subheader("Most Bearish Stocks (whole market)")
    if st.button("Run", key="bearish_btn"):
        with st.spinner("Scanning..."):
            df = most_bearish(n=top_n, lookback=lookback,
                               rs_bull_threshold=bull_th, rs_bear_threshold=bear_th)
            show(df)

with tab2:
    st.subheader("High Momentum Stocks")
    st.caption("Ranked by short-term price rate-of-change combined with volume surge — "
               "fast movers backed by real trading activity.")
    if st.button("Run", key="momentum_btn"):
        with st.spinner("Scanning..."):
            df = momentum_scan(n=top_n)
            show(df, signal_col=None)

with tab3:
    st.subheader("Top Gainers & Losers (today)")
    if st.button("Run", key="gl_btn"):
        with st.spinner("Scanning..."):
            gainers, losers = top_gainers_losers(n=top_n)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top Gainers**")
                show(gainers, signal_col=None)
            with c2:
                st.markdown("**Top Losers**")
                show(losers, signal_col=None)

with tab4:
    st.subheader("Which Sectors Are Turning Bullish / Bearish")
    if st.button("Run", key="sector_btn"):
        with st.spinner("Scanning all sectors..."):
            df = sector_overview(lookback=lookback)
            show(df, signal_col="Sector Bias")

with tab5:
    st.subheader("Drill Into One Sector")
    sector = st.selectbox("Sector", list(SECTOR_STOCKS.keys()))
    if st.button("Run", key="single_btn"):
        with st.spinner(f"Scanning {sector}..."):
            df = scan_sector(sector, lookback=lookback,
                              rs_bull_threshold=bull_th, rs_bear_threshold=bear_th)
            show(df)
