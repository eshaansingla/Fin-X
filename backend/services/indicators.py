import pandas as pd
import yfinance as yf

try:
    import pandas_ta as ta
    USE_PANDAS_TA = True
except ImportError:
    USE_PANDAS_TA = False
    ta = None

try:
    from ta.momentum import RSIIndicator
    from ta.trend import EMAIndicator, SMAIndicator

    USE_TA_LIB = True
except ImportError:
    USE_TA_LIB = False
    print("[Indicators] ta lib not available - using manual RSI calculation")

POPULAR_STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "TATAMOTORS.NS",
    "WIPRO.NS",
    "BAJFINANCE.NS",
    "SUNPHARMA.NS",
    "ITC.NS",
    "SBIN.NS",
    "ADANIENT.NS",
    "MARUTI.NS",
    "NESTLEIND.NS",
    "POWERGRID.NS",
]


def add_ns_suffix(symbol: str) -> str:
    symbol = symbol.upper().strip()
    if symbol.startswith("^"):
        return symbol
    return symbol if (symbol.endswith(".NS") or symbol.endswith(".BO")) else f"{symbol}.NS"


def compute_rsi_manual(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
    avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def interpret_rsi(rsi_val) -> str:
    if rsi_val is None or (hasattr(rsi_val, "__float__") and pd.isna(rsi_val)):
        return "unknown"
    v = float(rsi_val)
    if v >= 70:
        return "overbought"
    if v >= 60:
        return "approaching_overbought"
    if v <= 30:
        return "oversold"
    if v <= 40:
        return "approaching_oversold"
    return "neutral"


def _get_stock_data_yahoo_direct(symbol: str, period: str = "3mo") -> dict:
    """
    Fetch stock history directly from Yahoo Finance chart API.
    Used as fallback when yfinance library fails (Brotli decode errors).
    """
    import requests as _req, datetime as _dt
    _range_map = {"1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y"}
    yf_range = _range_map.get(period, "3mo")
    try:
        resp = _req.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS",
            params={"range": yf_range, "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"},
            timeout=12,
        )
        resp.raise_for_status()
        data  = resp.json()
        res   = (data.get("chart", {}).get("result") or [None])[0]
        if not res:
            return {"error": "No data", "symbol": symbol}

        meta       = res.get("meta") or {}
        timestamps = res.get("timestamp") or []
        q          = ((res.get("indicators") or {}).get("quote") or [{}])[0]
        closes     = q.get("close",  [])
        opens      = q.get("open",   [])
        highs      = q.get("high",   [])
        lows       = q.get("low",    [])
        volumes    = q.get("volume", [])

        # Filter out None values, keeping aligned lists
        valid = [(ts, c, o, h, l, v) for ts, c, o, h, l, v
                 in zip(timestamps, closes, opens, highs, lows, volumes)
                 if c is not None]
        if len(valid) < 5:
            return {"error": "Insufficient data", "symbol": symbol}

        dates_all  = [str(_dt.datetime.utcfromtimestamp(r[0]).date()) for r in valid]
        close_arr  = pd.Series([r[1] for r in valid], dtype=float)

        # Compute indicators from close prices
        if USE_PANDAS_TA and ta:
            rsi_s   = ta.rsi(close_arr, length=14)
            ema20_s = ta.ema(close_arr, length=20)
            ema50_s = ta.ema(close_arr, length=50)
        elif USE_TA_LIB:
            rsi_s   = RSIIndicator(close=close_arr, window=14).rsi()
            ema20_s = EMAIndicator(close=close_arr, window=20).ema_indicator()
            ema50_s = EMAIndicator(close=close_arr, window=50).ema_indicator()
        else:
            rsi_s   = compute_rsi_manual(close_arr, 14)
            ema20_s = close_arr.ewm(span=20, adjust=False).mean()
            ema50_s = close_arr.ewm(span=50, adjust=False).mean()

        def _safe_last(s):
            """Return last non-NaN value of a Series, or None if series is None/empty."""
            if s is None or len(s) == 0:
                return None
            v = s.iloc[-1]
            return float(v) if pd.notna(v) else None

        last_rsi   = _safe_last(rsi_s)
        last_ema20 = _safe_last(ema20_s)
        last_ema50 = _safe_last(ema50_s)

        ema_signal = "neutral"
        if last_ema20 and last_ema50:
            prev_ema20 = float(ema20_s.iloc[-2]) if (ema20_s is not None and len(ema20_s) >= 2) else last_ema20
            prev_ema50 = float(ema50_s.iloc[-2]) if (ema50_s is not None and len(ema50_s) >= 2) else last_ema50
            if last_ema20 > last_ema50:
                ema_signal = "bullish_crossover" if prev_ema20 <= prev_ema50 else "bullish"
            elif last_ema20 < last_ema50:
                ema_signal = "bearish_crossover" if prev_ema20 >= prev_ema50 else "bearish"

        ltp = float(meta.get("regularMarketPrice") or valid[-1][1])
        prev_c = float(valid[-2][1]) if len(valid) >= 2 else ltp
        change_pct = round((ltp - prev_c) / prev_c * 100, 2) if prev_c else 0

        last_30 = [round(r[1], 2) for r in valid[-30:]]
        dates_30 = dates_all[-30:]

        highs = [r[3] for r in valid if r[3] is not None and r[3] > 0]
        lows  = [r[4] for r in valid if r[4] is not None and r[4] > 0]
        return {
            "symbol":        symbol.upper(),
            "current_price": round(ltp, 2),
            "change_pct":    change_pct,
            "volume":        int(valid[-1][5] or 0),
            "rsi":           round(float(last_rsi), 1) if last_rsi else None,
            "ema20":         round(float(last_ema20), 2) if last_ema20 else None,
            "ema50":         round(float(last_ema50), 2) if last_ema50 else None,
            "sma200":        None,
            "ema_signal":    ema_signal,
            "rsi_zone":      interpret_rsi(last_rsi),
            "price_30d":     last_30,
            "dates_30d":     dates_30,
            "high_52w":      round(max(highs), 2) if highs else None,
            "low_52w":       round(min(lows),  2) if lows  else None,
            "avg_volume_20d": int(sum(r[5] for r in valid[-20:] if r[5]) / min(20, len(valid))),
        }
    except Exception as e:
        print(f"[Indicators-Direct] Error for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


def get_stock_data(symbol: str, period: str = "3mo") -> dict:
    ns_symbol = add_ns_suffix(symbol)
    try:
        ticker = yf.Ticker(ns_symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            hist = ticker.history(period="1mo")
            if hist.empty:
                print(f"[Indicators] yfinance empty for {symbol} — trying direct Yahoo API")
                return _get_stock_data_yahoo_direct(symbol, period)

        close = hist["Close"]
        if USE_PANDAS_TA:
            hist["RSI"] = ta.rsi(close, length=14)
            hist["EMA20"] = ta.ema(close, length=20)
            hist["EMA50"] = ta.ema(close, length=50)
            hist["SMA200"] = ta.sma(close, length=200)
        elif USE_TA_LIB:
            hist["RSI"] = RSIIndicator(close=close, window=14).rsi()
            hist["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
            hist["EMA50"] = EMAIndicator(close=close, window=50).ema_indicator()
            hist["SMA200"] = SMAIndicator(close=close, window=200).sma_indicator()
        else:
            hist["RSI"] = compute_rsi_manual(close, 14)
            hist["EMA20"] = close.ewm(span=20, adjust=False).mean()
            hist["EMA50"] = close.ewm(span=50, adjust=False).mean()
            hist["SMA200"] = close.rolling(200).mean()

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else latest
        ema_signal = "neutral"
        if pd.notna(latest["EMA20"]) and pd.notna(latest["EMA50"]):
            if latest["EMA20"] > latest["EMA50"]:
                ema_signal = "bullish_crossover" if prev["EMA20"] <= prev["EMA50"] else "bullish"
            elif latest["EMA20"] < latest["EMA50"]:
                ema_signal = "bearish_crossover" if prev["EMA20"] >= prev["EMA50"] else "bearish"

        last_30 = hist.tail(30)["Close"].round(2).tolist()
        dates_30 = [str(d.date()) for d in hist.tail(30).index]
        current_price = round(float(latest["Close"]), 2)
        prev_price = round(float(prev["Close"]), 2)
        change_pct = round((current_price - prev_price) / prev_price * 100, 2)

        return {
            "symbol": symbol.upper(),
            "current_price": current_price,
            "change_pct": change_pct,
            "volume": int(latest.get("Volume", 0)),
            "rsi": round(float(latest["RSI"]), 1) if pd.notna(latest["RSI"]) else None,
            "ema20": round(float(latest["EMA20"]), 2) if pd.notna(latest["EMA20"]) else None,
            "ema50": round(float(latest["EMA50"]), 2) if pd.notna(latest["EMA50"]) else None,
            "sma200": round(float(latest["SMA200"]), 2) if pd.notna(latest["SMA200"]) else None,
            "ema_signal": ema_signal,
            "rsi_zone": interpret_rsi(latest["RSI"]),
            "price_30d": last_30,
            "dates_30d": dates_30,
            "high_52w": round(float(hist["High"].max()), 2),
            "low_52w": round(float(hist["Low"].min()), 2),
            "avg_volume_20d": int(hist["Volume"].tail(20).mean()),
        }
    except Exception as e:
        print(f"[Indicators] yfinance error for {symbol}: {e} — trying direct Yahoo API")
        return _get_stock_data_yahoo_direct(symbol, period)


def get_nifty_snapshot() -> dict:
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d")
        if len(hist) < 2:
            return {}
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        change_pct = round(
            (float(latest["Close"]) - float(prev["Close"])) / float(prev["Close"]) * 100, 2
        )
        return {
            "nifty50": round(float(latest["Close"]), 2),
            "nifty50_change_pct": change_pct,
            "nifty50_direction": "up" if change_pct > 0 else "down",
        }
    except Exception as e:
        print(f"[Nifty] Snapshot error: {e}")
        return {}
