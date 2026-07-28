import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Penny Stock Scanner", layout="wide")

st.title("💎 Penny Stock Scanner (< ₹100)")
st.write(
    "Screen for quality-filtered low-priced stocks based on price range,"
    " valuation, and debt metrics."
)

# Sidebar filters for Penny Stock criteria
st.sidebar.header("Scanner Filters")
max_price = st.sidebar.slider(
    "Max Price Threshold (₹)", min_value=10, max_value=200, value=100, step=5
)
max_debt_to_equity = st.sidebar.number_input(
    "Max Debt-to-Equity Ratio", min_value=0.0, value=1.5, step=0.1
)

# Sample universe of low-priced liquid equities
penny_universe = [
    "IDFCFIRSTB.NS",
    "SUZLON.NS",
    "JPPOWER.NS",
    "YESBANK.NS",
    "VODAFONE.NS",
    "PNB.NS",
    "NHPC.NS",
    "IDBI.NS",
    "SOUTHBANK.NS",
    "RPOWER.NS",
    "GTLINFRA.NS",
    "UCOBANK.NS",
]

if st.button("Scan Penny Stocks"):
  with st.spinner(
      "Fetching live prices and fundamental metrics from market data..."
  ):
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

        # Apply user filters
        if latest_price <= max_price:
          # If debt data exists, filter by it, otherwise allow
          if (
              debt_to_equity == 0
              or debt_to_equity is None
              or debt_to_equity <= max_debt_to_equity
          ):
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
                "Status": "✅ Passed Filter Criteria",
            })
      except Exception:
        continue

    if penny_results:
      penny_df = pd.DataFrame(penny_results)

      # Sort by lowest price or alphabetical order
      penny_df = penny_df.sort_values(by="Price (₹)", ascending=True).reset_index(
          drop=True
      )
      penny_df.index = penny_df.index + 1

      st.success(
          f"Successfully scanned and filtered {len(penny_df)} penny stocks!"
      )
      st.dataframe(penny_df, use_container_width=True)
    else:
      st.warning(
          "No stocks matched the selected filters. Try adjusting the thresholds"
          " in the sidebar."
      )
else:
  st.info("Click the button above to run the Penny Stock Scanner.")
