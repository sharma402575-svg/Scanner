import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="1-Min Breakout Momentum Scanner", layout="wide")

st.title("⚡ 1-Minute Intraday Breakout Scanner (F&O)")
st.write(
    "Scans liquid F&O stocks to detect momentum breakouts past their first"
    " 1-minute candle high/low."
)

# List of F&O stocks to scan
default_stocks = [
    "RELIANCE.NS",
    "TATAMOTORS.NS",
    "SBIN.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "TATASTEEL.NS",
    "AXISBANK.NS",
    "M&M.NS",
]

if st.button("Run Live 1-Min Breakout Scan"):
  with st.spinner("Fetching live intraday market data..."):
    try:
      data = yf.download(
          default_stocks,
          period="1d",
          interval="1m",
          group_by="ticker",
          progress=False,
      )

      results = []
      for stock in default_stocks:
        df = data[stock].dropna()
        if len(df) < 2:
          continue

        f_high = df.iloc[0]["High"]
        f_low = df.iloc[0]["Low"]
        c_close = df.iloc[-1]["Close"]
        c_time = df.index[-1].strftime("%H:%M:%S")

        status = "Consolidating / Inside Range"
        if c_close > f_high:
          status = "🚀 Bullish Breakout (Above High)"
        elif c_close < f_low:
          status = "🔻 Bearish Breakdown (Below Low)"

        results.append({
            "Stock": stock.replace(".NS", ""),
            "1st Candle High": round(f_high, 2),
            "1st Candle Low": round(f_low, 2),
            "Latest Close": round(c_close, 2),
            "Time": c_time,
            "Status": status,
        })

      res_df = pd.DataFrame(results)
      st.success("Scan Completed Successfully!")
      st.dataframe(res_df, use_container_width=True)

    except Exception as e:
      st.error(f"Error fetching live data: {e}")
else:
  st.info("Click the button above to execute the live breakout scan.")
