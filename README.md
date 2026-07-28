[README.md](https://github.com/user-attachments/files/30441425/README.md)
# Sector Trade Scanner

A single-page NSE (India) stock scanner. One click refreshes everything
from one consistent data snapshot, with an overall Buy/Sell market signal
pinned at the very top.

## What's on the page (top to bottom)

1. **Overall Market Signal** — a single Buy / Sell / Neutral call for the
   whole scanned universe, with breadth stats (% of stocks buy-leaning vs
   sell-leaning). This is the first thing you see.
2. **Most bullish / bearish** — whole-market stocks ranked by R Factor.
3. **Momentum** — fastest movers (rate-of-change + volume surge).
4. **Gainers & losers** — today's biggest % movers.
5. **Volume surge alerts** — unusual volume right now.
6. **Day high / day low** — stocks trading at (or within 0.3% of) today's
   high or low.
7. **52-week high / low** — stocks within 3% of their 52-week high or low.
8. **Sector overview** — average R Factor per sector, expandable to every
   stock in that sector.

Every section shows a **Trade Signal** (Strong Buy / Buy / Hold / Sell /
Strong Sell) per stock.

## R Factor

```
R Factor = stock's % return over the lookback window
           − sector index's % return over the same window
```
Positive → stock beating its sector. Negative → lagging it.

## How Trade Signal is calculated

A transparent points system, not a black box:

| Factor | Points |
|---|---|
| R Factor ≥ bullish threshold / ≤ bearish threshold | +2 / -2 |
| Price above / below 20-day moving average | +1 / -1 |
| RSI in healthy zone (40-65) / overbought (>75) or deeply oversold (<25) | +1 / -1 |
| Momentum score positive / negative (with volume behind it) | +1 / -1 |
| Near 52-week high / near 52-week low | +1 / -1 |

Score ≥ 4 → **Strong Buy** · ≥ 2 → **Buy** · -1 to 1 → **Hold** ·
≤ -2 → **Sell** · ≤ -4 → **Strong Sell**

This combines common technical factors into one number so you can scan
fast — it does **not** know about news, earnings, or fundamentals, and is
not financial advice. Always confirm before trading.

## Refresh & auto-refresh

- **🔄 Refresh all data** — one fetch, every section recomputed from the
  same snapshot.
- **Auto-refresh toggle** (sidebar) — re-runs on a timer (1/2/5/10/15 min).
  Turn off when not actively watching, to avoid unnecessary API calls.

## Data freshness banner

Shows the actual date of the latest bar Yahoo Finance has. An earlier
date than today right after market close is normal sync delay, not a bug.

## Files

- `sectors.py` — sector → stock list, sector → benchmark index.
- `scanner.py` — `build_master_table()` computes every metric for every
  stock once; all views (`view_*` functions) filter/sort that same table.
  `overall_market_signal()` aggregates it into the top banner.
- `app.py` — the single-page Streamlit dashboard.
- `requirements.txt` — Python packages needed.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or deploy free via GitHub + Streamlit Community Cloud.

## Notes / limitations

- Data source: Yahoo Finance via `yfinance` — free but delayed (~15-20
  min) vs live NSE, unadjusted prices to match official NSE closes.
- 52-week high/low uses ~1 year of daily bars from Yahoo — a close
  approximation of NSE's official 52-week figure, not guaranteed identical.
- Not covered (would need paid data): options chain analytics, FII/DII
  institutional flow data.
- For tick-accurate live data or automated execution, you'd need a paid
  feed or broker API (Zerodha Kite Connect, Upstox API, etc.).
- Informational tool only — not financial advice.
