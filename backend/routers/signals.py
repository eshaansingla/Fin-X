# backend/routers/signals.py
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from database import db_fetchall, db_fetchone, db_execute
from services.nse_fetcher import fetch_bulk_deals, fetch_block_deals, fetch_bulk_deals_lookback, save_bulk_deals_to_db
from services.indicators import get_stock_data
from services.gpt import explain_signal
from services.nse_service import get_bulk_quotes
from services.symbol_resolver import normalize_symbol
import time

router = APIRouter()


@router.get('/signals')
def get_signals(
    limit:      int = Query(20, ge=1, le=100),
    risk_level: str = Query(None, pattern='^(high|medium|low)$'),
    symbol:     str = Query(None, max_length=10),
):
    """Returns latest AI-explained signals from the Opportunity Radar."""
    try:
        query      = 'SELECT * FROM signals'
        params     = []
        conditions = []

        if risk_level:
            conditions.append('risk_level = ?')
            params.append(risk_level)
        if symbol:
            conditions.append('symbol = ?')
            params.append(normalize_symbol(symbol)[:10])

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        signals = db_fetchall(query, tuple(params))

        # Enrich with live NSE price data
        if signals:
            unique_symbols = list({s['symbol'] for s in signals if s.get('symbol')})
            try:
                quotes = get_bulk_quotes(unique_symbols)
                for sig in signals:
                    q = quotes.get(sig.get('symbol'))
                    sig['price']          = q['price']          if q else None
                    sig['percent_change'] = q['percent_change'] if q else None
            except Exception as e:
                print(f'[Signals] Price enrichment failed: {e}')

        # Replace stale "temporarily unavailable" explanations with rule-based analysis
        _STALE = 'Signal analysis temporarily unavailable.'
        stale_ids = [
            s['deal_id'] for s in signals
            if s.get('explanation') == _STALE and s.get('deal_id')
        ]
        if stale_ids:
            try:
                from services.gpt import _rule_based_signal_explanation
                ph = ','.join('?' * len(stale_ids))
                deals_rows = db_fetchall(
                    f'SELECT * FROM bulk_deals WHERE id IN ({ph})',
                    tuple(stale_ids),
                )
                deals_map = {d['id']: d for d in deals_rows}
                for sig in signals:
                    if sig.get('explanation') == _STALE and sig.get('deal_id') in deals_map:
                        deal = deals_map[sig['deal_id']]
                        stock = {
                            'symbol':        sig.get('symbol', ''),
                            'current_price': sig.get('price'),
                            'change_pct':    sig.get('percent_change') or 0,
                            'rsi':           None,
                            'ema_signal':    'neutral',
                            'high_52w':      None,
                            'low_52w':       None,
                        }
                        rb = _rule_based_signal_explanation(deal, stock)
                        sig.update({
                            'explanation':     rb['explanation'],
                            'signal_type':     rb.get('signal_type',     sig.get('signal_type', 'neutral')),
                            'risk_level':      rb.get('risk_level',      sig.get('risk_level',  'medium')),
                            'confidence':      rb.get('confidence',      sig.get('confidence',   50)),
                            'key_observation': rb.get('key_observation', sig.get('key_observation', '')),
                            'ai_provider':     rb.get('ai_provider',     sig.get('ai_provider', 'rule_based')),
                        })
            except Exception as e:
                print(f'[Signals] Stale explanation fix failed: {e}')

        return {'success': True, 'data': {'signals': signals}, 'error': None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )


@router.get('/signals/{signal_id}')
def get_signal_by_id(signal_id: int):
    """Returns a single signal by its database ID."""
    try:
        row = db_fetchone('SELECT * FROM signals WHERE id=?', (signal_id,))
        if not row:
            return JSONResponse(
                status_code=404,
                content={'success': False, 'data': None, 'error': 'Signal not found'},
            )
        return {'success': True, 'data': row, 'error': None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )


@router.post('/signals/refresh')
def manual_refresh():
    """
    Manually triggers the Opportunity Radar pipeline.
    Fetches NSE deals → saves → generates AI signals.
    Returns counts: new_deals saved, signals_generated.
    """
    try:
        deals = fetch_bulk_deals() + fetch_block_deals()
        # If today has no deals (market closed / not yet published), look back up to 7 days
        if not deals:
            print('[Refresh] Today has no deals — looking back up to 7 days')
            deals = fetch_bulk_deals_lookback(7)
        saved = save_bulk_deals_to_db(deals)

        unsignalled = db_fetchall(
            '''SELECT bd.* FROM bulk_deals bd
               LEFT JOIN signals s ON s.deal_id = bd.id
               WHERE s.id IS NULL
               ORDER BY bd.fetched_at DESC LIMIT 10'''
        )

        generated = 0
        for deal in unsignalled:
            try:
                stock = get_stock_data(deal['symbol'])
                if 'error' in stock:
                    print(f"[Refresh] No price data for {deal['symbol']} — skipping")
                    continue
                signal = explain_signal(deal, stock)
                db_execute(
                    '''INSERT INTO signals
                       (deal_id, symbol, explanation, signal_type, risk_level,
                        confidence, key_observation, disclaimer, ai_provider)
                       VALUES (?,?,?,?,?,?,?,?,?)''',
                    (
                        deal['id'],
                        deal['symbol'],
                        signal.get('explanation',     ''),
                        signal.get('signal_type',     'neutral'),
                        signal.get('risk_level',      'medium'),
                        signal.get('confidence',       50),
                        signal.get('key_observation', ''),
                        signal.get('disclaimer', 'For educational purposes only. Not financial advice.'),
                        signal.get('ai_provider'),
                    )
                )
                generated += 1
                time.sleep(2.5)
            except Exception as e:
                print(f"[Refresh] Error processing deal {deal.get('id')}: {e}")
                continue

        return {
            'success': True,
            'data': {'new_deals': saved, 'signals_generated': generated},
            'error': None,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )


@router.get('/bulk-deals')
def get_bulk_deals(limit: int = Query(20, ge=1, le=100)):
    """Returns raw bulk deal data without AI explanation."""
    try:
        deals = db_fetchall(
            'SELECT * FROM bulk_deals ORDER BY fetched_at DESC LIMIT ?',
            (limit,)
        )
        return {'success': True, 'data': {'deals': deals}, 'error': None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )
