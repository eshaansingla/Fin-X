# backend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os, logging
import time

logging.basicConfig(level=logging.INFO)
logger    = logging.getLogger('[Scheduler]')
scheduler = BackgroundScheduler()

# All 50 movers symbols kept hot in the quote cache during market hours.
# Matches _SYMBOLS in routers/market.py — update both together.
_LIVE_SYMBOLS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'TATAMOTORS', 'WIPRO', 'BAJFINANCE', 'SUNPHARMA', 'ITC',
    'SBIN', 'ADANIENT', 'MARUTI', 'BHARTIARTL', 'AXISBANK',
    'KOTAKBANK', 'LT', 'HCLTECH', 'TITAN', 'ONGC',
    'NTPC', 'JSWSTEEL', 'TATASTEEL', 'DRREDDY', 'CIPLA',
    'EICHERMOT', 'HEROMOTOCO', 'BPCL', 'HINDALCO', 'COALINDIA',
    'ULTRACEMCO', 'TECHM', 'BAJAJFINSV', 'ASIANPAINT', 'NESTLEIND',
    'POWERGRID', 'DIVISLAB', 'GRASIM', 'INDUSINDBK', 'TATACONSUM',
    'BRITANNIA', 'APOLLOHOSP', 'SHREECEM', 'SBILIFE', 'HDFCLIFE',
    'PIDILITIND', 'DABUR', 'BERGEPAINT', 'MARICO', 'MUTHOOTFIN',
]


def run_radar_job():
    """
    The Opportunity Radar core loop — runs every RADAR_INTERVAL_HOURS (default 1h).
    Fetches NSE deals → saves → generates AI signals for unsignalled deals.
    Max 10 signals per run. Each deal wrapped in its own try/except.
    """
    logger.info('Radar job started')
    try:
        from services.nse_fetcher import fetch_bulk_deals, fetch_block_deals, save_bulk_deals_to_db
        from services.indicators import get_stock_data
        from services.gpt import explain_signal
        from database import db_fetchall, db_execute

        deals     = fetch_bulk_deals() + fetch_block_deals()
        logger.info(f'Fetched {len(deals)} deals from NSE')

        new_count = save_bulk_deals_to_db(deals)
        logger.info(f'Saved {new_count} new deals to DB')

        if new_count == 0:
            logger.info('No new deals — skipping AI processing')
            return

        unsignalled = db_fetchall(
            '''SELECT bd.* FROM bulk_deals bd
               LEFT JOIN signals s ON s.deal_id = bd.id
               WHERE s.id IS NULL
               ORDER BY bd.quantity DESC
               LIMIT 10'''
        )

        for deal in unsignalled:
            try:
                stock = get_stock_data(deal['symbol'])
                if 'error' in stock:
                    logger.warning(f"No price data for {deal['symbol']} — skipping")
                    continue

                signal = explain_signal(deal, stock)

                db_execute(
                    '''INSERT INTO signals
                       (deal_id, symbol, explanation, signal_type, risk_level,
                        confidence, key_observation, disclaimer)
                       VALUES (?,?,?,?,?,?,?,?)''',
                    (
                        deal['id'],
                        deal['symbol'],
                        signal.get('explanation',     ''),
                        signal.get('signal_type',     'neutral'),
                        signal.get('risk_level',      'medium'),
                        signal.get('confidence',       50),
                        signal.get('key_observation', ''),
                        signal.get('disclaimer', 'For educational purposes only. Not SEBI-registered investment advice.'),
                    )
                )
                logger.info(f"Signal created: {deal['symbol']} — {signal.get('signal_type')}")
                time.sleep(2.5)

            except Exception as e:
                logger.error(f"Error processing deal {deal.get('id')}: {e}")
                continue

    except Exception as e:
        logger.error(f'Radar job failed: {e}')


def prefetch_popular_stocks():
    """
    Runs at startup (30s delay) to pre-warm card cache for popular NSE stocks.
    Cache TTL: 1 hour (vs 15 min for user-triggered refreshes).
    """
    from services.indicators import POPULAR_STOCKS, get_stock_data
    from services.news_fetcher import get_stock_news
    from services.gpt import generate_signal_card
    from database import db_execute
    from datetime import datetime, timedelta
    import json

    logger.info('Pre-fetching signal cards for popular stocks...')
    for ns_symbol in POPULAR_STOCKS[:10]:
        symbol = ns_symbol.replace('.NS', '')
        try:
            stock = get_stock_data(symbol)
            if 'error' in stock:
                continue
            news = get_stock_news(symbol)
            card = generate_signal_card(symbol, stock, news)
            dates  = stock.get('dates_30d', [])
            prices = stock.get('price_30d', [])
            trends = {
                '1m': [{'time': d, 'price': p} for d, p in zip(dates, prices)],
                '1w': [{'time': d, 'price': p} for d, p in zip(dates[-7:],  prices[-7:])],
                '1d': [{'time': d, 'price': p} for d, p in zip(dates[-5:],  prices[-5:])],
            }
            card.update({
                'price_30d':     prices,
                'dates_30d':     dates,
                'current_price': stock.get('current_price'),
                'change_pct':    stock.get('change_pct'),
                'rsi':           stock.get('rsi'),
                'ema_signal':    stock.get('ema_signal'),
                'rsi_zone':      stock.get('rsi_zone'),
                'symbol':        symbol,
                'trends':        trends,
                'news': [
                    {'headline': n.get('headline', ''), 'source': n.get('source', ''), 'url': n.get('url', '')}
                    for n in news[:4]
                ],
            })
            expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            db_execute(
                'INSERT OR REPLACE INTO card_cache (symbol, card_json, expires_at) VALUES (?,?,?)',
                (symbol, json.dumps(card), expires)
            )
            logger.info(f'Pre-fetched card: {symbol}')
            time.sleep(3)
        except Exception as e:
            logger.error(f'Pre-fetch failed for {symbol}: {e}')


def refresh_live_quotes():
    """
    Pre-warm the in-memory quote cache for all 50 movers symbols.
    Runs every 10 seconds via APScheduler. No-op outside market hours.
    Parallel fetch (ThreadPoolExecutor in get_bulk_quotes) keeps this fast.
    max_instances=1 prevents overlapping runs if NSE is slow.
    Also warms the intraday cache so /market/live and /market/price
    respond instantly (< 10 ms) for all popular symbols.
    """
    try:
        from services.market_hours import is_market_open
        if not is_market_open():
            return   # no-op outside market hours
        from services.nse_service import get_bulk_quotes, get_historical
        from concurrent.futures import ThreadPoolExecutor

        # Warm quote cache (parallel across all 50 symbols)
        get_bulk_quotes(_LIVE_SYMBOLS)

        # Warm intraday cache for the 10 most popular symbols (background)
        def _warm_intraday(sym):
            try:
                get_historical(sym, '1d')
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=5) as ex:
            for sym in _LIVE_SYMBOLS[:10]:
                ex.submit(_warm_intraday, sym)

        logger.debug(f'[LiveQuotes] Cache warmed for {len(_LIVE_SYMBOLS)} symbols')
    except Exception as e:
        logger.warning(f'[LiveQuotes] Refresh error: {e}')


def refresh_movers_cache():
    """
    Pre-warm the market movers in-memory cache so the /market/movers
    endpoint always responds from cache (< 5 ms) during market hours.
    Runs every 8 seconds — just inside the 8-second quote TTL window.
    """
    try:
        from services.market_hours import is_market_open
        if not is_market_open():
            return
        # Trigger the movers endpoint logic directly to refresh its cache
        from routers.market import _SYMBOLS, _cache
        from services.nse_service import get_bulk_quotes
        from services.search_service import NSE_STOCKS
        import time as _time

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
            return

        by_pct   = sorted(stocks, key=lambda x: x['change_pct'], reverse=True)
        by_price = sorted(stocks, key=lambda x: float(x['price']))

        gainers_pos = [s for s in by_pct if s['change_pct'] > 0]
        gainers = gainers_pos[:10]
        if len(gainers) < 10:
            gainers += [s for s in by_pct if s['change_pct'] <= 0][:10 - len(gainers)]

        losers_neg = [s for s in reversed(by_pct) if s['change_pct'] < 0]
        losers = losers_neg[:10]
        if len(losers) < 10:
            losers += [s for s in by_pct if s['change_pct'] >= 0][-10 + len(losers):]

        _cache['movers'] = {
            'data': {
                'gainers':   gainers,
                'losers':    losers,
                'cheapest':  by_price[:10],
                'expensive': list(reversed(by_price))[:10],
                'total':     len(stocks),
            },
            'ts': _time.time(),
        }
        logger.debug(f'[MoversCache] Pre-warmed — {len(stocks)} stocks')
    except Exception as e:
        logger.warning(f'[MoversCache] Refresh error: {e}')


def start_scheduler():
    """
    Configures and starts the APScheduler background scheduler.
    Guard against duplicate starts (e.g. uvicorn --reload).
    """
    if scheduler.running:
        logger.info('Scheduler already running — skipping start')
        return

    interval_hours = int(os.getenv('RADAR_INTERVAL_HOURS', '1'))

    scheduler.add_job(
        run_radar_job,
        trigger          = IntervalTrigger(hours=interval_hours),
        id               = 'opportunity_radar',
        max_instances    = 1,
        replace_existing = True,
    )

    import datetime as dt

    scheduler.add_job(
        run_radar_job,
        trigger          = 'date',
        run_date         = dt.datetime.now() + dt.timedelta(seconds=10),
        id               = 'radar_startup',
        replace_existing = True,
    )

    scheduler.add_job(
        prefetch_popular_stocks,
        trigger          = 'date',
        run_date         = dt.datetime.now() + dt.timedelta(seconds=30),
        id               = 'prefetch_startup',
        replace_existing = True,
    )

    # Live quote cache warmer — all 50 movers symbols, every 10 s
    scheduler.add_job(
        refresh_live_quotes,
        trigger          = IntervalTrigger(seconds=10),
        id               = 'live_quote_refresh',
        max_instances    = 1,
        replace_existing = True,
    )

    # Movers cache pre-warmer — every 8 s during market hours
    # Keeps /market/movers always served from in-memory cache (< 5 ms)
    scheduler.add_job(
        refresh_movers_cache,
        trigger          = IntervalTrigger(seconds=8),
        id               = 'movers_cache_refresh',
        max_instances    = 1,
        replace_existing = True,
    )

    scheduler.start()
    logger.info(f'Scheduler started — Opportunity Radar runs every {interval_hours}h')
