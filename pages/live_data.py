"""
Live fetchers for India VIX and Nifty PCR — the two factors that ARE
available from free sources, unlike FII/DII flows.

- India VIX: Yahoo Finance ticker ^INDIAVIX (same source as the rest of
  the scanner).
- Nifty PCR: NSE's own public option-chain API (nseindia.com). This isn't
  officially documented but is the same endpoint NSE's own website charts
  use. NSE blocks requests without browser-like headers and a warmed-up
  session, so this fetch: (1) hits the homepage first to collect cookies,
  (2) reuses those cookies for the option-chain request. NSE also
  occasionally rate-limits or blocks cloud-hosted IPs — if this fails,
  the app falls back to manual PCR entry, so nothing breaks.
"""

import yfinance as yf
import requests

_NSE_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/option-chain",
}


def fetch_india_vix():
    """Returns the latest India VIX close, or None if unavailable."""
    try:
        hist = yf.Ticker("^INDIAVIX").history(period="5d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception:
        pass
    return None


def fetch_nifty_pcr():
    """
    Returns (pcr, total_call_oi, total_put_oi) or (None, None, None) if
    the fetch fails (NSE blocked/rate-limited/changed something).
    """
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=_NSE_HEADERS, timeout=6)
        resp = session.get(
            "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
            headers=_NSE_HEADERS, timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", {}).get("data", [])
        total_ce_oi = sum(r["CE"]["openInterest"] for r in records if "CE" in r)
        total_pe_oi = sum(r["PE"]["openInterest"] for r in records if "PE" in r)
        if total_ce_oi > 0:
            pcr = round(total_pe_oi / total_ce_oi, 2)
            return pcr, total_ce_oi, total_pe_oi
    except Exception:
        pass
    return None, None, None
