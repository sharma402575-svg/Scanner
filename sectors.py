"""
Sector -> constituent stock mapping for NSE (yfinance tickers use .NS suffix).
Each sector also maps to a benchmark sector index (Yahoo Finance ticker) used
to compute the R Factor (relative strength vs sector).

BANK list matches the 12 constituents of the Nifty Bank index.
Other sectors are a curated liquid subset — expand freely.
"""

SECTOR_INDEX = {
    "BANK":     "^NSEBANK",     # Nifty Bank
    "IT":       "^CNXIT",       # Nifty IT
    "AUTO":     "^CNXAUTO",     # Nifty Auto
    "PHARMA":   "^CNXPHARMA",   # Nifty Pharma
    "FMCG":     "^CNXFMCG",     # Nifty FMCG
    "METAL":    "^CNXMETAL",    # Nifty Metal
    "ENERGY":   "^CNXENERGY",   # Nifty Energy
    "REALTY":   "^CNXREALTY",   # Nifty Realty
}

SECTOR_STOCKS = {
    "BANK": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS",
        "IDFCFIRSTB.NS", "FEDERALBNK.NS", "AUBANK.NS", "CANBK.NS",
    ],
    "IT": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS",
    ],
    "AUTO": [
        "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS",
        "EICHERMOT.NS", "HEROMOTOCO.NS", "TVSMOTOR.NS", "ASHOKLEY.NS",
    ],
    "PHARMA": [
        "SUNPHARMA.NS", "DIVISLAB.NS", "CIPLA.NS", "DRREDDY.NS",
        "APOLLOHOSP.NS", "LUPIN.NS", "AUROPHARMA.NS", "TORNTPHARM.NS",
    ],
    "FMCG": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS",
        "TATACONSUM.NS", "DABUR.NS", "MARICO.NS", "GODREJCP.NS",
    ],
    "METAL": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS",
        "SAIL.NS", "NMDC.NS", "JINDALSTEL.NS",
    ],
    "ENERGY": [
        "RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS",
        "COALINDIA.NS", "BPCL.NS", "IOC.NS", "GAIL.NS",
    ],
    "REALTY": [
        "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS",
        "PRESTIGE.NS", "BRIGADE.NS",
    ],
}
