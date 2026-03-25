# backend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os, logging
import time

logging.basicConfig(level=logging.INFO)
logger    = logging.getLogger('[Scheduler]')
scheduler = BackgroundScheduler()


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

    scheduler.start()
    logger.info(f'Scheduler started — Opportunity Radar runs every {interval_hours}h')
