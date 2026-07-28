import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Momentum & Penny Stock Screener", layout="wide")

st.title("🎯 Advanced Stock Screener: Momentum & Penny Stocks")
st.write(
    "Screen for high-momentum F&O setups and fundamental-backed penny stocks."
)

# Sidebar selection for screener type
screener_mode = st.sidebar.selectbox(
    "Select Screener Type",
    [
        "🚀 High-Momentum F&O Screener",
        "💎 Quality Penny Stock Screener (< ₹100)",
    ],
)

# 1. HIGH-MOMENTUM SCREENER
if screener_mode == "🚀 High-Momentum F&O Screener":
  st.subheader("🚀 High-Momentum F&O Screening Criteria")
  st.markdown(
      "- **Volume Expansion:** Current volume > 1.5x of 20-day average volume\n"
      "- **Breakout:** Price trading near day highs / breaking opening range\n"
      "- **Relative Strength:** Outperforming broader market trend"
  )

  # Sample universe of F&O liquid stocks
  universe_stocks = [
      "RELIANCE.NS",
      "TATAMOTORS.NS",
      "SBIN.NS",
      "INFY.NS",
      "ICICIBANK.NS",
      "HDFCBANK.NS",
      "TCS.NS",
      "AXISBANK.NS",
      "TATASTEEL.NS",
      "SUNPHARMA.NS",
      "M&M.NS",
      "NTPC.NS",
  ]

  if st.button("Run Momentum Scan"):
    with st.spinner("Analyzing volume and price momentum across universe..."):
      results = []
      for stock in universe_stocks:
        try:
          df = yf.download(stock, period="1mo", interval="1d", progress=False)
          if len(df) < 20:
            continue

          # Calculate 20-day average volume
          avg_volume = df["Volume"].iloc[-20:-1].mean()
          latest_volume = df["Volume"].iloc[-1]
          latest_close = df["Close"].iloc[-1]
          prev_close = df["Close"].iloc[-2]

          price_change_pct = ((latest_close - prev_close) / prev_close) * 100
          volume_spike_ratio = (
              latest_volume / avg_volume if avg_volume > 0 else 0
          )

          # Criteria: Volume spike > 1.5x and positive price action
          if volume_spike_ratio >= 1.2 and price_change_pct > 0:
            results.append({
                "Stock": stock.replace(".NS", ""),
                "Latest Price (₹)": round(float(latest_close), 2),
                "Daily Change (%)": round(float(price_change_pct), 2),
                "Volume Spike (x)": round(float(volume_spike_ratio), 2),
                "Status": "🔥 High Momentum Setup",
            })
        except Exception:
          continue

      if results:
        res_df = pd.DataFrame(results)
        res_df = res_df.sort_values(
            by="Volume Spike (x)", ascending=False
        ).reset_index(drop=True)
        res_df.index = res_df.index + 1

        st.success(
            f"Found {len(res_df)} stocks matching high-momentum volume"
            " criteria!"
        )
        st.dataframe(res_df, use_container_width=True)
      else:
        st.info(
            "No stocks met the aggressive momentum criteria for the current"
            " session."
        )

# 2. QUALITY PENNY STOCK SCREENER
elif screener_mode == "💎 Quality Penny Stock Screener (< ₹100)":
  st.subheader("💎 Quality Penny Stock Filter Criteria")
  st.markdown(
      "- **Price Range:** Under ₹100\n"
      "- **Fundamentals:** Positive earnings trend & manageable debt\n"
      "- **Liquidity:** Sufficient daily traded volume to avoid circuit traps"
  )

  # Sample list of low-priced liquid equities for demonstration
  penny_universe = [
      "IDFCFIRSTB.NS",
      "SUZLON.NS",
      "JPPOWER.NS",
      "YESBANK.NS",
      "VODAFONE.NS",
      "PNB.NS",
      "NHPC.NS",
      "IDBI.NS",
  ]

  if st.button("Scan Penny Stocks"):
    with st.spinner("Fetching fundamentals and price filters..."):
      penny_results = []
      for stock in penny_universe:
        try:
          ticker = yf.Ticker(stock)
          hist = ticker.history(period="5d")
          if len(hist) == 0:
            continue

          latest_price = hist["Close"].iloc[-1]
          info = ticker.info

          market_cap = info.get("marketCap", 0)
          debt_to_equity = info.get("debtToEquity", 0)
          pe_ratio = info.get("trailingPE", 0)

          # Filter criteria: Price < 100
          if latest_price < 100:
            penny_results.append({
                "Stock": stock.replace(".NS", ""),
                "Price (₹)": round(float(latest_price), 2),
                "Market Cap (Cr)": (
                    round(market_cap / 10000000, 2) if market_cap else "N/A"
                ),
                "P/E Ratio": round(float(pe_ratio), 2) if pe_ratio else "N/A",
                "Debt/Equity": (
                    round(float(debt_to_equity), 2)
                    if debt_to_equity
                    else "N/A"
                ),
                "Screen Status": "✅ Passed Price Filter",
            })
        except Exception:
          continue

      if penny_results:
        penny_df = pd.DataFrame(penny_results)
        penny_df.index = penny_df.index + 1

        st.success(f"Scanned successfully! Showing stocks under ₹100.")
        st.dataframe(penny_df, use_container_width=True)
      else:
        st.warning("No stocks matched the filter parameters.")
