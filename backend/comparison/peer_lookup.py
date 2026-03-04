"""
comparison/peer_lookup.py — Dynamic yfinance peer resolution.

Allows explicit peer passing via the ?peers= query param, or falls back to
an internal sector map for large-cap defaults.
"""

from typing import List
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# Fallback map for common tech/mega-cap if not provided
DEFAULT_PEERS = {
    "AAPL": ["MSFT", "GOOG", "HPQ"],
    "MSFT": ["AAPL", "GOOG", "ORCL"],
    "GOOG": ["META", "MSFT", "AAPL"],
    "META": ["SNAP", "PINS", "GOOG"],
    "AMZN": ["WMT", "TGT", "EBAY", "BABA"],
    "TSLA": ["F", "GM", "TM"],
    "NVDA": ["AMD", "INTC", "QCOM"],
    "JPM": ["BAC", "C", "WFC"],
}

def get_peer_companies(ticker: str, explicit_peers: str = None) -> List[str]:
    """
    Resolve 3-5 peer companies for benchmarking.
    """
    ticker = ticker.upper()
    
    # 1. Explicitly provided in route
    if explicit_peers is not None and explicit_peers.strip():
        peers = [p.strip().upper() for p in explicit_peers.split(",") if p.strip()]
        # Remove self
        peers = [p for p in peers if p != ticker]
        if peers:
            return peers
            
    # 2. Hardcoded common defaults
    if ticker in DEFAULT_PEERS:
        return DEFAULT_PEERS[ticker]
        
    # 3. Dynamic lookup attempt via info (Sector matching fallback)
    try:
        t = yf.Ticker(ticker)
        info = t.info
        sector = info.get("sector")
        
        # In a real enterprise system, we would query a database of 10,000 tickers
        # by sector here. Because we don't have a local DB of all tickers, we will
        # return a generic market fallback if we can't sector match.
        if sector == "Technology":
            return ["MSFT", "AAPL", "GOOG"]
        elif sector == "Financial Services":
            return ["JPM", "BAC", "GS"]
        elif sector == "Healthcare":
            return ["JNJ", "UNH", "PFE"]
        elif sector == "Consumer Cyclical":
            return ["AMZN", "HD", "MCD"]
            
    except Exception as e:
        logger.warning(f"Failed to dynamically lookup sector for {ticker}: {str(e)}")
        
    # 4. Ultimate fallback - broad market index proxies
    return ["SPY", "QQQ"]
