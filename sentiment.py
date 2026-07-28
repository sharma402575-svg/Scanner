"""
Manual market-sentiment engine.

FII/DII flows, PCR, VIX, market breadth, and stock-wise F&O OI data are
NOT available from free sources (Yahoo Finance doesn't carry them) — so
this module scores whatever numbers the USER types in, and explains its
reasoning in plain language for every factor, so nothing is a black box.

Every factor is optional. Leave a field blank and it's simply excluded
from the score (and said so in the breakdown).
"""

from typing import Optional


def parse_optional_float(text: str) -> Optional[float]:
    text = (text or "").strip().replace(",", "")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


# ---------- individual factor scorers ----------
# Each returns None if not provided, else a dict with the points awarded
# and a plain-English message explaining exactly why.

def _flow_factor(name: str, value: Optional[float], weight: float = 1.0):
    if value is None:
        return None
    if value > 2000:
        pts, tone = 3, "strong buying"
    elif value > 500:
        pts, tone = 2, "buying"
    elif value > 0:
        pts, tone = 1, "mild buying"
    elif value == 0:
        pts, tone = 0, "flat, no net flow"
    elif value > -500:
        pts, tone = -1, "mild selling"
    elif value > -2000:
        pts, tone = -2, "selling"
    else:
        pts, tone = -3, "strong selling"
    pts = round(pts * weight, 1)
    sign = "+" if pts >= 0 else ""
    msg = (f"{name} = ₹{value:,.0f} Cr ({tone}) → {sign}{pts} pts. "
           f"{'Positive' if value > 0 else 'Negative' if value < 0 else 'Zero'} net flow "
           f"{'supports' if value > 0 else 'weighs on' if value < 0 else 'has no effect on'} the market.")
    return {"factor": name, "value": value, "points": pts, "message": msg}


def _pcr_factor(pcr: Optional[float]):
    if pcr is None:
        return None
    if pcr > 1.3:
        pts, tone = 2, "high — heavy put writing relative to calls, a bullish tilt (more downside protection being sold)"
    elif pcr > 1.0:
        pts, tone = 1, "above 1 — mildly bullish"
    elif pcr > 0.8:
        pts, tone = 0, "near 1 — balanced, neutral"
    elif pcr > 0.6:
        pts, tone = -1, "below 0.8 — mildly bearish"
    else:
        pts, tone = -2, "low — heavy call writing relative to puts, a bearish tilt"
    msg = f"Put-Call Ratio = {pcr:.2f} ({tone}) → {'+' if pts>=0 else ''}{pts} pts."
    return {"factor": "PCR", "value": pcr, "points": pts, "message": msg}


def _vix_factor(vix: Optional[float]):
    if vix is None:
        return None
    if vix < 13:
        pts, tone = 1, "low — market is complacent/calm, mildly bullish for trend continuation"
    elif vix < 18:
        pts, tone = 0, "normal range — neutral"
    elif vix < 22:
        pts, tone = -1, "elevated — rising fear, mildly bearish"
    else:
        pts, tone = -2, "high — significant fear/uncertainty, bearish"
    msg = f"India VIX = {vix:.2f} ({tone}) → {'+' if pts>=0 else ''}{pts} pts."
    return {"factor": "India VIX", "value": vix, "points": pts, "message": msg}


def _long_pct_factor(long_pct: Optional[float], name: str = "FII Long % (Index Fut)"):
    if long_pct is None:
        return None
    if long_pct > 60:
        pts, tone = 2, "majority long — bullish positioning"
    elif long_pct > 50:
        pts, tone = 1, "slightly more long than short — mildly bullish"
    elif long_pct > 40:
        pts, tone = -1, "slightly more short than long — mildly bearish"
    else:
        pts, tone = -2, "majority short — bearish positioning"
    msg = f"{name} = {long_pct:.1f}% ({tone}) → {'+' if pts>=0 else ''}{pts} pts."
    return {"factor": name, "value": long_pct, "points": pts, "message": msg}


def _breadth_factor(ad_ratio: Optional[float]):
    if ad_ratio is None:
        return None
    if ad_ratio > 2:
        pts, tone = 2, "advances far outnumber declines — broad-based buying"
    elif ad_ratio > 1.2:
        pts, tone = 1, "more advances than declines — mildly positive breadth"
    elif ad_ratio > 0.8:
        pts, tone = 0, "roughly balanced — neutral breadth"
    elif ad_ratio > 0.5:
        pts, tone = -1, "more declines than advances — mildly negative breadth"
    else:
        pts, tone = -2, "declines far outnumber advances — broad-based selling"
    msg = f"Advance/Decline Ratio = {ad_ratio:.2f} ({tone}) → {'+' if pts>=0 else ''}{pts} pts."
    return {"factor": "Advance/Decline Ratio", "value": ad_ratio, "points": pts, "message": msg}


def compute_market_sentiment(fii_cash=None, dii_cash=None, fii_fno_index=None,
                              fii_long_pct=None, pcr=None, vix=None, ad_ratio=None):
    """
    Combines every provided factor into one sentiment score, with a full
    breakdown of exactly how each number contributed — nothing hidden.
    """
    breakdown = []
    for item in [
        _flow_factor("FII Cash Net", fii_cash, weight=1.5),   # FII weighted higher — bigger market mover
        _flow_factor("DII Cash Net", dii_cash, weight=1.0),
        _flow_factor("FII F&O Index Net", fii_fno_index, weight=1.0),
        _long_pct_factor(fii_long_pct),
        _pcr_factor(pcr),
        _vix_factor(vix),
        _breadth_factor(ad_ratio),
    ]:
        if item:
            breakdown.append(item)

    if not breakdown:
        return {"score": 0, "label": "No data", "color": "#6b7280", "breakdown": [],
                "summary": "No data entered yet — fill in at least one field below."}

    total = round(sum(b["points"] for b in breakdown), 1)

    if total >= 6:
        label, color = "Strongly Bullish", "#16a34a"
    elif total >= 2:
        label, color = "Bullish", "#16a34a"
    elif total <= -6:
        label, color = "Strongly Bearish", "#b91c1c"
    elif total <= -2:
        label, color = "Bearish", "#b91c1c"
    else:
        label, color = "Neutral", "#6b7280"

    n = len(breakdown)
    summary = (f"{n} factor{'s' if n != 1 else ''} provided, combined score = {total}. "
               f"Net reading: {label}.")

    return {"score": total, "label": label, "color": color, "breakdown": breakdown, "summary": summary}


# ---------- stock-wise F&O OI buildup classification ----------

def classify_fno_row(ticker: str, price_chg_pct: float, oi_chg_pct: float):
    """
    Standard F&O open-interest buildup classification:
      Price up   + OI up   -> Long Buildup    (Bullish, new longs entering)
      Price up   + OI down -> Short Covering  (Bullish, shorts exiting)
      Price down + OI up   -> Short Buildup   (Bearish, new shorts entering)
      Price down + OI down -> Long Unwinding  (Bearish, longs exiting)
    """
    price_up = price_chg_pct > 0
    oi_up = oi_chg_pct > 0
    if price_up and oi_up:
        label, bias = "Long Buildup", "Bullish"
    elif price_up and not oi_up:
        label, bias = "Short Covering", "Bullish"
    elif not price_up and oi_up:
        label, bias = "Short Buildup", "Bearish"
    else:
        label, bias = "Long Unwinding", "Bearish"
    return {
        "Ticker": ticker.strip().upper(),
        "% Price Chg": round(price_chg_pct, 2),
        "% OI Chg": round(oi_chg_pct, 2),
        "Buildup": label,
        "Bias": bias,
    }


def parse_fno_text(text: str):
    """
    Parses lines like:  TICKER, price_change_pct, oi_change_pct
    (comma or whitespace separated). Skips blank/invalid lines silently
    and returns (rows, skipped_count).
    """
    rows = []
    skipped = 0
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.replace("\t", ",").split(",") if p.strip() != ""]
        if len(parts) < 3:
            parts = line.split()
        if len(parts) < 3:
            skipped += 1
            continue
        ticker, price_str, oi_str = parts[0], parts[1], parts[2]
        try:
            price_chg = float(price_str.replace("%", ""))
            oi_chg = float(oi_str.replace("%", ""))
        except ValueError:
            skipped += 1
            continue
        rows.append(classify_fno_row(ticker, price_chg, oi_chg))
    return rows, skipped


# ---------- NSE "Participant wise Open Interest" report parser ----------
# NSE publishes this CSV daily, free, on their website. Columns are fixed:
# Client Type, Future Index Long, Future Index Short, Future Stock Long,
# Future Stock Short, Option Index Call Long, Option Index Put Long,
# Option Index Call Short, Option Index Put Short, Option Stock Call Long,
# Option Stock Put Long, Option Stock Call Short, Option Stock Put Short,
# Total Long Contracts, Total Short Contracts

def parse_participant_csv(text: str):
    """
    Parses NSE's participant-wise OI CSV (as pasted by the user) into
    {CLIENT_TYPE: {column_name: value}}. Skips the title row automatically
    (first row if it doesn't look like a header). Returns None if it can't
    find a usable header + FII/DII rows.
    """
    lines = [l for l in (text or "").splitlines() if l.strip()]
    if len(lines) < 3:
        return None

    header_idx = None
    for i, line in enumerate(lines[:3]):
        if "client type" in line.lower():
            header_idx = i
            break
    if header_idx is None:
        return None

    headers = [h.strip() for h in lines[header_idx].split(",")]
    rows = {}
    for line in lines[header_idx + 1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        client_type = parts[0].strip().upper()
        row = {}
        for h, v in zip(headers[1:], parts[1:]):
            try:
                row[h] = float(v.replace(",", ""))
            except ValueError:
                row[h] = None
        rows[client_type] = row
    return rows if rows else None


def _get(row: dict, *keys):
    """Fetch the first matching key from a parsed CSV row, case/spacing tolerant."""
    lookup = {k.lower().replace(" ", ""): v for k, v in row.items()}
    for k in keys:
        v = lookup.get(k.lower().replace(" ", ""))
        if v is not None:
            return v
    return None


def _participant_factor_items(row: dict, label: str, weight: float):
    """Index Futures Long % and Index Options bias for one participant
    (FII or DII), as a list of breakdown items. Shared by the
    participant-only scorer and the combined tomorrow-sentiment scorer."""
    items = []
    if not row:
        return items

    fut_long = _get(row, "Future Index Long")
    fut_short = _get(row, "Future Index Short")
    if fut_long is not None and fut_short is not None and (fut_long + fut_short) > 0:
        pct = fut_long / (fut_long + fut_short) * 100
        item = _long_pct_factor(pct, name=f"{label} Index Futures Long %")
        if item:
            item["points"] = round(item["points"] * weight, 2)
            item["message"] += f" (weighted x{weight})"
            items.append(item)

    call_long = _get(row, "Option Index Call Long")
    call_short = _get(row, "Option Index Call Short")
    put_long = _get(row, "Option Index Put Long")
    put_short = _get(row, "Option Index Put Short")
    if None not in (call_long, call_short, put_long, put_short):
        bullish_leg = call_long + put_short
        bearish_leg = call_short + put_long
        total = bullish_leg + bearish_leg
        if total > 0:
            pct = bullish_leg / total * 100
            item = _long_pct_factor(pct, name=f"{label} Index Options Bullish %")
            if item:
                item["points"] = round(item["points"] * weight, 2)
                item["message"] += (f" (weighted x{weight}). Basis: long calls + short puts "
                                     f"= {bullish_leg:,.0f} vs short calls + long puts = {bearish_leg:,.0f}.")
                items.append(item)
    return items


def compute_participant_sentiment(fii_row: dict, dii_row: dict):
    """Participant-OI-only sentiment (used when no macro data is filled in)."""
    breakdown = _participant_factor_items(fii_row, "FII", weight=1.5)
    breakdown += _participant_factor_items(dii_row, "DII", weight=0.8)

    if not breakdown:
        return {"score": 0, "label": "No data", "color": "#6b7280", "breakdown": [],
                "summary": "Couldn't find usable FII/DII Index Futures or Options columns in the pasted data."}

    total = round(sum(b["points"] for b in breakdown), 2)
    if total >= 4:
        label, color = "Bullish for tomorrow", "#16a34a"
    elif total <= -4:
        label, color = "Bearish for tomorrow", "#b91c1c"
    else:
        label, color = "Neutral for tomorrow", "#6b7280"

    summary = f"Combined weighted score = {total} from {len(breakdown)} factor(s). Reading: {label}."
    return {"score": total, "label": label, "color": color, "breakdown": breakdown, "summary": summary}


def compute_tomorrow_sentiment(fii_cash=None, dii_cash=None, pcr=None, vix=None,
                                ad_ratio=None, fii_row=None, dii_row=None):
    """
    THE combined end-of-day call for tomorrow: merges macro factors (PCR,
    VIX, FII/DII cash flow, market breadth — whatever's filled in above)
    with FII/DII Index Futures + Options positioning from the uploaded
    Participant OI file (whatever's available). This is what "Tomorrow's
    Sentiment" in the weekly log is built from — one number, not two.
    """
    breakdown = []
    for item in [
        _flow_factor("FII Cash Net", fii_cash, weight=1.5),
        _flow_factor("DII Cash Net", dii_cash, weight=1.0),
        _pcr_factor(pcr),
        _vix_factor(vix),
        _breadth_factor(ad_ratio),
    ]:
        if item:
            breakdown.append(item)

    breakdown += _participant_factor_items(fii_row, "FII", weight=1.5)
    breakdown += _participant_factor_items(dii_row, "DII", weight=0.8)

    if not breakdown:
        return {"score": 0, "label": "No data", "color": "#6b7280", "breakdown": [],
                "summary": "No inputs yet — fill in the fields above and/or upload the Participant OI file."}

    total = round(sum(b["points"] for b in breakdown), 2)
    if total >= 7:
        label, color = "Strongly Bullish for tomorrow", "#16a34a"
    elif total >= 3:
        label, color = "Bullish for tomorrow", "#16a34a"
    elif total <= -7:
        label, color = "Strongly Bearish for tomorrow", "#b91c1c"
    elif total <= -3:
        label, color = "Bearish for tomorrow", "#b91c1c"
    else:
        label, color = "Neutral for tomorrow", "#6b7280"

    n = len(breakdown)
    summary = (f"{n} factor{'s' if n != 1 else ''} combined, weighted score = {total}. "
               f"Reading: {label}.")
    return {"score": total, "label": label, "color": color, "breakdown": breakdown, "summary": summary}


# ---------- NSE Participant-wise Open Interest (Client / DII / FII / Pro) ----------
# Standard 14-column layout of NSE's daily F&O participant OI report:
#   Future Index Long, Future Index Short, Future Stock Long, Future Stock Short,
#   Option Index Call Long, Option Index Call Short, Option Index Put Long,
#   Option Index Put Short, Option Stock Call Long, Option Stock Call Short,
#   Option Stock Put Long, Option Stock Put Short, Total Long, Total Short

OI_COLUMNS = [
    "future_index_long", "future_index_short", "future_stock_long", "future_stock_short",
    "option_index_call_long", "option_index_call_short", "option_index_put_long", "option_index_put_short",
    "option_stock_call_long", "option_stock_call_short", "option_stock_put_long", "option_stock_put_short",
    "total_long", "total_short",
]


def parse_participant_oi_text(text: str):
    """
    Parses NSE's participant-wise OI table. One row per line:
      ParticipantName, val1, val2, ... val14   (comma or whitespace separated)
    Commas used as thousands separators inside numbers are stripped first.
    Returns ({participant_name: {column: value, ...}}, skipped_line_count).
    """
    participants = {}
    skipped = 0
    for line in (text or "").splitlines():
        raw_line = line.strip()
        if not raw_line:
            continue
        # protect thousands-separator commas inside numbers, then split on the
        # remaining structural commas (name vs numbers) — simplest robust way:
        # try comma split first (typical CSV paste), else whitespace split.
        parts = [p.strip() for p in raw_line.split(",") if p.strip() != ""]
        if len(parts) < 15:
            parts = raw_line.split()
        if len(parts) < 15:
            skipped += 1
            continue
        name = parts[0]
        nums = []
        ok = True
        for tok in parts[1:15]:
            tok_clean = tok.replace(",", "").replace("₹", "").strip()
            try:
                nums.append(float(tok_clean))
            except ValueError:
                ok = False
                break
        if not ok:
            skipped += 1
            continue
        participants[name.strip().upper()] = dict(zip(OI_COLUMNS, nums))
    return participants, skipped


def _net_pct(long_val, short_val):
    total = long_val + short_val
    if total <= 0:
        return None
    return (long_val - short_val) / total * 100


def _futures_factor(participant: str, d: dict, weight: float):
    pct = _net_pct(d["future_index_long"], d["future_index_short"])
    if pct is None:
        return None
    if pct > 15:
        pts, tone = 2, "strongly net long"
    elif pct > 5:
        pts, tone = 1, "net long"
    elif pct < -15:
        pts, tone = -2, "strongly net short"
    elif pct < -5:
        pts, tone = -1, "net short"
    else:
        pts, tone = 0, "roughly balanced"
    pts = round(pts * weight, 1)
    msg = (f"{participant} Index Futures: Long {d['future_index_long']:,.0f} vs "
           f"Short {d['future_index_short']:,.0f} ({pct:+.1f}% net, {tone}) → "
           f"{'+' if pts>=0 else ''}{pts} pts. {participant} being net long index futures "
           f"is a bullish signal for the next session; net short is bearish.")
    return {"factor": f"{participant} Index Futures", "points": pts, "message": msg}


def _options_factor(participant: str, d: dict, weight: float):
    call_long, call_short = d["option_index_call_long"], d["option_index_call_short"]
    put_long, put_short = d["option_index_put_long"], d["option_index_put_short"]
    total = call_long + call_short + put_long + put_short
    if total <= 0:
        return None
    call_net = call_long - call_short   # net long calls = bullish stance
    put_net = put_long - put_short      # net long puts = bearish stance (buying downside protection)
    combined = call_net - put_net
    pct = combined / total * 100
    if pct > 15:
        pts, tone = 2, "net positioning skewed bullish (long calls / short puts)"
    elif pct > 5:
        pts, tone = 1, "mildly bullish options positioning"
    elif pct < -15:
        pts, tone = -2, "net positioning skewed bearish (long puts / short calls)"
    elif pct < -5:
        pts, tone = -1, "mildly bearish options positioning"
    else:
        pts, tone = 0, "balanced options positioning"
    pts = round(pts * weight, 1)
    msg = (f"{participant} Index Options: net call bias {call_net:+,.0f}, net put bias "
           f"{put_net:+,.0f} ({pct:+.1f}% combined, {tone}) → {'+' if pts>=0 else ''}{pts} pts. "
           f"Long calls / short puts = betting on upside; long puts / short calls = hedging or "
           f"betting on downside.")
    return {"factor": f"{participant} Index Options", "points": pts, "message": msg}


def _stock_derivatives_factor(participant: str, d: dict, weight: float):
    fut_net = d["future_stock_long"] - d["future_stock_short"]
    opt_net = ((d["option_stock_call_long"] - d["option_stock_call_short"])
               - (d["option_stock_put_long"] - d["option_stock_put_short"]))
    total = (d["future_stock_long"] + d["future_stock_short"]
             + d["option_stock_call_long"] + d["option_stock_call_short"]
             + d["option_stock_put_long"] + d["option_stock_put_short"])
    if total <= 0:
        return None
    combined = fut_net + opt_net
    pct = combined / total * 100
    if pct > 15:
        pts, tone = 1, "net bullish in single-stock derivatives"
    elif pct < -15:
        pts, tone = -1, "net bearish in single-stock derivatives"
    else:
        pts, tone = 0, "balanced"
    pts = round(pts * weight, 1)
    msg = (f"{participant} Stock F&O: combined net {combined:+,.0f} ({pct:+.1f}%, {tone}) → "
           f"{'+' if pts>=0 else ''}{pts} pts.")
    return {"factor": f"{participant} Stock F&O", "points": pts, "message": msg}


def compute_participant_sentiment(participants: dict):
    """
    Builds next-session sentiment from NSE's participant-wise OI report.
    FII is weighted highest (biggest, most-watched mover), DII second,
    Pro (prop desks) third. Client (retail) is shown for reference only —
    often read as a contrarian indicator, so it is NOT scored into the
    total (deliberately, to avoid double-counting the same market against
    itself); it is still returned in the breakdown as context.
    """
    breakdown = []
    weights = {"FII": 1.5, "DII": 1.0, "PRO": 0.5}
    for participant, weight in weights.items():
        d = participants.get(participant)
        if not d:
            continue
        for factor_fn in (_futures_factor, _options_factor, _stock_derivatives_factor):
            item = factor_fn(participant, d, weight)
            if item:
                breakdown.append(item)

    # Client (retail) shown as context only — not scored
    client = participants.get("CLIENT")
    context_msg = None
    if client:
        pct = _net_pct(client["future_index_long"], client["future_index_short"])
        if pct is not None:
            context_msg = (f"Client (retail) Index Futures net = {pct:+.1f}% "
                            f"— shown for context only, not scored (retail positioning is "
                            f"often read as a contrarian indicator, so including it in the "
                            f"main score would effectively count the market against itself).")

    if not breakdown:
        return {"score": 0, "label": "No data", "color": "#6b7280", "breakdown": [],
                "context": context_msg, "summary": "No usable FII/DII/Pro rows found."}

    total = round(sum(b["points"] for b in breakdown), 1)
    if total >= 5:
        label, color = "Strongly Bullish", "#16a34a"
    elif total >= 2:
        label, color = "Bullish", "#16a34a"
    elif total <= -5:
        label, color = "Strongly Bearish", "#b91c1c"
    elif total <= -2:
        label, color = "Bearish", "#b91c1c"
    else:
        label, color = "Neutral", "#6b7280"

    summary = (f"Combined FII/DII/Pro positioning score = {total}. "
               f"Next-session reading: {label}.")

    return {"score": total, "label": label, "color": color, "breakdown": breakdown,
            "context": context_msg, "summary": summary}
