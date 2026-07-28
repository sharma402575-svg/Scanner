"""
Sector Trade Scanner — single-page Streamlit dashboard

Run with:
    streamlit run app.py

Requires:
    pip install -r requirements.txt
"""

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from sectors import SECTOR_STOCKS
from scanner import run_full_scan_bundle

st.set_page_config(page_title="Sector Trade Scanner", layout="wide")

with st.sidebar:
    st.header("Settings")
    lookback = st.slider("R Factor lookback (trading days)", 5, 60, 20)
    bull_th = st.slider("Bullish R Factor threshold (%)", 0.0, 10.0, 2.0, 0.5)
    bear_th = st.slider("Bearish R Factor threshold (%)", -10.0, 0.0, -2.0, 0.5)
    top_n = st.slider("How many rows per list", 5, 30, 15)
    vol_th = st.slider("Volume surge threshold (x avg)", 1.5, 10.0, 2.0, 0.5)
    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=False)
    interval_min = st.selectbox("Refresh every", [1, 2, 5, 10, 15], index=2,
                                 disabled=not auto_refresh, format_func=lambda x: f"{x} min")
    st.divider()
    st.caption("Data: Yahoo Finance (delayed ~15-20 min). NSE stocks.")
    st.markdown("**How Trade Signal is calculated**")
    st.caption(
        "Points system: R Factor vs sector (±2), trend vs 20DMA (±1), "
        "RSI zone (±1), momentum+volume (±1), proximity to 52w high/low "
        "(±1). Score ≥4 Strong Buy, ≥2 Buy, ≤-4 Strong Sell, ≤-2 Sell, "
        "else Hold. This is a rules-based heuristic, not financial advice."
    )

if auto_refresh:
    st_autorefresh(interval=interval_min * 60 * 1000, key="auto_refresh_timer")

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("📊 Sector Trade Scanner")
with col_btn:
    st.write("")
    manual_refresh = st.button("🔄 Refresh all data", type="primary")

should_run = manual_refresh or auto_refresh or "bundle" not in st.session_state
if should_run:
    with st.spinner("Fetching live data and running all scans..."):
        st.session_state["bundle"] = run_full_scan_bundle(
            lookback=lookback, rs_bull_threshold=bull_th, rs_bear_threshold=bear_th,
            vol_threshold=vol_th, top_n=top_n,
        )

bundle = st.session_state.get("bundle")
if not bundle:
    st.info("Click **Refresh all data** to load the scanner.")
    st.stop()


# ---------- OVERALL MARKET SIGNAL — always first thing visible ----------

overall = bundle["overall"]
f = bundle["freshness"]

signal_colors = {
    "Buy": ("#16a34a", "🟢"), "Sell": ("#dc2626", "🔴"), "Neutral": ("#6b7280", "⚪"),
}
color, dot = signal_colors.get(overall["label"], ("#6b7280", "⚪"))

st.markdown(
    f"""
    <div style="border: 2px solid {color}; border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;">
        <div style="font-size: 14px; color: #888; margin-bottom: 4px;">OVERALL MARKET SIGNAL · {overall['total']} stocks scanned</div>
        <div style="font-size: 32px; font-weight: 700; color: {color};">{dot} {overall['label']}</div>
        <div style="font-size: 14px; margin-top: 8px;">
            Avg score: <b>{overall['avg_score']}</b> &nbsp;|&nbsp;
            Buy-leaning: <b style="color:#16a34a">{overall['pct_buy']}%</b> &nbsp;|&nbsp;
            Sell-leaning: <b style="color:#dc2626">{overall['pct_sell']}%</b> &nbsp;|&nbsp;
            Hold: <b>{overall['pct_hold']}%</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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


def style_row(val):
    if val in ("Bullish", "Up", "Buy", "Strong Buy"):
        return "color: #16a34a; font-weight: 600"
    if val in ("Bearish", "Down", "Sell", "Strong Sell"):
        return "color: #dc2626; font-weight: 600"
    return ""


def show(df: pd.DataFrame, style_cols=("Trend Signal", "Trade Signal", "Sector Bias", "Direction")):
    if df is None or df.empty:
        st.info("No matches right now.")
        return
    present = [c for c in style_cols if c in df.columns]
    if present:
        styler = df.style
        style_fn = getattr(styler, "map", None) or styler.applymap
        st.dataframe(style_fn(style_row, subset=present), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


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
st.header("🧭 Sector overview")
st.caption("Expand a sector to see every stock in it with its own R Factor, trend and trade signal.")
show(bundle["sector_agg"])
for sector in bundle["sector_agg"]["Sector"]:
    with st.expander(f"{sector} — all stocks"):
        show(bundle["sector_detail"][sector])
