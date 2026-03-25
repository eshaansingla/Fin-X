# backend/routers/market.py
"""
Market movers endpoint — top gainers, losers, cheapest, most expensive.
Uses a 30-second in-memory cache to avoid hammering NSE on every request.
"""
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# ── In-memory cache ───────────────────────────────────────────
_cache: dict = {}
_CACHE_TTL   = 30  # seconds

# Curated set of liquid NSE stocks for movers
_SYMBOLS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'TATAMOTORS', 'WIPRO', 'BAJFINANCE', 'SUNPHARMA', 'ITC',
    'SBIN', 'ADANIENT', 'MARUTI', 'BHARTIARTL', 'AXISBANK',
    'KOTAKBANK', 'LT', 'HCLTECH', 'TITAN', 'ONGC',
    'NTPC', 'JSWSTEEL', 'TATASTEEL', 'DRREDDY', 'CIPLA',
    'EICHERMOT', 'HEROMOTOCO', 'BPCL', 'HINDALCO', 'COALINDIA',
]


@router.get('/market/movers')
def get_market_movers():
    """
    Returns top gainers, losers, cheapest and most expensive NSE stocks
    from a curated watchlist. Cached for 30 seconds.
    """
    # Serve from cache if fresh
    cached = _cache.get('movers')
    if cached and (time.time() - cached['ts']) < _CACHE_TTL:
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

        data = {
            'gainers':   [s for s in by_pct if s['change_pct'] > 0][:6],
            'losers':    [s for s in reversed(by_pct) if s['change_pct'] < 0][:6],
            'cheapest':  by_price[:6],
            'expensive': list(reversed(by_price))[:6],
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
