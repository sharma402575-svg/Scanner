import pandas as pd
import streamlit as st
import yfinance as yf

# Optional component for autorefresh if available, otherwise using st_autorefresh or manual loop logic
try:
  from streamlit_autorefresh import st_autorefresh

  has_autorefresh = True
except ImportError:
  has_autorefresh = False

st.set_page_config(
    page_title="1-Min Breakout Momentum Scanner (F&O)", layout="wide"
)

st.title("⚡ Comprehensive F&O 1-Minute Breakout Scanner")
st.write(
    "Scans liquid F&O stocks, sorts them by momentum aggression, and features"
    " an auto-refresh toggle."
)

# Sidebar controls for Auto-Refresh and Manual Switch
st.sidebar.header("Scanner Controls")
auto_refresh_enabled = st.sidebar.toggle(
    "Enable 1-Min Auto-Refresh", value=False
)

# If auto-refresh is toggled ON, refresh every 60,000 ms (1 minute)
if auto_refresh_enabled and has_autorefresh:
  st_autorefresh(interval=60000, key="datarefresh")
elif auto_refresh_enabled and not has_autorefresh:
  st.sidebar.warning(
      "To use auto-refresh, install package: pip install streamlit-autorefresh"
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


# Run scan automatically if auto-refresh is on, or via button click if off
run_scan = st.button("Run Full F&O Momentum Scan") or auto_refresh_enabled

if run_scan:
  with st.spinner(
      "Scanning all F&O stocks and calculating momentum aggression..."
  ):
    try:
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
          df = data[stock].dropna()
          if len(df) < 2:
            continue

          f_high = df.iloc[0]["High"]
          f_low = df.iloc[0]["Low"]
          c_close = df.iloc[-1]["Close"]
          c_time = df.index[-1].strftime("%H:%M:%S")

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

        # Sort by aggression score descending
        res_df = res_df.sort_values(
            by="Aggression Score (%)", ascending=False
        ).reset_index(drop=True)

        # Make index start from 1 instead of 0
        res_df.index = res_df.index + 1

        st.success(
            f"Successfully scanned {len(results)} F&O stocks! Sorted by highest"
            " aggression first."
        )

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
      "Click the button above or turn on **Enable 1-Min Auto-Refresh** in the"
      " sidebar."
  )
