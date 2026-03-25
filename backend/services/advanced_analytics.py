# backend/services/advanced_analytics.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from services.indicators import add_ns_suffix, compute_rsi_manual
from services.news_fetcher import get_stock_news
from services.gpt import gemini_call, load_prompt, parse_json_response
from database import db_fetchall

SECTORS = {
    "RELIANCE": "Energy", "TCS": "IT", "INFY": "IT", "HDFCBANK": "Finance",
    "ICICIBANK": "Finance", "TATAMOTORS": "Auto", "WIPRO": "IT", "BAJFINANCE": "Finance",
    "SUNPHARMA": "Pharma", "ITC": "FMCG", "SBIN": "Finance", "ADANIENT": "Infrastructure",
    "MARUTI": "Auto", "NESTLEIND": "FMCG", "POWERGRID": "Energy"
}

def get_pattern_success_rate(symbol: str, signal_type: str) -> dict:
    """
    Back-tests a signal over 2 years of daily data.
    Returns the % of times the stock was higher 5 days after the signal triggered.
    """
    ns_symbol = add_ns_suffix(symbol)
    try:
        ticker = yf.Ticker(ns_symbol)
        hist = ticker.history(period="2y")
        if hist.empty:
            return {"error": "No data found", "symbol": symbol}
        
        close = hist["Close"]
        occurrences = 0
        successes = 0
        
        # Calculate indicators needed for backtesting
        if signal_type.lower() == "rsi < 30":
            rsi = compute_rsi_manual(close, 14)
            for i in range(14, len(rsi) - 5):
                # Triggered when RSI dips below 30
                if rsi.iloc[i-1] >= 30 and rsi.iloc[i] < 30:
                    occurrences += 1
                    # Check price 5 days later
                    if close.iloc[i+5] > close.iloc[i]:
                        successes += 1
        else: # Default behavior: just look for generic bullish crossovers (EMA 20 > EMA 50)
            ema20 = close.ewm(span=20, adjust=False).mean()
            ema50 = close.ewm(span=50, adjust=False).mean()
            for i in range(50, len(close) - 5):
                if ema20.iloc[i-1] <= ema50.iloc[i-1] and ema20.iloc[i] > ema50.iloc[i]:
                    occurrences += 1
                    if close.iloc[i+5] > close.iloc[i]:
                        successes += 1
        
        win_rate = (successes / occurrences * 100) if occurrences > 0 else 0
        return {
            "symbol": symbol,
            "signal_type": signal_type,
            "occurrences": occurrences,
            "win_rate": round(win_rate, 2),
            "successes": successes
        }
    except Exception as e:
        print(f"[Analytics] Error in get_pattern_success_rate for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol, "win_rate": None}

def get_institutional_clusters() -> dict:
    """
    Queries bulk_deals within the last 7 days.
    Groups by sector, and flags if >= 3 diff institutions entered same sector.
    """
    try:
        cutoff = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        query = "SELECT symbol, client_name, deal_type FROM bulk_deals WHERE fetched_at >= ? OR deal_date >= ?"
        # Alternatively, if deal_date is more reliable:
        # Note: deal_date might just be YYYY-MM-DD
        deals = db_fetchall(query, (cutoff, (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')))
        
        # Aggregate by sector
        sector_institutions = {}
        for d in deals:
            sym = d["symbol"].upper().replace(".NS", "")
            sector = SECTORS.get(sym, "Other")
            client = d.get("client_name", "Unknown")
            
            if sector not in sector_institutions:
                sector_institutions[sector] = set()
            sector_institutions[sector].add(client)
        
        clusters = []
        for sector, clients in sector_institutions.items():
            if len(clients) >= 3:
                clusters.append({
                    "sector": sector,
                    "institution_count": len(clients),
                    "flag": "High Conviction Sector Cluster",
                    "clients": list(clients)[:5] # Show up to 5
                })
        
        return {"clusters": clusters}
    except Exception as e:
        print(f"[Analytics] Error in get_institutional_clusters: {e}")
        return {"error": str(e), "clusters": []}

def analyze_management_tone(symbol: str) -> dict:
    """
    Fetches news/commentary and uses GPT to compare sentiment tone shift.
    """
    docs = get_stock_news(symbol, max_age_minutes=60*24*7) # Look back a week to get enough articles
    snippets = [n["headline"] for n in docs[:4]] if docs else []
    
    _fallback = {
        "symbol": symbol,
        "tone_shift_score": 0.0,
        "explanation": "Not enough news data to determine management tone shift."
    }
    
    if not snippets:
        return _fallback
        
    try:
        prompt_template = load_prompt("tone.txt")
        if not prompt_template:
            prompt_template = "Analyze the tone shift from these news snippets: {news_snippets}. Return JSON with 'tone_shift_score' (-1.0 to 1.0) and 'explanation'."
            
        prompt = prompt_template.format(news_snippets=json.dumps(snippets, indent=2))
        raw = gemini_call(prompt, json_mode=True, max_tokens=256)
        
        parsed = parse_json_response(raw, fallback=_fallback)
        parsed["symbol"] = symbol
        return parsed
    except Exception as e:
        print(f"[Analytics] Error in analyze_management_tone for {symbol}: {e}")
        return _fallback
