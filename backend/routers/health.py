# backend/routers/health.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
from database import db_fetchone

router = APIRouter()


@router.get('/health')
def health_check():
    """
    Keep-alive endpoint. Returns status and signal count for uptime monitoring.
    """
    try:
        signal_count = db_fetchone('SELECT COUNT(*) as cnt FROM signals')
        return {
            'success': True,
            'data': {
                'status':        'ok',
                'timestamp':     datetime.utcnow().isoformat(),
                'signals_in_db': signal_count['cnt'] if signal_count else 0,
            },
            'error': None,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'data': None, 'error': str(e)},
        )
