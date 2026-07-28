# Sector Trade Scanner

A stock scanner (NSE, India) with five views:

1. **Most Bullish / Bearish** — every stock across every sector, ranked by
   R Factor, filtered to just the Bullish or Bearish tagged ones.
2. **Momentum** — fastest-moving stocks (price rate-of-change + volume
   surge), regardless of sector.
3. **Gainers & Losers** — today's biggest % movers, side by side.
4. **Sector Overview** — average R Factor per sector, so you can see which
   sectors as a whole are turning bullish or bearish.
5. **Single Sector** — drill into one sector's stocks in detail.

## R Factor

```
R Factor = stock's % return over the lookback window
           − sector index's % return over the same window
```

Positive → stock is beating its sector (bullish tilt).
Negative → stock is lagging its sector (bearish tilt).

Final Signal also checks the 20-day moving average to confirm the trend
before calling something Bullish or Bearish.

## Files

- `sectors.py` — sector → stock list, sector → benchmark index. Edit to
  add/remove stocks or sectors.
- `scanner.py` — all the scanning logic, no UI code. Can be reused/imported
  elsewhere.
- `app.py` — the Streamlit dashboard (5 tabs).
- `requirements.txt` — Python packages needed.

## Running it

You don't need Python installed locally — see the GitHub + Streamlit Cloud
deployment guide provided separately. If you do want to run it locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Data source: Yahoo Finance via `yfinance` — free but delayed (~15 min).
  Good for swing/end-of-day scanning, not live intraday execution.
- Symbols are set up for NSE. Change the `.NS` suffixes and `SECTOR_INDEX`
  values in `sectors.py` for a different market.
