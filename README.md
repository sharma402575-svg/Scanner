[README.md](https://github.com/user-attachments/files/30445150/README.md)
# Sector Trade Scanner

A single-page NSE (India) stock scanner. One click refreshes everything
from one consistent data snapshot, with an overall Buy/Sell signal and
live alerts pinned at the very top.

## What's on the page (top to bottom)

1. **Overall Market Signal + Live Alerts** — a compact Buy/Sell/Neutral
   card side by side with a flash panel of any stocks currently showing a
   breakout, breakdown, day-high/low touch, or 52-week high/low proximity.
2. **Most bullish / bearish** — whole-market stocks ranked by R Factor.
3. **Momentum** — fastest movers (rate-of-change + volume surge).
4. **Gainers & losers** — today's biggest % movers.
5. **Volume surge alerts** — unusual volume right now.
6. **Day high / day low** — stocks at (or within 0.3% of) today's high/low.
7. **52-week high / low** — stocks within 3% of their 52-week high/low.
8. **Range breakout / breakdown** — stocks closing outside their prior
   N-day trading range (N is adjustable in the sidebar, default 20 days).
9. **Sector overview** — average R Factor per sector, expandable to every
   stock in that sector (the expander title shows e.g. "BANK — 12/12
   stocks" so you can see if any were dropped due to a data fetch issue).

Every section shows a **Trade Signal** (Strong Buy / Buy / Hold / Sell /
Strong Sell) per stock, and all percentage/numeric values are shown to
2 decimal places.

## R Factor

```
R Factor = stock's % return over the lookback window
           − sector index's % return over the same window
```

## Range Breakout / Breakdown

```
Breakout  = today's close > highest close of the prior N days
Breakdown = today's close < lowest close of the prior N days
```
A standard definition of price breaking out of its recent trading range.

## How Trade Signal is calculated

| Factor | Points |
|---|---|
| R Factor ≥ bullish threshold / ≤ bearish threshold | +2 / -2 |
| Price above / below 20-day moving average | +1 / -1 |
| RSI healthy (40-65) / overbought (>75) or deeply oversold (<25) | +1 / -1 |
| Momentum score positive / negative (with volume) | +1 / -1 |
| Near 52-week high / near 52-week low | +1 / -1 |
| Range breakout / breakdown | +1 / -1 |

Score ≥ 4 → **Strong Buy** · ≥ 2 → **Buy** · -1 to 1 → **Hold** ·
≤ -2 → **Sell** · ≤ -4 → **Strong Sell**

Rules-based heuristic combining common technical factors — not financial
advice, and has no knowledge of news, earnings, or fundamentals.

## Dates & times

All dates are shown as **dd-mm-yyyy**. The "last fetched" time and
freshness check are both reported in **IST (Indian market time)**
regardless of what timezone the app happens to be hosted in.

## Refresh & auto-refresh

- **🔄 Refresh all data** — one fetch, every section recomputed from the
  same snapshot.
- **Auto-refresh toggle** (sidebar) — re-runs on a timer (1/2/5/10/15 min).

## Files

- `sectors.py` — sector → stock list (BANK now has all 12 Nifty Bank
  constituents), sector → benchmark index.
- `scanner.py` — `build_master_table()` computes every metric once;
  `view_*` functions filter/sort it; `overall_market_signal()` and
  `alerts_summary()` power the top banner.
- `app.py` — the single-page Streamlit dashboard.
- `requirements.txt` — Python packages needed (includes `tzdata` so the
  IST timezone resolves correctly on any hosting environment).

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes / limitations — please read

- Data source: Yahoo Finance via `yfinance` — **free but delayed ~15-20
  minutes** vs the live NSE feed, and occasionally has data gaps or
  short outages for individual tickers (if a sector shows fewer stocks
  than expected, e.g. "10/12", one or more tickers failed to fetch that
  run — try refreshing again).
- Prices are unadjusted (raw close) to match official NSE closing prices
  as closely as a free source allows — but exact tick-for-tick matching
  with NSE's live feed is not possible with this data source.
- 52-week high/low uses ~1 year of daily bars — a close approximation of
  NSE's official figure, not guaranteed identical.
- Not covered (would need paid data): options chain analytics, FII/DII
  institutional flow data.
- For tick-accurate live data or automated execution, you'd need a paid
  feed or broker API (Zerodha Kite Connect, Upstox API, etc.) instead.
- Informational tool only — not financial advice.
