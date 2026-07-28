"""
FII/DII & Sentiment — separate page (own URL), independent of the Live
Scanner page. Nothing here is ever affected by that page's refresh or
auto-refresh — it only updates when you act on this page.

Everything below feeds into ONE combined "Tomorrow's Sentiment" score —
not separate scores in separate boxes. Fill in whatever macro numbers you
have (or fetch VIX/PCR live), then upload the Participant OI file; both
sets of factors are combined into a single end-of-day call for tomorrow.
"""

import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
from sentiment import parse_optional_float, parse_fno_text, parse_participant_csv, compute_tomorrow_sentiment
from live_data import fetch_india_vix, fetch_nifty_pcr

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(page_title="FII/DII & Sentiment", layout="wide", page_icon="🧾")

st.title("🧾 FII/DII & Sentiment — Tomorrow's Call")
st.caption(
    "Fill in what you have below (VIX/PCR can be fetched live), then upload the "
    "NSE Participant OI file — everything combines into ONE Tomorrow's Sentiment "
    "reading at the bottom, with the full logic shown. This page is separate "
    "from the Live Scanner and unaffected by its refresh."
)


def style_row(val):
    if val in ("Bullish", "Strongly Bullish", "Bullish for tomorrow", "Strongly Bullish for tomorrow"):
        return "color: #16a34a; font-weight: 600"
    if val in ("Bearish", "Strongly Bearish", "Bearish for tomorrow", "Strongly Bearish for tomorrow"):
        return "color: #b91c1c; font-weight: 600"
    return ""


def show(df: pd.DataFrame, style_cols=("Bias", "Sentiment")):
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


if "participant_history" not in st.session_state:
    st.session_state["participant_history"] = []

# ---------------------------------------------------------------------
# STEP 1 — macro inputs (India VIX, Nifty PCR, cash flows, breadth)
# ---------------------------------------------------------------------
st.subheader("1. Market-wide inputs")

if st.button("🌐 Fetch Live India VIX & Nifty PCR"):
    with st.spinner("Fetching..."):
        vix_val = fetch_india_vix()
        pcr_val, ce_oi, pe_oi = fetch_nifty_pcr()
    msgs = []
    if vix_val is not None:
        st.session_state["vix"] = str(vix_val)
        msgs.append(f"India VIX = {vix_val}")
    else:
        msgs.append("India VIX fetch failed")
    if pcr_val is not None:
        st.session_state["pcr"] = str(pcr_val)
        msgs.append(f"Nifty PCR = {pcr_val} (Call OI {ce_oi:,.0f}, Put OI {pe_oi:,.0f})")
    else:
        msgs.append("Nifty PCR fetch failed (NSE sometimes blocks automated requests — enter it manually below)")
    st.info(" · ".join(msgs))

colA, colB = st.columns(2)
with colA:
    fii_cash_txt = st.text_input("FII Cash Net (₹ Cr)", placeholder="e.g. 1250 or -800", key="fii_cash")
    pcr_txt = st.text_input("Nifty PCR", placeholder="e.g. 1.15", key="pcr")
with colB:
    dii_cash_txt = st.text_input("DII Cash Net (₹ Cr)", placeholder="e.g. 900", key="dii_cash")
    vix_txt = st.text_input("India VIX", placeholder="e.g. 14.2", key="vix")
ad_txt = st.text_input("Advance/Decline Ratio (optional)", placeholder="e.g. 1.8", key="ad_ratio")

st.divider()

# ---------------------------------------------------------------------
# STEP 2 — FII/DII positioning from NSE Participant OI file
# ---------------------------------------------------------------------
st.subheader("2. FII/DII positioning (NSE Participant OI)")
st.caption(
    "Upload NSE's official 'Participant wise Open Interest' CSV (published free "
    "daily on nseindia.com) — read automatically. This adds FII/DII Index "
    "Futures and Options positioning into the combined score below."
)


def _process_participant_csv(text: str):
    parsed = parse_participant_csv(text)
    fii_row = dii_row = None
    if parsed:
        fii_row = parsed.get("FII")
        dii_row = parsed.get("DII")
        if not fii_row and not dii_row:
            st.error("Found data but no FII or DII row — check the file.")
            return
    else:
        st.error("Couldn't read that — make sure it includes the 'Client Type' header row and FII/DII rows.")
        return

    result = compute_tomorrow_sentiment(
        fii_cash=parse_optional_float(fii_cash_txt),
        dii_cash=parse_optional_float(dii_cash_txt),
        pcr=parse_optional_float(pcr_txt),
        vix=parse_optional_float(vix_txt),
        ad_ratio=parse_optional_float(ad_txt),
        fii_row=fii_row,
        dii_row=dii_row,
    )
    st.session_state["tomorrow_result"] = result
    if result["breakdown"]:
        record = {
            "date": datetime.datetime.now(IST).strftime("%d-%m-%Y"),
            "time": datetime.datetime.now(IST).strftime("%H:%M IST"),
            "label": result["label"],
            "score": result["score"],
            "breakdown": result["breakdown"],
        }
        hist = st.session_state["participant_history"]
        if not hist or hist[0]["date"] != record["date"] or hist[0]["score"] != record["score"]:
            hist.insert(0, record)
            st.session_state["participant_history"] = hist[:7]  # keep last 7 = 1 week
        st.success(f"Saved to weekly log: {result['label']} (score {result['score']})")


uploaded_file = st.file_uploader("Upload NSE Participant OI CSV", type=["csv"])
if uploaded_file is not None:
    csv_text = uploaded_file.read().decode("utf-8", errors="ignore")
    _process_participant_csv(csv_text)

with st.expander("Or paste CSV instead"):
    oi_text = st.text_area(
        "NSE Participant OI CSV",
        height=180,
        placeholder=(
            "Participant wise Open Interest (no. of contracts),2026\n"
            "Client Type,Future Index Long,Future Index Short,...\n"
            "Client,230926,61733,...\nDII,80730,15645,...\nFII,28429,295354,...\n"
            "Pro,65692,33045,...\nTOTAL,405777,405777,..."
        ),
    )
    if st.button("Analyze Pasted Data", type="primary"):
        _process_participant_csv(oi_text)

if st.button("Compute from macro inputs only (no file)"):
    result = compute_tomorrow_sentiment(
        fii_cash=parse_optional_float(fii_cash_txt),
        dii_cash=parse_optional_float(dii_cash_txt),
        pcr=parse_optional_float(pcr_txt),
        vix=parse_optional_float(vix_txt),
        ad_ratio=parse_optional_float(ad_txt),
    )
    st.session_state["tomorrow_result"] = result
    if result["breakdown"]:
        record = {
            "date": datetime.datetime.now(IST).strftime("%d-%m-%Y"),
            "time": datetime.datetime.now(IST).strftime("%H:%M IST"),
            "label": result["label"], "score": result["score"], "breakdown": result["breakdown"],
        }
        hist = st.session_state["participant_history"]
        if not hist or hist[0]["date"] != record["date"] or hist[0]["score"] != record["score"]:
            hist.insert(0, record)
            st.session_state["participant_history"] = hist[:7]

st.divider()

# ---------------------------------------------------------------------
# RESULT — one combined score
# ---------------------------------------------------------------------
st.subheader("3. Tomorrow's Sentiment")
result = st.session_state.get("tomorrow_result")
if result and result["breakdown"]:
    st.markdown(
        f"""
        <div style="border: 2px solid {result['color']}; border-radius: 10px; padding: 0.6rem 0.9rem;">
            <span style="font-size: 13px; color: #888;">TOMORROW'S SENTIMENT:</span>
            <span style="font-size: 18px; font-weight: 700; color: {result['color']};"> {result['label']}</span>
            <span style="font-size: 13px; color: #888;"> (score {result['score']})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Show logic", expanded=True):
        for item in result["breakdown"]:
            st.write(f"• {item['message']}")
else:
    st.info("Fill in step 1 and/or upload the file in step 2 to get a reading.")

if st.session_state["participant_history"]:
    st.markdown(f"**This week's log** ({len(st.session_state['participant_history'])}/7 days)")
    week_df = pd.DataFrame([
        {"Date": r["date"], "Time": r["time"], "Sentiment": r["label"], "Score": r["score"]}
        for r in st.session_state["participant_history"]
    ])
    show(week_df)
    for rec in st.session_state["participant_history"]:
        with st.expander(f"{rec['date']} {rec['time']} — {rec['label']} (score {rec['score']})"):
            for item in rec["breakdown"]:
                st.write(f"• {item['message']}")
    st.caption(
        "Log lives in this browser session only — it resets if you close the tab "
        "or the app restarts. For permanent storage across days/devices, a small "
        "database would need to be added (tell me if you want that built)."
    )

st.divider()
with st.expander("Stock-wise F&O OI data (optional, separate from the score above)"):
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
