import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="1-Min Breakout Momentum Scanner", layout="wide")

st.title("⚡ 1-Minute Intraday Breakout Scanner (F&O)")
st.write(
    "Scans liquid F&O stocks, sorts them by **momentum aggressiveness**, and"
    " color-codes bullish/bearish breakouts."
)

default_stocks = [
    "RELIANCE.NS",
    "TATAMotors.NS",
    "SBIN.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "TATASTEEL.NS",
    "AXISBANK.NS",
    "M&M.NS",
    "NTPC.NS",
    "RELINFRA.NS",
    "HDFCBANK.NS",
    "TCS.NS",
]


def color_coding(val):
  if "Bullish" in str(val):
    return "color: #22c55e; font-weight: bold;"
  elif "Bearish" in str(val):
    return "color: #ef4444; font-weight: bold;"
  return "color: #94a3b8;"


if st.button("Run Aggressive Breakout Scan"):
  with st.spinner("Fetching live intraday data and sorting by momentum..."):
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

        # Calculate aggressiveness metric (% distance from breakout level)
        if c_close > f_high:
          status = "🚀 Bullish Breakout"
          aggression_score = ((c_close - f_high) / f_high) * 100
        elif c_close < f_low:
          status = "🔻 Bearish Breakdown"
          aggression_score = ((f_low - c_close) / f_low) * 100
        else:
          status = "Consolidating"
          aggression_score = 0.0

        results.append({
            "Stock": stock.replace(".NS", ""),
            "Status": status,
            "Aggression Score (%)": round(aggression_score, 3),
            "Latest Close": round(c_close, 2),
            "1st Candle High": round(f_high, 2),
            "1st Candle Low": round(f_low, 2),
            "Time": c_time,
        })

      if results:
        res_df = pd.DataFrame(results)

        # Sort by aggression score descending so highest momentum stocks appear first
        res_df = res_df.sort_values(
            by="Aggression Score (%)", ascending=False
        ).reset_index(drop=True)

        st.success(
            "Scan Complete! Sorted by highest momentum aggressiveness first."
        )

        # Apply styling
        styled_df = res_df.style.map(
            color_coding, subset=["Status"]
        ).format({
            "Aggression Score (%)": "{:.3f}%",
            "Latest Close": "{:.2f}",
            "1st Candle High": "{:.2f}",
            "1st Candle Low": "{:.2f}",
        })

        st.dataframe(styled_df, use_container_width=True)
      else:
        st.warning("No data retrieved for the selected stocks.")

    except Exception as e:
      st.error(f"Error executing scan: {e}")
else:
  st.info(
      "Click the button above to run the live aggressive momentum scan."
  )
