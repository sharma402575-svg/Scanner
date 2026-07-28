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
    scan_sector, most_bullish, most_bearish, top_gainers_losers,
    momentum_scan, volume_surge_scan, sector_overview_with_detail,
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
    vol_th = st.slider("Volume surge threshold (x avg)", 1.5, 10.0, 2.0, 0.5)
    st.caption("Data: Yahoo Finance (delayed ~15 min). NSE stocks.")
    st.divider()
    st.markdown("**Reading RSI(14) / ATR(14)**")
    st.caption(
        "RSI > 70 = overbought, < 30 = oversold. "
        "ATR = average daily range; 'Suggested Stop' = LTP − 1.5×ATR, "
        "a simple volatility-based stop for long swing trades."
    )


def style_signal(val):
    if val in ("Bullish", "Up"):
        return "color: #16a34a; font-weight: 600"
    if val in ("Bearish", "Down"):
        return "color: #dc2626; font-weight: 600"
    return ""


def show(df: pd.DataFrame, signal_col: str = "Signal"):
    if df.empty:
        st.info("No data returned — try again in a moment (Yahoo Finance may be rate-limiting).")
        return
    if signal_col and signal_col in df.columns:
        st.dataframe(df.style.applymap(style_signal, subset=[signal_col]),
                     use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["🚀 Most Bullish / Bearish", "🔥 Momentum", "📈 Gainers & Losers",
     "🧭 Sector Overview", "⚡ Volume Surge", "🔍 Single Sector"]
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
    st.caption("Ranked by short-term rate-of-change combined with volume surge — "
               "useful for swing entries; check RSI in Single Sector before chasing.")
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
    st.caption("Expand a sector below to see every stock in it with its own R Factor and bias.")
    if st.button("Run", key="sector_btn"):
        with st.spinner("Scanning all sectors..."):
            agg, per_sector = sector_overview_with_detail(
                lookback=lookback, rs_bull_threshold=bull_th, rs_bear_threshold=bear_th
            )
            show(agg, signal_col="Sector Bias")
            st.divider()
            for sector in agg["Sector"]:
                with st.expander(f"{sector} — all stocks"):
                    show(per_sector[sector])

with tab5:
    st.subheader("Live Volume Surge Alerts")
    st.caption(
        "Stocks trading at an unusual multiple of their 20-day average volume "
        "right now — often an early tell for intraday breakouts or news-driven moves."
    )
    if st.button("Run", key="surge_btn"):
        with st.spinner("Scanning..."):
            df = volume_surge_scan(threshold=vol_th, n=top_n)
            show(df, signal_col="Direction")

with tab6:
    st.subheader("Drill Into One Sector")
    sector = st.selectbox("Sector", list(SECTOR_STOCKS.keys()))
    if st.button("Run", key="single_btn"):
        with st.spinner(f"Scanning {sector}..."):
            df = scan_sector(sector, lookback=lookback,
                              rs_bull_threshold=bull_th, rs_bear_threshold=bear_th)
            show(df)
