"""
FII/DII & Sentiment — separate page (own URL), independent of the Live
Scanner page. Upload NSE's Participant OI file, get a sentiment reading
from FII/DII positioning, and it's automatically logged to a weekly
history you can look back through.
"""

import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
from sentiment import parse_fno_text, parse_participant_csv, compute_participant_sentiment

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(page_title="FII/DII & Sentiment", layout="wide", page_icon="🧾")

st.title("🧾 FII/DII & Sentiment")
st.caption(
    "Upload NSE's official 'Participant wise Open Interest' CSV (published free "
    "daily on nseindia.com) — read automatically. This page is separate from the "
    "Live Scanner and unaffected by its refresh."
)


def style_row(val):
    if val in ("Bullish", "Strongly Bullish", "Bullish for tomorrow"):
        return "color: #16a34a; font-weight: 600"
    if val in ("Bearish", "Strongly Bearish", "Bearish for tomorrow"):
        return "color: #b91c1c; font-weight: 600"
    return ""


def show(df: pd.DataFrame, style_cols=("Bias", "Sentiment")):
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


if "participant_history" not in st.session_state:
    st.session_state["participant_history"] = []


def _process_participant_csv(text: str):
    parsed = parse_participant_csv(text)
    if not parsed:
        st.error("Couldn't read that — make sure it includes the 'Client Type' header row and FII/DII rows.")
        return
    fii_row = parsed.get("FII")
    dii_row = parsed.get("DII")
    if not fii_row and not dii_row:
        st.error("Found data but no FII or DII row — check the file.")
        return

    result = compute_participant_sentiment(fii_row, dii_row)
    st.session_state["participant_result"] = result
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

result = st.session_state.get("participant_result")
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
    with st.expander("Show logic", expanded=True):
        for item in result["breakdown"]:
            st.write(f"• {item['message']}")

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
