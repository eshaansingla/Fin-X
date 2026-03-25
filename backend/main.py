# backend/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from database import init_db
from routers import chat, signals, cards, health
from routers import search as search_router
from routers import market as market_router
from routers import inshorts as inshorts_router
from scheduler import start_scheduler

load_dotenv(override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    start_scheduler()
    print('[FALCON-X] Server ready — API docs at /docs')
    yield
    # Shutdown (nothing needed — daemon thread dies with process)

app = FastAPI(
    title       = 'FALCON-X API',
    description = 'NSE Opportunity Radar & AI Market Intelligence for Indian Investors',
    version     = '1.0.0',
    docs_url    = '/docs',
    redoc_url   = '/redoc',
    lifespan    = lifespan,
)

# CORS — read allowed origins from env, never use '*' with credentials
_raw_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173')
origins = [o.strip() for o in _raw_origins.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)

# Mount all routers under /api prefix
app.include_router(health.router,        prefix='/api', tags=['Health'])
app.include_router(signals.router,       prefix='/api', tags=['Signals'])
app.include_router(cards.router,         prefix='/api', tags=['Cards'])
app.include_router(chat.router,          prefix='/api', tags=['Chat'])
app.include_router(search_router.router, prefix='/api', tags=['Search'])
app.include_router(market_router.router, prefix='/api', tags=['Market'])
app.include_router(inshorts_router.router, prefix='/api', tags=['Inshorts'])

# Analytics + Audio endpoints
try:
    from services.advanced_analytics import get_pattern_success_rate, get_institutional_clusters, analyze_management_tone

    @app.get('/api/analytics/success-rate/{symbol}', tags=['Analytics'])
    def api_success_rate(symbol: str, signal_type: str = 'EMA Crossover'):
        return get_pattern_success_rate(symbol, signal_type)

    @app.get('/api/analytics/clusters', tags=['Analytics'])
    def api_clusters():
        return get_institutional_clusters()

    @app.get('/api/analytics/tone-shift/{symbol}', tags=['Analytics'])
    def api_tone_shift(symbol: str):
        return analyze_management_tone(symbol)

except Exception as e:
    print(f'[WARN] Analytics endpoints unavailable: {e}')

try:
    from services.audio_briefing import generate_market_minutes

    @app.get('/api/audio/market-minutes', tags=['Audio'])
    def api_market_minutes():
        return generate_market_minutes()

except Exception as e:
    print(f'[WARN] Audio endpoints unavailable: {e}')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
