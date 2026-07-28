[README.md](https://github.com/user-attachments/files/30439729/README.md)
# Sector Trade Scanner

A stock scanner (NSE, India) with six views:

1. **Most Bullish / Bearish** — every stock across every sector, ranked by
   R Factor, filtered to Bullish or Bearish tagged ones.
2. **Momentum** — fastest-moving stocks (price rate-of-change + volume surge).
3. **Gainers & Losers** — today's biggest % movers, side by side.
4. **Sector Overview** — average R Factor per sector, plus an expandable
   list of every individual stock in that sector with its own R Factor
   and bias.
5. **Volume Surge** — stocks trading at an unusual multiple of their
   20-day average volume right now — an early tell for intraday breakouts
   or news-driven moves.
6. **Single Sector** — drill into one sector's stocks in full detail.

## R Factor

```
R Factor = stock's % return over the lookback window
           − sector index's % return over the same window
```

Positive → stock is beating its sector (bullish tilt).
Negative → stock is lagging its sector (bearish tilt).

Final Signal also checks the 20-day moving average to confirm the trend.

## Extra columns for intraday / swing trading

- **RSI(14)** — momentum oscillator. Above 70 = overbought, below 30 =
  oversold. Useful for timing entries/exits on both intraday and swing
  trades.
- **ATR(14)** — average true range, a volatility measure.
- **Suggested Stop (long)** — LTP − 1.5×ATR, a simple volatility-based
  stop-loss distance for long swing positions. (Adjust the multiplier to
  taste — 1.5x is a common starting point, not a rule.)
- **Volume Surge (x avg)** — today's volume divided by the 20-day average.
  A quick way to see if a move is backed by real participation.

## Files

- `sectors.py` — sector → stock list, sector → benchmark index. Edit to
  add/remove stocks or sectors.
- `scanner.py` — all scanning logic (R Factor, RSI, ATR, momentum, volume
  surge, sector aggregation). No UI code — reusable elsewhere.
- `app.py` — the Streamlit dashboard (6 tabs).
- `requirements.txt` — Python packages needed.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or deploy free via GitHub + Streamlit Community Cloud (no local install
needed) — see the deployment guide provided separately.

## About the "data as of" banner

The app checks Yahoo Finance's most recent available bar every time it
loads and shows a banner:
- ✅ green = data matches today's date (as fresh as the free feed gets)
- ⚠️ yellow = data is from an earlier date — this is normal right around
  or after market close, since Yahoo can take a few hours to sync the
  final end-of-day numbers. Any mismatch you see vs official NSE data
  right after close is almost always this sync delay, not a calculation
  error. Wait an hour or two and re-run the scan.

## Notes

- Data source: Yahoo Finance via `yfinance` — free but delayed (~15-20 min)
  vs the live NSE feed. Good for swing/end-of-day scanning, not live
  intraday execution or automated order placement.
- Prices are now fetched **unadjusted** (raw close), which should match
  official NSE closing prices much more closely than before. Small gaps can
  still remain due to the ~15-20 min delay, occasional data-provider
  discrepancies, or timing differences right around market open/close —
  if you need tick-accurate live data, you'd need a paid data feed or a
  broker API (Zerodha Kite Connect, Upstox API, etc.) instead of Yahoo
  Finance.
- Symbols are set up for NSE. Change `.NS` suffixes and `SECTOR_INDEX`
  values in `sectors.py` for a different market.
- This tool is informational, not financial advice — always confirm
  signals with your own analysis before trading.
