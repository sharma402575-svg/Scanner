import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="1-Min Breakout Momentum Scanner", layout="wide")

st.title("⚡ Comprehensive F&O 1-Minute Breakout Scanner")
st.write(
    "Scans liquid F&O stocks across the market, calculates momentum"
    " aggressiveness, and sorts the fastest-moving stocks to the top."
)

# Comprehensive list of liquid NSE F&O stocks
fo_stocks = [
    "RELIANCE.NS",
    "TATAMOTORS.NS",
    "SBIN.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "HDFCBANK.NS",
    "TCS.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "LT.NS",
    "ITC.NS",
    "BHARTIARTL.NS",
    "BAJFINANCE.NS",
    "TATASTEEL.NS",
    "SUNPHARMA.NS",
    "M&M.NS",
    "MARUTI.NS",
    "WIPRO.NS",
    "HCLTECH.NS",
    "TITAN.NS",
    "NTPC.NS",
    "POWERGRID.NS",
    "ONGC.NS",
    "COALINDIA.NS",
    "ADANIENT.NS",
    "ADANIPORTS.NS",
    "BAJAJ-AUTO.NS",
    "JSWSTEEL.NS",
    "GRASIM.NS",
    "HINDALCO.NS",
]


def color_coding(val):
  if "Bullish" in str(val):
    return "color: #22c55e; font-weight: bold;"
  elif "Bearish" in str(val):
    return "color: #ef4444; font-weight: bold;"
  return "color: #94a3b8;"


if st.button("Run Full F&O Momentum Scan"):
  with st.spinner(
      "Scanning all F&O stocks and calculating momentum aggression..."
  ):
    try:
      # Batch download intraday 1-minute data
      data = yf.download(
          fo_stocks,
          period="1d",
          interval="1m",
          group_by="ticker",
          progress=False,
      )

      results = []
      for stock in fo_stocks:
        try:
          # Handle multi-index structure from batch download
          df = data[stock].dropna()
          if len(df) < 2:
            continue

          f_high = df.iloc[0]["High"]
          f_low = df.iloc[0]["Low"]
          c_close = df.iloc[-1]["Close"]
          c_time = df.index[-1].strftime("%H:%M:%S")

          # Calculate momentum aggression score (% distance from breakout level)
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
        except Exception:
          continue

      if results:
        res_df = pd.DataFrame(results)

        # Sort by highest aggression score so most active momentum stocks appear first
        res_df = res_df.sort_values(
            by="Aggression Score (%)", ascending=False
        ).reset_index(drop=True)

        st.success(
            f"Successfully scanned {len(results)} F&O stocks! Sorted by highest"
            " aggression first."
        )

        # Apply color coding to the status column
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
        st.warning(
            "No data retrieved. Ensure the market is open or data sources are"
            " responding."
        )

    except Exception as e:
      st.error(f"Error executing scan: {e}")
else:
  st.info(
      "Click the button above to execute the live scan across all listed F&O"
      " stocks."
  )
