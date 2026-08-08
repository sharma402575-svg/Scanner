[README.md](https://github.com/user-attachments/files/30849375/README.md)
# Sector Trade Scanner

A single-page NSE (India) stock scanner. One click refreshes everything
from one consistent data snapshot.

## What's on the page (top to bottom)

1. **Gainers & losers** — today's biggest % movers.
2. **Most bullish / bearish** — same data as #1 (today's top gainers and
   top losers) shown again with the Trade Signal column — R Factor used
   to gate this list and was removed because it didn't reflect same-day
   price action.
3. **200 EMA crossovers** — stocks whose **close** just crossed above
   (bullish) or below (bearish) their 200-day EMA. Two separate lists.
4. **Momentum** — fastest movers (5-day rate-of-change + volume surge,
   no R-Factor involved).
5. **Volume surge alerts** — unusual volume right now.
6. **Day high / day low** — stocks at (or within 0.3% of) today's high/low.
7. **52-week high / low** — stocks within 3% of their 52-week high/low.
8. **Range breakout / breakdown** — stocks closing outside their prior
   N-day trading range (N adjustable in the sidebar, default 20 days).
9. **Sector overview** — average 1-day % change per sector, expandable to
   every stock in that sector.

Every table shows a **Trade Signal** (Strong Buy / Buy / Hold / Sell /
Strong Sell) per stock, 2 decimal places throughout, and is rendered in a
**fixed, pre-sorted order that cannot be re-sorted by clicking a column
header**.

**Why a top gainer can show "Sell" and a top loser can show "Buy":**
Trade Signal is a separate read from today's price move — it looks at
5-day trend vs 20DMA, RSI zone, 5-day momentum, and 52-week/breakout
context. A stock can pop 4-5% today and still score "Sell" if it's
still below its 20-day average, RSI just went overbought from the spike,
or its 5-day trend is still net negative — i.e. today's move is loud but
the underlying trend hasn't turned yet. That's intentional, not a bug,
but it's worth knowing the two aren't measuring the same thing.

## Settings persist

Every sidebar setting (lookback, thresholds, auto-refresh, etc.) is saved
into the page's URL as you change it. Reloading the browser, or sharing
the URL with someone else, keeps those exact settings — you don't need to
redo them each time.

## Range Breakout / Breakdown

```
Breakout  = today's close > highest close of the prior N days
Breakdown = today's close < lowest close of the prior N days
```
A standard definition of price breaking out of its recent trading range.

## How Trade Signal is calculated

| Factor | Points |
|---|---|
| Price above / below 20-day moving average | +1 / -1 |
| RSI healthy (40-65) / overbought (>75) or deeply oversold (<25) | +1 / -1 |
| 5-day momentum score positive / negative (with volume) | +1 / -1 |
| Near 52-week high / near 52-week low | +1 / -1 |
| Range breakout / breakdown | +1 / -1 |

Score ≥ 3 → **Strong Buy** · ≥ 1 → **Buy** · 0 → **Hold** ·
≤ -1 → **Sell** · ≤ -3 → **Strong Sell**

Rules-based heuristic combining common technical factors — not financial
advice, and has no knowledge of news, earnings, or fundamentals.
(R Factor — sector-relative return — was removed entirely from this
scoring and from every filter in the app; it didn't line up with actual
day-to-day price action.)

## Pages

This is a proper multi-page Streamlit app — two separate pages, each with
its own URL, linked from the sidebar:

- **Live Scanner** (`app.py`) — gainers/losers, momentum, 200 EMA
  crossovers, breakouts, 52-week levels, sector overview.
- **FII/DII & Sentiment** (`pages/1_FII_DII_and_Sentiment.py`) — manual
  data entry, completely separate page. Refreshing or auto-refreshing the
  Live Scanner page never touches this one — it only updates when you
  click its own "Compute Sentiment" button. You can right-click its
  sidebar link and "open in new tab" for a true separate browser tab.

## Sector Rotation page (new — RRG)

A third page, own URL: `pages/2_Sector_Rotation.py`. Plots a classic
Relative Rotation Graph — every sector's **RS-Ratio** (relative strength
vs Nifty 50, x-axis) against its **RS-Momentum** (is that strength
accelerating, y-axis), both centered at 100, with a trailing tail of
recent weeks so you can see each sector rotating between the four
quadrants:
- **Leading** (top-right) — outperforming and accelerating
- **Weakening** (bottom-right) — still outperforming, losing steam
- **Lagging** (bottom-left) — underperforming, still falling
- **Improving** (top-left) — underperforming, but turning up

Sectors classically rotate clockwise through these over time. A table
below the chart shows each sector's current quadrant.

**Honesty note on methodology**: the original JdK RS-Ratio/RS-Momentum
formulas (the ones StockCharts' RRG uses) are proprietary. This uses the
standard open approximation (z-score-normalized RS-Ratio, rate-of-change
RS-Momentum) that's publicly documented and widely used in open-source
RRG implementations — it produces the same quadrant behavior and rotation
pattern, but won't match a licensed StockCharts RRG tick-for-tick.

New file: `sector_rotation.py` — the RS-Ratio/Momentum computation,
independent of `scanner.py`.

## FII/DII & Sentiment page

FII/DII flows and F&O open-interest data aren't available from free data
feeds like Yahoo Finance — this page reads them from a file you provide.

**Upload NSE's Participant OI file**: click "Upload NSE Participant OI
CSV" and pick the `.csv` you downloaded from nseindia.com's official,
free, daily "Participant wise Open Interest" report — it's read and
scored automatically. A "paste instead" fallback is there if you don't
have the file itself.

**Scoring**: reads the FII and DII rows specifically, and scores two
things per participant — Index Futures Long % (straightforward
directional positioning) and Index Options bias (long calls + short
puts vs short calls + long puts). FII is weighted higher (1.5x) than DII
(0.8x), since FII flows are the more closely watched next-day driver.
Gives one reading: **Bullish / Bearish / Neutral for tomorrow**, with a
"Show logic" breakdown of exactly how each number contributed.

**Weekly log**: every computed reading is saved to a rolling log — a
compact table of date/sentiment/score, capped at the last 7 entries (a
week), with each day expandable for the full logic used that day. This
log lives only in the current browser session — it resets if you close
the tab or the app restarts. Ask if you want permanent day-to-day
storage added (needs a small database).

### Stock-wise F&O data (separate, optional tool)

Below the main score, a collapsed section lets you paste
`TICKER, % price change, % OI change` per line, classified into:
- Price↑ + OI↑ → **Long Buildup** (bullish — new longs entering)
- Price↑ + OI↓ → **Short Covering** (bullish — shorts exiting)
- Price↓ + OI↑ → **Short Buildup** (bearish — new shorts entering)
- Price↓ + OI↓ → **Long Unwinding** (bearish — longs exiting)

This is a per-stock lens, kept separate from (not added into) the main
sentiment score above.

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
- `scanner.py` — `build_master_table()` computes every metric once (RSI,
  ATR, momentum, 52w high/low, range breakout/breakdown, 200 EMA
  crossover — no R Factor); `view_*` functions filter/sort it per section.
- `live_data.py` — live India VIX / Nifty PCR fetchers. **Currently
  unused** — the FII/DII page no longer has the macro-inputs step that
  needed them. Safe to leave in the repo or delete; nothing imports it.
- `sentiment.py` — FII/DII Participant-OI positioning scoring and F&O OI
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
