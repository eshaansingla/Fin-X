# backend/services/nse_service.py
"""
NSE live quote service using NSE India's internal API.
Exposes: get_quote(symbol), get_bulk_quotes(symbols), get_historical(symbol, period)
Cache TTL: 8 seconds for quotes, 60 seconds for historical
Fallback: yfinance if NSE API fails
"""

import time
import datetime
import threading
import os
import requests as _requests
from typing import Optional

_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

NSE_BASE = "https://www.nseindia.com"

# ── Dedicated equity-quote session ───────────────────────────
# Uses gzip/deflate only (no 'br'/Brotli) since Python requests
# can't decompress Brotli without brotlipy, causing empty bodies.
_EQ_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",   # NO 'br' — avoids Brotli decode failure
    "Referer":         "https://www.nseindia.com/",
    "Connection":      "keep-alive",
}

_eq_session: _requests.Session | None = None
_eq_lock = threading.Lock()


def _get_eq_session() -> _requests.Session:
    """Return (or create) a warmed-up session for the equity-quote endpoint."""
    global _eq_session
    with _eq_lock:
        if _eq_session is None:
            s = _requests.Session()
            s.headers.update(_EQ_HEADERS)
            try:
                s.get(NSE_BASE, timeout=8)
                time.sleep(0.8)
                # Visit the equity page to get required cookies (nsit, browse-url)
                s.get(f"{NSE_BASE}/get-quotes/equity?symbol=RELIANCE", timeout=8)
                time.sleep(0.5)
                print("[NSE-EQ] Equity session warmed up")
            except Exception as e:
                print(f"[NSE-EQ] Warmup error: {e}")
            _eq_session = s
        return _eq_session


def _reset_eq_session():
    global _eq_session
    with _eq_lock:
        _eq_session = None
    print("[NSE-EQ] Session reset")

# ── Caches ────────────────────────────────────────────────────
_quote_cache: dict = {}   # {symbol: (timestamp, data)}
_hist_cache:  dict = {}   # {"symbol_period": (timestamp, data)}
_cache_lock   = threading.Lock()
_hot_symbols: dict[str, float] = {}  # {symbol: last_requested_ts}
QUOTE_TTL       = max(1, int(os.getenv("QUOTE_TTL_SECONDS", "2")))   # seconds
HIST_TTL        = max(10, int(os.getenv("HIST_TTL_SECONDS", "60")))  # seconds
HIST_TTL_1D_OPEN   =  max(1, int(os.getenv("HIST_TTL_1D_OPEN_SECONDS", "2")))  # seconds
HIST_TTL_1D_CLOSED = 300 # seconds — intraday cache after market close
HOT_SYMBOL_TTL_SECONDS = max(10, int(os.getenv("HOT_SYMBOL_TTL_SECONDS", "180")))
MAX_HOT_SYMBOLS = max(5, int(os.getenv("MAX_HOT_SYMBOLS", "20")))

# Common English words / finance terms to skip in symbol detection
_STOPWORDS = {
    "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER",
    "WAS", "ONE", "OUR", "OUT", "DAY", "GET", "HAS", "HIM", "HIS", "HOW",
    "ITS", "MAY", "NEW", "NOW", "OLD", "SEE", "TWO", "WAY", "WHO", "BOY",
    "DID", "LET", "PUT", "SAY", "SHE", "TOO", "USE", "BUY", "SELL", "NSE",
    "BSE", "IPO", "ETF", "LTP", "WHAT", "WHEN", "THIS", "WITH", "THAT",
    "FROM", "HAVE", "WILL", "BEEN", "THEY", "WERE", "SAID", "EACH", "TELL",
    "DOES", "SOME", "THAN", "THEN", "THEM", "ALSO", "VERY", "JUST", "OVER",
    "KNOW", "INTO", "GOOD", "MUCH", "LIKE", "TIME", "YEAR", "MAKE", "LOOK",
    "COME", "GIVE", "EVEN", "BACK", "ONLY", "WELL", "MOST", "AFTER", "BEFORE",
    "ABOUT", "STOCK", "SHARE", "PRICE", "TRADE", "MARKET", "INDEX", "TODAY",
    "NIFTY", "SENSEX", "WANT", "SHOULD", "WOULD", "COULD", "GOING", "DOING",
    "THINK", "TELL", "SHOW", "GIVE", "TAKE", "COME", "HELP", "NEED", "WANT",
    "MEAN", "CALL", "KEEP", "FEEL", "FALL", "RISE", "HIGH", "LAST", "NEXT",
    "DOWN", "SURE", "LONG", "TERM", "VIEW", "HOLD", "OPEN", "LIVE", "REAL",
    "DATA", "NEWS", "RATE", "FUND", "BANK", "YEAR", "WEEK", "MONTH", "BEST",
    "PLAN", "GROW", "BULL", "BEAR", "ZONE", "RISK", "LOSS", "GAIN",
    # Short common English words (2-3 letters)
    "IS", "IT", "IN", "AN", "AT", "SO", "NO", "DO", "GO", "TO", "AM", "BE",
    "MY", "BY", "UP", "AS", "IF", "OR", "OF", "ON", "ME", "HE", "US", "WE",
    "HI", "OK", "YES", "HEY", "ITS", "ITS",
    # Common words that appear after uppercasing sentences
    "PLEASE", "THANKS", "HELLO", "THERE", "THEIR", "WHERE", "WHICH", "WHILE",
    "THESE", "THOSE", "FIRST", "SECOND", "THIRD", "RIGHT", "WRONG", "AGAIN",
    "STILL", "OFTEN", "SINCE", "BELOW", "ABOVE", "BOTH", "EACH", "PART",
    "SUCH", "SAME", "BOTH", "LESS", "MORE", "TRUE", "LATE", "TELL", "FELL",
    "CASE", "MOVE", "NEED", "TURN", "PAST", "PUTS", "CALL", "PUTS", "TYPE",
    "FORM", "SHOW", "MEAN", "HELD", "HOLD", "GOES", "NEAR", "HARD", "FAST",
    "SLOW", "FELL", "MOVE", "STEP", "SIDE", "AREA", "HOME", "WORK", "CITY",
    "AREA", "FACT", "IDEA", "LIFE", "HAND", "FACE", "WORD", "FIRE", "DARK",
}


# ── Validators ───────────────────────────────────────────────
def _is_valid_symbol(symbol: str) -> bool:
    """Symbol must be 2–10 uppercase alphanumeric characters."""
    if not symbol:
        return False
    if len(symbol) < 2 or len(symbol) > 10:
        return False
    return symbol.isalnum()


def register_hot_symbol(symbol: str) -> None:
    """
    Mark a symbol as actively requested by clients so cache warmers can prioritize it.
    """
    sym = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
    if not _is_valid_symbol(sym):
        return
    now = time.time()
    with _cache_lock:
        _hot_symbols[sym] = now
        # Keep this map bounded.
        if len(_hot_symbols) > (MAX_HOT_SYMBOLS * 2):
            stale_cutoff = now - HOT_SYMBOL_TTL_SECONDS
            stale = [k for k, ts in _hot_symbols.items() if ts < stale_cutoff]
            for k in stale:
                _hot_symbols.pop(k, None)
            if len(_hot_symbols) > MAX_HOT_SYMBOLS:
                keep = sorted(_hot_symbols.items(), key=lambda kv: kv[1], reverse=True)[:MAX_HOT_SYMBOLS]
                _hot_symbols.clear()
                _hot_symbols.update(dict(keep))


def get_hot_symbols(limit: int = 10) -> list[str]:
    now = time.time()
    with _cache_lock:
        stale_cutoff = now - HOT_SYMBOL_TTL_SECONDS
        for k in [k for k, ts in _hot_symbols.items() if ts < stale_cutoff]:
            _hot_symbols.pop(k, None)
        ordered = sorted(_hot_symbols.items(), key=lambda kv: kv[1], reverse=True)
    return [k for k, _ in ordered[: max(1, limit)]]


def _downsample_points(points: list[dict], max_points: int) -> list[dict]:
    if len(points) <= max_points or max_points <= 0:
        return points
    # Uniform downsample while preserving first/last points.
    step = (len(points) - 1) / (max_points - 1)
    idxs = {0, len(points) - 1}
    for i in range(1, max_points - 1):
        idxs.add(int(round(i * step)))
    return [points[i] for i in sorted(idxs)]


# ── NSE API fetch ─────────────────────────────────────────────
def _fetch_nse_quote_raw(symbol: str, _retry: int = 0) -> Optional[dict]:
    """Fetch raw JSON from NSE quote-equity endpoint. Returns None on any failure."""
    if _retry >= 3:
        print(f"[NSE] Max retries reached for {symbol}")
        return None
    session = _get_eq_session()
    try:
        resp = session.get(
            f"{NSE_BASE}/api/quote-equity",
            params={"symbol": symbol},
            timeout=8,
        )
        if resp.status_code == 403:
            print(f"[NSE] 403 for {symbol} — resetting equity session (attempt {_retry + 1}/3)")
            _reset_eq_session()
            time.sleep(1)
            return _fetch_nse_quote_raw(symbol, _retry + 1)
        if resp.status_code in (404, 400):
            return None
        resp.raise_for_status()
        if not resp.content:
            print(f"[NSE] Empty response for {symbol}")
            return None
        data = resp.json()
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[NSE] Quote fetch error for {symbol}: {e}")
        return None


def _normalize_quote(symbol: str, raw: dict) -> dict:
    """
    Extract and normalize fields from raw NSE quote-equity response.
    Missing fields are set to None — never raises.
    """
    price_info = raw.get("priceInfo") or {}
    order_book = raw.get("marketDeptOrderBook") or {}
    trade_info = order_book.get("tradeInfo") or {}
    intraday   = price_info.get("intraDayHighLow") or {}

    def _f(val) -> Optional[float]:
        try:
            return round(float(val), 2) if val is not None else None
        except (TypeError, ValueError):
            return None

    def _i(val) -> Optional[int]:
        try:
            return int(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "symbol":         symbol.upper(),
        "price":          _f(price_info.get("lastPrice")),
        "change":         _f(price_info.get("change")),
        "percent_change": _f(price_info.get("pChange")),
        "open":           _f(price_info.get("open")),
        "high":           _f(intraday.get("max")),
        "low":            _f(intraday.get("min")),
        "prev_close":     _f(price_info.get("previousClose") or price_info.get("close")),
        "volume":         _i(trade_info.get("totalTradedVolume")),
        "timestamp":      datetime.datetime.utcnow().isoformat(),
        "raw_data":       raw,
    }


# ── yfinance fallback ─────────────────────────────────────────
def _yahoo_fallback(symbol: str) -> Optional[dict]:
    """
    Fallback using direct Yahoo Finance chart API.
    Does NOT use yfinance library (which has Brotli decode issues).
    """
    try:
        resp = _requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS",
            params={"range": "2d", "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("chart", {}).get("error"):
            return None
        result = (data.get("chart", {}).get("result") or [None])[0]
        if not result:
            return None

        meta   = result.get("meta") or {}
        quotes = ((result.get("indicators") or {}).get("quote") or [{}])[0]

        ltp        = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        opens      = quotes.get("open",   [])
        highs      = quotes.get("high",   [])
        lows       = quotes.get("low",    [])
        volumes    = quotes.get("volume", [])

        if ltp is None:
            return None

        ltp        = float(ltp)
        change     = round(ltp - float(prev_close), 2) if prev_close else 0
        pchange    = round((change / float(prev_close)) * 100, 2) if prev_close else 0

        def _last(lst):
            vals = [v for v in lst if v is not None]
            return round(float(vals[-1]), 2) if vals else None

        return {
            "symbol":         symbol.upper(),
            "price":          round(ltp, 2),
            "change":         change,
            "percent_change": pchange,
            "open":           _last(opens),
            "high":           _last(highs),
            "low":            _last(lows),
            "prev_close":     round(float(prev_close), 2) if prev_close else None,
            "volume":         int(volumes[-1]) if volumes and volumes[-1] else None,
            "timestamp":      datetime.datetime.utcnow().isoformat(),
            "raw_data":       None,
        }
    except Exception as e:
        print(f"[Yahoo] Fallback error for {symbol}: {e}")
        return None


# ── Public: get_quote ─────────────────────────────────────────
def get_quote(symbol: str) -> Optional[dict]:
    """
    Get live NSE quote for a symbol.
    Pipeline: cache → NSE API → yfinance → None
    Never raises. Returns None if all sources fail.
    """
    symbol = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
    if not _is_valid_symbol(symbol):
        return None
    register_hot_symbol(symbol)

    now = time.time()
    with _cache_lock:
        entry = _quote_cache.get(symbol)
        if entry and (now - entry[0]) < QUOTE_TTL:
            return entry[1]

    # Try NSE API
    raw = _fetch_nse_quote_raw(symbol)
    if raw and isinstance(raw.get("priceInfo"), dict):
        result = _normalize_quote(symbol, raw)
        with _cache_lock:
            _quote_cache[symbol] = (time.time(), result)
        return result

    # Fallback to direct Yahoo Finance API
    print(f"[NSE] API miss for {symbol} — falling back to Yahoo Finance")
    result = _yahoo_fallback(symbol)
    with _cache_lock:
        _quote_cache[symbol] = (time.time(), result)
    return result


# ── Public: get_bulk_quotes ───────────────────────────────────
def get_bulk_quotes(symbols: list) -> dict:
    """
    Get live NSE quotes for a list of symbols.
    Returns {symbol: quote_dict_or_None}. Deduplicates input.
    Fetches in parallel (up to 10 concurrent) for performance.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    seen: set = set()
    unique: list = []
    for sym in symbols:
        sym = sym.upper().strip().replace(".NS", "").replace(".BO", "")
        if sym and sym not in seen:
            seen.add(sym)
            unique.append(sym)

    if not unique:
        return {}

    results: dict = {}
    max_workers = min(10, len(unique))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_quote, sym): sym for sym in unique}
        for future in as_completed(futures):
            sym = futures[future]
            try:
                results[sym] = future.result()
            except Exception as e:
                print(f"[BulkQuotes] Error for {sym}: {e}")
                results[sym] = None
    return results


# ── Public: get_historical ────────────────────────────────────
def get_historical(symbol: str, period: str = "1m") -> list:
    """
    Get historical price data for charting.
    period: '1d', '1w', '1m', '5y', 'max'
    Returns: [{'time': str, 'price': float}, ...]
    Never raises — returns [] on failure.
    """
    symbol = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
    if not _is_valid_symbol(symbol):
        return []
    register_hot_symbol(symbol)

    cache_key = f"{symbol}_{period}"
    now = time.time()

    # Use a shorter TTL for intraday data while the market is live
    if period == '1d':
        try:
            from services.market_hours import is_market_open
            _ttl = HIST_TTL_1D_OPEN if is_market_open() else HIST_TTL_1D_CLOSED
        except Exception:
            _ttl = HIST_TTL
    else:
        _ttl = HIST_TTL

    with _cache_lock:
        entry = _hist_cache.get(cache_key)
        if entry and (now - entry[0]) < _ttl:
            return entry[1]

    _period_map = {
        "1d": ("1d",  "5m"),
        "1w": ("5d",  "60m"),
        "1m": ("1mo", "1d"),
        "5y": ("5y",  "1d"),
        "max": ("max", "1wk"),
    }
    _, interval = _period_map.get(period, ("1mo", "1d"))

    # Use direct Yahoo Finance chart API (avoids yfinance Brotli issues)
    _range_map = {"1d": "1d", "1w": "5d", "1m": "1mo", "5y": "5y", "max": "max"}
    yf_range = _range_map.get(period, "1mo")
    try:
        resp = _requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS",
            params={"range": yf_range, "interval": interval},
            headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"},
            timeout=10,
        )
        resp.raise_for_status()
        data   = resp.json()
        chart  = data.get("chart") or {}
        res    = (chart.get("result") or [None])[0]
        if not res:
            result = []
        else:
            timestamps = res.get("timestamp") or []
            closes     = ((res.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
            items = []
            for ts, c in zip(timestamps, closes):
                if c is None:
                    continue
                try:
                    t = datetime.datetime.fromtimestamp(ts, tz=_IST)
                    if period == "1d":
                        label = t.strftime("%Y-%m-%dT%H:%M")
                    elif period == "1w":
                        label = str(t.date())
                    elif period == "1m":
                        label = str(t.date())
                    elif period == "5y":
                        label = str(t.date())
                    else:  # max
                        label = str(t.date())
                    items.append({"time": label, "price": round(float(c), 2)})
                except Exception:
                    continue
            if period == "5y":
                result = _downsample_points(items, max_points=1250)
            elif period == "max":
                result = _downsample_points(items, max_points=1500)
            else:
                result = items
    except Exception as e:
        print(f"[Historical] Error for {symbol} period={period}: {e}")
        result = []

    with _cache_lock:
        _hist_cache[cache_key] = (time.time(), result)
    return result


# ── Symbol extraction from free text ─────────────────────────
def extract_symbols_from_text(text: str) -> list:
    """
    Extract potential NSE ticker symbols from free text.
    Input is uppercased before matching so 'reliance' → 'RELIANCE'.
    Returns list of candidate symbols (may be empty).
    """
    import re
    upper = text.upper()
    candidates = re.findall(r'\b([A-Z][A-Z0-9]{1,9})\b', upper)
    return [c for c in candidates if c not in _STOPWORDS]
