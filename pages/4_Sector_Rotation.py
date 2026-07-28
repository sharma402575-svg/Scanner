import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Sector Rotation Matrix", layout="wide")

st.title("🔄 Real-Time Sector Rotation Matrix (RRG Model)")
st.write(
    "Classifies major NSE sectors into **Leading, Weakening, Lagging, and"
    " Improving** quadrants based on live relative performance and momentum."
)

# Major NSE Sector Tickers on Yahoo Finance
sector_tickers = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Energy": "^CNXENERGY",
    "Nifty Infra": "^CNXINFRA",
    "Nifty PSU Bank": "^CNXPSUBANK",
    "Nifty Realty": "^CNXREALTY",
}

if st.button("Refresh Sector Matrix"):
  with st.spinner("Fetching live sectoral data and calculating quadrants..."):
    try:
      # Fetch benchmark Nifty 50
      nifty_df = yf.download("^NSEI", period="2mo", interval="1d", progress=False)[
          "Close"
      ]

      leading = []
      weakening = []
      lagging = []
      improving = []

      for name, ticker in sector_tickers.items():
        sec_df = yf.download(
            ticker, period="2mo", interval="1d", progress=False
        )["Close"]
        if len(sec_df) < 20 or len(nifty_df) < 20:
          continue

        # Align data
        combined = pd.concat([sec_df, nifty_df], axis=1).dropna()
        combined.columns = ["Sector", "Nifty"]

        # Calculate Relative Strength (Sector / Nifty)
        rs = combined["Sector"] / combined["Nifty"]

        # Momentum = Rate of Change of RS
        rs_momentum = rs.pct_change(5).iloc[-1] * 100
        rs_level = (rs.iloc[-1] / rs.rolling(20).mean().iloc[-1] - 1) * 100

        # Quadrant Classification Logic
        if rs_level >= 0 and rs_momentum >= 0:
          leading.append((name, round(float(rs_momentum), 2)))
        elif rs_level >= 0 and rs_momentum < 0:
          weakening.append((name, round(float(rs_momentum), 2)))
        elif rs_level < 0 and rs_momentum < 0:
          lagging.append((name, round(float(rs_momentum), 2)))
        else:
          improving.append((name, round(float(rs_momentum), 2)))

      # Render 4 Columns Layout
      col1, col2, col3, col4 = st.columns(4)

      with col1:
        st.markdown("### 🟢 Leading")
        st.caption("Strong RS & Strong Momentum")
        if leading:
          for s, m in leading:
            st.success(f"**{s}**\n\nMomentum: +{m}%")
        else:
          st.info("No sectors currently.")

      with col2:
        st.markdown("### 🟡 Weakening")
        st.caption("Strong RS, Losing Momentum")
        if weakening:
          for s, m in weakening:
            st.warning(f"**{s}**\n\nMomentum: {m}%")
        else:
          st.info("No sectors currently.")

      with col3:
        st.markdown("### 🔴 Lagging")
        st.caption("Weak RS & Weak Momentum")
        if lagging:
          for s, m in lagging:
            st.error(f"**{s}**\n\nMomentum: {m}%")
        else:
          st.info("No sectors currently.")

      with col4:
        st.markdown("### 🔵 Improving")
        st.caption("Weak RS, Gaining Momentum")
        if improving:
          for s, m in improving:
            st.info(f"**{s}**\n\nMomentum: +{m}%")
        else:
          st.info("No sectors currently.")

    except Exception as e:
      st.error(f"Error loading sector matrix: {e}")
else:
  st.info("Click the button above to generate the live 4-quadrant sector matrix.")
