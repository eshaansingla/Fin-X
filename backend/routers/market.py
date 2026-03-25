# backend/routers/market.py
"""
Market endpoints:
  GET /market/status           — IST market open/close flag
  GET /market/price/{symbol}   — instant price-only (no intraday); < 50 ms from cache
  GET /market/live/{symbol}    — price + intraday chart (parallel fetch, cached)
  GET /market/movers           — top gainers, losers, cheapest, most expensive
"""
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# ── In-memory movers cache ────────────────────────────────────
_cache: dict = {}
_CACHE_TTL_OPEN   =  5   # seconds — during market hours (aggressive refresh)
_CACHE_TTL_CLOSED = 120  # seconds — after market close (stale is fine)

# Broad NSE stock pool — 50 liquid stocks across sectors.
# Large enough to always fill 10 gainers + 10 losers + cheapest + expensive.
_SYMBOLS = [
    # Nifty 50 heavyweights
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'TATAMOTORS', 'WIPRO', 'BAJFINANCE', 'SUNPHARMA', 'ITC',
    'SBIN', 'ADANIENT', 'MARUTI', 'BHARTIARTL', 'AXISBANK',
    'KOTAKBANK', 'LT', 'HCLTECH', 'TITAN', 'ONGC',
    'NTPC', 'JSWSTEEL', 'TATASTEEL', 'DRREDDY', 'CIPLA',
    'EICHERMOT', 'HEROMOTOCO', 'BPCL', 'HINDALCO', 'COALINDIA',
    # Additional Nifty 50 / large-cap
    'ULTRACEMCO', 'TECHM', 'BAJAJFINSV', 'ASIANPAINT', 'NESTLEIND',
    'POWERGRID', 'DIVISLAB', 'GRASIM', 'INDUSINDBK', 'TATACONSUM',
    'BRITANNIA', 'APOLLOHOSP', 'SHREECEM', 'SBILIFE', 'HDFCLIFE',
    'PIDILITIND', 'DABUR', 'BERGEPAINT', 'MARICO', 'MUTHOOTFIN',
]


# ── /market/status ────────────────────────────────────────────
@router.get('/market/status')
def get_market_status():
    """Return current IST time and whether the NSE market is open."""
    try:
        from services.market_hours import market_status
        return {'success': True, 'data': market_status(), 'error': None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )


# ── /market/price/{symbol} ────────────────────────────────────
@router.get('/market/price/{symbol}')
def get_quick_price(symbol: str):
    """
    Ultra-fast price-only endpoint. Returns price + OHLCV from cache.
    No intraday chart — use this for the instant first-render price tile.
    Typically < 50 ms when cache is warm (scheduler pre-warms 50 symbols).
    """
    try:
        from services.symbol_resolver import normalize_symbol
        from services.nse_service import get_quote
        from services.market_hours import market_status

        symbol = normalize_symbol(symbol)
        if not symbol:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'data': None, 'error': 'Invalid symbol'},
            )

        status = market_status()
        quote  = get_quote(symbol)

        if quote is None:
            return JSONResponse(
                status_code=503,
                content={'success': False, 'data': None, 'error': f'Quote unavailable for {symbol}'},
            )

        return {
            'success': True,
            'data': {
                'symbol':      symbol,
                'price':       quote.get('price'),
                'change':      quote.get('change'),
                'change_pct':  quote.get('percent_change'),
                'open':        quote.get('open'),
                'high':        quote.get('high'),
                'low':         quote.get('low'),
                'volume':      quote.get('volume'),
                'prev_close':  quote.get('prev_close'),
                'market_open': status['is_open'],
                'time_ist':    status['time_ist'],
            },
            'error': None,
        }

    except Exception as e:
        print(f'[QuickPrice] Error for {symbol}: {e}')
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )


# ── /market/live/{symbol} ─────────────────────────────────────
@router.get('/market/live/{symbol}')
def get_live_quote(symbol: str):
    """
    Real-time price + intraday chart.
    Quote and intraday fetch run in parallel for reduced latency.
    Served from in-memory cache (8 s quote TTL, 5 s intraday TTL when open).
    """
    try:
        from services.symbol_resolver import normalize_symbol
        from services.nse_service import get_quote, get_historical
        from services.market_hours import market_status
        from concurrent.futures import ThreadPoolExecutor

        symbol = normalize_symbol(symbol)
        if not symbol:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'data': None, 'error': 'Invalid symbol'},
            )

        # Parallel: quote + intraday (both are cache-first, so usually < 10 ms)
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_quote    = ex.submit(get_quote,    symbol)
            f_intraday = ex.submit(get_historical, symbol, '1d')
            quote    = f_quote.result(timeout=10)
            intraday = f_intraday.result(timeout=10)

        status = market_status()

        if quote is None:
            return JSONResponse(
                status_code=503,
                content={
                    'success': False,
                    'data':    None,
                    'error':   f'Quote unavailable for {symbol}',
                },
            )

        return {
            'success': True,
            'data': {
                'symbol':      symbol,
                'price':       quote.get('price'),
                'change':      quote.get('change'),
                'change_pct':  quote.get('percent_change'),
                'open':        quote.get('open'),
                'high':        quote.get('high'),
                'low':         quote.get('low'),
                'volume':      quote.get('volume'),
                'prev_close':  quote.get('prev_close'),
                'intraday':    intraday,
                'market_open': status['is_open'],
                'time_ist':    status['time_ist'],
                'date_ist':    status['date_ist'],
            },
            'error': None,
        }

    except Exception as e:
        print(f'[LiveQuote] Error for {symbol}: {e}')
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )


# ── /market/movers ────────────────────────────────────────────
@router.get('/market/movers')
def get_market_movers():
    """
    Returns top gainers, losers, cheapest and most expensive NSE stocks
    from a curated watchlist. Cached for 30 seconds.
    """
    # Dynamic TTL: fast refresh during market hours, slower when closed
    try:
        from services.market_hours import is_market_open
        _ttl = _CACHE_TTL_OPEN if is_market_open() else _CACHE_TTL_CLOSED
    except Exception:
        _ttl = _CACHE_TTL_CLOSED

    # Serve from cache if fresh
    cached = _cache.get('movers')
    if cached and (time.time() - cached['ts']) < _ttl:
        return {'success': True, 'data': cached['data'], 'error': None}

    try:
        from services.nse_service import get_bulk_quotes
        from services.search_service import NSE_STOCKS

        quotes = get_bulk_quotes(_SYMBOLS)
        stocks = []
        for sym, q in quotes.items():
            if not q or q.get('price') is None:
                continue
            pct = q.get('percent_change')
            try:
                pct = float(pct) if pct is not None else 0.0
            except (ValueError, TypeError):
                pct = 0.0
            stocks.append({
                'symbol':     sym,
                'name':       NSE_STOCKS.get(sym, sym),
                'price':      q['price'],
                'change_pct': round(pct, 2),
                'change':     q.get('change', 0),
            })

        if not stocks:
            return {
                'success': True,
                'data': {'gainers': [], 'losers': [], 'cheapest': [], 'expensive': [], 'total': 0},
                'error': None,
            }

        by_pct   = sorted(stocks, key=lambda x: x['change_pct'], reverse=True)
        by_price = sorted(stocks, key=lambda x: float(x['price']))

        # Always fill all 10 slots:
        # Gainers = top 10 by % change (positive first, fill rest if needed)
        # Losers  = bottom 10 by % change (negative first, fill rest if needed)
        gainers_pos = [s for s in by_pct if s['change_pct'] > 0]
        gainers = gainers_pos[:10]
        if len(gainers) < 10:
            gainers += [s for s in by_pct if s['change_pct'] <= 0][:10 - len(gainers)]

        losers_neg = [s for s in reversed(by_pct) if s['change_pct'] < 0]
        losers = losers_neg[:10]
        if len(losers) < 10:
            losers += [s for s in by_pct if s['change_pct'] >= 0][-10 + len(losers):]

        data = {
            'gainers':   gainers,
            'losers':    losers,
            'cheapest':  by_price[:10],
            'expensive': list(reversed(by_price))[:10],
            'total':     len(stocks),
        }

        _cache['movers'] = {'data': data, 'ts': time.time()}
        return {'success': True, 'data': data, 'error': None}

    except Exception as e:
        print(f'[Movers] Error: {e}')
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )
