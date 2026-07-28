"""
FII/DII & Sentiment — separate page (own URL), independent of the Live
Scanner page. Nothing here is ever affected by that page's refresh or
auto-refresh — it only updates when you click the buttons on this page.
"""

import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
from sentiment import (
    parse_optional_float, compute_market_sentiment, parse_fno_text,
    parse_participant_csv, compute_participant_sentiment,
)

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(page_title="FII/DII & Sentiment", layout="wide", page_icon="🧾")

st.title("🧾 FII/DII & Sentiment")
st.caption(
    "Manual entry — FII/DII flows, PCR, VIX, breadth, and F&O OI data aren't "
    "available from free data feeds. Leave any field blank to skip it. This "
    "page is completely separate from the Live Scanner page."
)


def style_row(val):
    if val in ("Bullish", "Strongly Bullish"):
        return "color: #16a34a; font-weight: 600"
    if val in ("Bearish", "Strongly Bearish"):
        return "color: #b91c1c; font-weight: 600"
    return ""


def show(df: pd.DataFrame, style_cols=("Bias",)):
    if df is None or df.empty:
        st.info("No matches right now.")
        return
    present = [c for c in style_cols if c in df.columns]
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    styler = df.style.format(precision=2, subset=numeric_cols) if numeric_cols else df.style
    if present:
        style_fn = getattr(styler, "map", None) or styler.applymap
        styler = style_fn(style_row, subset=present)
    st.dataframe(styler, use_container_width=True, hide_index=True)


if "sentiment_history" not in st.session_state:
    st.session_state["sentiment_history"] = []

colA, colB = st.columns(2)
with colA:
    fii_cash_txt = st.text_input("FII Cash Net (₹ Cr)", placeholder="e.g. 1250 or -800", key="fii_cash")
    fii_fno_txt = st.text_input("FII F&O Index Net (₹ Cr)", placeholder="e.g. 500", key="fii_fno")
    fii_long_txt = st.text_input("FII Long % in Index Futures", placeholder="e.g. 65", key="fii_long")
    pcr_txt = st.text_input("Nifty PCR", placeholder="e.g. 1.15", key="pcr")
with colB:
    dii_cash_txt = st.text_input("DII Cash Net (₹ Cr)", placeholder="e.g. 900", key="dii_cash")
    vix_txt = st.text_input("India VIX", placeholder="e.g. 14.2", key="vix")
    ad_txt = st.text_input("Advance/Decline Ratio", placeholder="e.g. 1.8", key="ad_ratio")

if st.button("Compute Sentiment", type="primary"):
    result = compute_market_sentiment(
        fii_cash=parse_optional_float(fii_cash_txt),
        dii_cash=parse_optional_float(dii_cash_txt),
        fii_fno_index=parse_optional_float(fii_fno_txt),
        fii_long_pct=parse_optional_float(fii_long_txt),
        pcr=parse_optional_float(pcr_txt),
        vix=parse_optional_float(vix_txt),
        ad_ratio=parse_optional_float(ad_txt),
    )
    st.session_state["sentiment_result"] = result
    if result["breakdown"]:
        record = {
            "time": datetime.datetime.now(IST).strftime("%d-%m-%Y %H:%M IST"),
            "label": result["label"],
            "score": result["score"],
            "inputs": {
                "FII Cash Net": fii_cash_txt, "DII Cash Net": dii_cash_txt,
                "FII F&O Index Net": fii_fno_txt, "FII Long %": fii_long_txt,
                "PCR": pcr_txt, "VIX": vix_txt, "A/D Ratio": ad_txt,
            },
            "breakdown": result["breakdown"],
        }
        st.session_state["sentiment_history"].insert(0, record)
        st.session_state["sentiment_history"] = st.session_state["sentiment_history"][:20]

result = st.session_state.get("sentiment_result")
if result and result["breakdown"]:
    st.markdown(
        f"""
        <div style="border: 2px solid {result['color']}; border-radius: 10px; padding: 0.6rem 0.9rem;">
            <span style="font-size: 13px; color: #888;">SENTIMENT:</span>
            <span style="font-size: 18px; font-weight: 700; color: {result['color']};"> {result['label']}</span>
            <span style="font-size: 13px; color: #888;"> (score {result['score']})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Show logic"):
        for item in result["breakdown"]:
            st.write(f"• {item['message']}")

with st.expander("Stock-wise F&O OI data (optional)"):
    st.caption(
        "One stock per line: `TICKER, % price change, % OI change`. "
        "Price↑+OI↑=Long Buildup(bullish) · Price↑+OI↓=Short Covering(bullish) · "
        "Price↓+OI↑=Short Buildup(bearish) · Price↓+OI↓=Long Unwinding(bearish)."
    )
    fno_text = st.text_area("F&O data", height=100, placeholder="RELIANCE, 2.1, 8.5\nTATASTEEL, -1.4, 6.0")
    if st.button("Classify F&O Data"):
        rows, skipped = parse_fno_text(fno_text)
        if rows:
            fno_df = pd.DataFrame(rows)
            show(fno_df)
            bullish_n = (fno_df["Bias"] == "Bullish").sum()
            bearish_n = (fno_df["Bias"] == "Bearish").sum()
            st.caption(f"{bullish_n} bullish, {bearish_n} bearish.")
        else:
            st.info("No valid rows found.")
        if skipped:
            st.caption(f"{skipped} line(s) skipped.")

if st.session_state["sentiment_history"]:
    st.divider()
    st.markdown("**History**")
    for i, rec in enumerate(st.session_state["sentiment_history"]):
        with st.expander(f"{rec['time']} — {rec['label']} (score {rec['score']})"):
            entered = {k: v for k, v in rec["inputs"].items() if v}
            if entered:
                st.write(", ".join(f"{k}: {v}" for k, v in entered.items()))
            for item in rec["breakdown"]:
                st.write(f"• {item['message']}")


# =====================================================================
# NSE PARTICIPANT-WISE OPEN INTEREST — paste NSE's official daily CSV,
# get a tomorrow-facing sentiment reading, keep a rolling 7-day log.
# =====================================================================
st.divider()
st.header("📋 NSE Participant OI → Tomorrow's Sentiment")
st.caption(
    "Paste NSE's official 'Participant wise Open Interest' CSV (published free "
    "daily on nseindia.com) as-is. Reads the FII and DII rows, scores their Index "
    "Futures and Index Options positioning, and gives a bullish/bearish/neutral "
    "read for tomorrow. Keeps the last 7 entries so you can see the week's trend."
)

if "participant_history" not in st.session_state:
    st.session_state["participant_history"] = []

with st.expander("Paste CSV here", expanded=not st.session_state["participant_history"]):
    oi_text = st.text_area(
        "NSE Participant OI CSV",
        height=180,
        placeholder=(
            "Participant wise Open Interest (no. of contracts),2026\n"
            "Client Type,Future Index Long,Future Index Short,Future Stock Long,Future Stock Short,"
            "Option Index Call Long,Option Index Put Long,Option Index Call Short,Option Index Put Short,"
            "Option Stock Call Long,Option Stock Put Long,Option Stock Call Short,Option Stock Put Short,"
            "Total Long Contracts,Total Short Contracts\n"
            "Client,230926,61733,...\nDII,80730,15645,...\nFII,28429,295354,...\nPro,65692,33045,...\n"
            "TOTAL,405777,405777,..."
        ),
    )
    if st.button("Analyze & Save to Weekly Log", type="primary"):
        parsed = parse_participant_csv(oi_text)
        if not parsed:
            st.error("Couldn't read that — make sure it includes the 'Client Type' header row and FII/DII rows.")
        else:
            fii_row = parsed.get("FII")
            dii_row = parsed.get("DII")
            if not fii_row and not dii_row:
                st.error("Found data but no FII or DII row — check the pasted CSV.")
            else:
                p_result = compute_participant_sentiment(fii_row, dii_row)
                st.session_state["participant_result"] = p_result
                if p_result["breakdown"]:
                    record = {
                        "date": datetime.datetime.now(IST).strftime("%d-%m-%Y"),
                        "time": datetime.datetime.now(IST).strftime("%H:%M IST"),
                        "label": p_result["label"],
                        "score": p_result["score"],
                        "breakdown": p_result["breakdown"],
                    }
                    hist = st.session_state["participant_history"]
                    hist.insert(0, record)
                    st.session_state["participant_history"] = hist[:7]  # keep last 7 = 1 week

p_result = st.session_state.get("participant_result")
if p_result and p_result["breakdown"]:
    st.markdown(
        f"""
        <div style="border: 2px solid {p_result['color']}; border-radius: 10px; padding: 0.6rem 0.9rem;">
            <span style="font-size: 13px; color: #888;">TOMORROW'S SENTIMENT:</span>
            <span style="font-size: 18px; font-weight: 700; color: {p_result['color']};"> {p_result['label']}</span>
            <span style="font-size: 13px; color: #888;"> (score {p_result['score']})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Show logic"):
        for item in p_result["breakdown"]:
            st.write(f"• {item['message']}")

if st.session_state["participant_history"]:
    st.markdown(f"**This week's log** ({len(st.session_state['participant_history'])}/7 days)")
    week_df = pd.DataFrame([
        {"Date": r["date"], "Time": r["time"], "Sentiment": r["label"], "Score": r["score"]}
        for r in st.session_state["participant_history"]
    ])
    show(week_df, style_cols=("Sentiment",))
    for rec in st.session_state["participant_history"]:
        with st.expander(f"{rec['date']} {rec['time']} — {rec['label']} (score {rec['score']})"):
            for item in rec["breakdown"]:
                st.write(f"• {item['message']}")
    st.caption(
        "Log lives in this browser session only — it resets if you close the tab "
        "or the app restarts. For permanent storage across days/devices, a small "
        "database would need to be added (tell me if you want that built)."
    )
