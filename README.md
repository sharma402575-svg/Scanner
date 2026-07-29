[Uploading README.md…]()
# Sector Trade Scanner

A single-page NSE (India) stock scanner. One click refreshes everything
from one consistent data snapshot, with an overall Buy/Sell signal and
live alerts pinned at the very top.

## What's on the page (top to bottom)

1. **Most bullish / bearish** — whole-market stocks ranked by R Factor.
2. **200 EMA crossovers** — stocks that just crossed above (bullish) or
   below (bearish) their 200-day EMA, a widely-watched long-term trend
   signal. Two separate lists.
3. **Momentum** — fastest movers (rate-of-change + volume surge).
4. **Gainers & losers** — today's biggest % movers.
5. **Volume surge alerts** — unusual volume right now.
6. **Day high / day low** — stocks at (or within 0.3% of) today's high/low.
7. **52-week high / low** — stocks within 3% of their 52-week high/low.
8. **Range breakout / breakdown** — stocks closing outside their prior
   N-day trading range (N adjustable in the sidebar, default 20 days).
9. **Sector overview** — average R Factor per sector, expandable to every
   stock in that sector.

Every table shows a **Trade Signal** (Strong Buy / Buy / Hold / Sell /
Strong Sell) per stock, 2 decimal places throughout, and is rendered in a
**fixed, pre-sorted order that cannot be re-sorted by clicking a column
header** — most gainers/highest R Factor/etc. always stay on top exactly
as computed.

## Settings persist

Every sidebar setting (lookback, thresholds, auto-refresh, etc.) is saved
into the page's URL as you change it. Reloading the browser, or sharing
the URL with someone else, keeps those exact settings — you don't need to
redo them each time.

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

## Pages

This is a proper multi-page Streamlit app — two separate pages, each with
its own URL, linked from the sidebar:

- **Live Scanner** (`app.py`) — everything from R Factor ranking to
  sector overview.
- **FII/DII & Sentiment** (`pages/1_FII_DII_and_Sentiment.py`) — manual
  data entry, completely separate page. Refreshing or auto-refreshing the
  Live Scanner page never touches this one — it only updates when you
  click its own "Compute Sentiment" button. You can right-click its
  sidebar link and "open in new tab" for a true separate browser tab.

## FII/DII & Sentiment page — Tomorrow's Call (one combined score)

Everything on this page feeds into **one final "Tomorrow's Sentiment"
reading** — it used to be two separate scores in two separate boxes; now
it's unified into a 3-step flow:

**Step 1 — Market-wide inputs**: FII Cash Net, DII Cash Net, Nifty PCR,
India VIX, Advance/Decline Ratio. VIX and PCR can be fetched live with one
click (see below); any field can also be left blank.

**Step 2 — FII/DII positioning**: upload NSE's official daily "Participant
wise Open Interest" CSV (free, from nseindia.com) — read automatically.
Adds FII/DII Index Futures Long % and Index Options bias (long calls +
short puts vs short calls + long puts) into the same combined score.

**Step 3 — Tomorrow's Sentiment**: one combined, weighted score across
whatever was filled in from steps 1 and 2 — **Strongly Bullish / Bullish /
Neutral / Bearish / Strongly Bearish for tomorrow** — with a "Show logic"
breakdown listing exactly how every single number contributed. You can
also compute from macro inputs alone (button below step 2) if you don't
have the OI file yet.

**Why this combination**: PCR and VIX reflect options-market fear/greed;
FII/DII cash flow and OI positioning reflect where the big money is
actually placed. Combined, they're the standard end-of-day read traders
use to form a view for the next session — that's the whole point of this
page, so they're scored together rather than separately.

### Live India VIX & Nifty PCR

Click **"🌐 Fetch Live India VIX & Nifty PCR"** and it auto-fills those two
fields:
- **India VIX** — via Yahoo Finance (`^INDIAVIX`), same reliable source as
  the rest of the scanner.
- **Nifty PCR** — via NSE's own public option-chain API. This isn't an
  official documented API, so it can occasionally fail or get rate-limited
  by NSE (especially from cloud-hosted IPs like Streamlit Cloud) — if it
  does, the app tells you and you can just type the PCR in manually as a
  fallback. Nothing else breaks if this fetch fails.

### Uploading the Participant OI file

Click "Upload NSE Participant OI CSV" and pick the `.csv` you downloaded
from NSE — it's read and folded into the combined score automatically, no
button click needed. A "paste instead" fallback is there if you don't
have the file itself.

### Weekly log

Every time a reading is computed (from either the upload or the
"macro inputs only" button), it's saved to a rolling log — a compact
table of date/sentiment/score, capped at the last 7 entries (a week),
with each day expandable for the full logic used that day.

Same caveat applies: this log lives only in the current browser session
— it resets if you close the tab or the app restarts. Ask if you want
permanent day-to-day storage added (needs a small database).

### Stock-wise F&O data (separate, optional tool)

Below the main score, a collapsed section lets you paste
`TICKER, % price change, % OI change` per line, classified into:
- Price↑ + OI↑ → **Long Buildup** (bullish — new longs entering)
- Price↑ + OI↓ → **Short Covering** (bullish — shorts exiting)
- Price↓ + OI↑ → **Short Buildup** (bearish — new shorts entering)
- Price↓ + OI↓ → **Long Unwinding** (bearish — longs exiting)

This is a per-stock lens, kept separate from (not added into) the overall
Tomorrow's Sentiment score.

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
- `scanner.py` — `build_master_table()` computes every metric once (R
  Factor, RSI, ATR, momentum, 52w high/low, range breakout/breakdown, 200
  EMA crossover); `view_*` functions filter/sort it for each section.
- `live_data.py` — live India VIX (Yahoo Finance) and Nifty PCR (NSE
  option-chain API) fetchers, used by the sentiment page's fetch button.
- `sentiment.py` — manual FII/DII/PCR/VIX/breadth scoring and F&O OI
  buildup classification, used by the sentiment page.
- `app.py` — the Live Scanner page (Streamlit's "main" page — this is
  the file you deploy/run).
- `pages/1_FII_DII_and_Sentiment.py` — the FII/DII & Sentiment page.
  Streamlit auto-detects anything in a `pages/` folder next to `app.py`
  and turns it into a separate page with its own URL and sidebar link —
  no extra setup needed.
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
