# FALCON-X Dev Guide

## First-Time Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `backend/.env` with:
```
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
NEWS_API_KEY=your_key
DATABASE_URL=data/falcon.db
CORS_ORIGINS=http://localhost:5173
RADAR_INTERVAL_HOURS=1
```

### Frontend
```bash
cd frontend
npm install
```

---

## Running the Project

**Always run backend from the `backend/` directory** (so the DB path `data/falcon.db` resolves correctly).

### Terminal 1 — Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Terminal 2 — Frontend
```bash
cd frontend
npm run dev
```

App runs at: **http://localhost:5173**
API docs at: **http://localhost:8001/docs**

> **Port note:** The frontend reads `VITE_API_URL` from `frontend/.env.local` (gitignored).
> Current value: `http://localhost:8001/api`. If you change the backend port, update this file.

---

## Seeding the Radar (first run)

If the Opportunity Radar shows 0 signals after startup, open a **third terminal** and run:

```bash
cd backend
python -c "
import json, time, sys
sys.path.insert(0, '.')
from database import db_fetchall, db_execute
from datetime import date as _date
from services.gpt import explain_signal

existing = db_fetchall('SELECT id FROM signals LIMIT 1')
if existing:
    print('Signals already exist')
    exit()

cached_cards = db_fetchall('SELECT symbol, card_json FROM card_cache ORDER BY created_at DESC LIMIT 8')
print(f'Seeding from {len(cached_cards)} cached cards...')
generated = 0
for row in cached_cards:
    sym = row['symbol']
    try:
        card = json.loads(row['card_json'])
        price = card.get('current_price') or 0
        if not price:
            continue
        stock = {'symbol': sym, 'current_price': price, 'change_pct': card.get('change_pct', 0),
                 'rsi': card.get('rsi'), 'ema_signal': card.get('ema_signal', 'neutral'),
                 'rsi_zone': card.get('rsi_zone', 'neutral'), 'volume': card.get('volume', 0)}
        deal_id = db_execute(
            'INSERT INTO bulk_deals (symbol, client_name, deal_type, quantity, price, deal_date) VALUES (?,?,?,?,?,?)',
            (sym, 'Market Intelligence', 'B', 0, float(price), _date.today().isoformat())
        )
        deal = {'id': deal_id, 'symbol': sym, 'deal_type': 'B', 'quantity': 0,
                'price': price, 'deal_date': _date.today().isoformat(), 'client_name': 'Market Intelligence'}
        sig = explain_signal(deal, stock)
        db_execute(
            'INSERT INTO signals (deal_id, symbol, explanation, signal_type, risk_level, confidence, key_observation, disclaimer) VALUES (?,?,?,?,?,?,?,?)',
            (deal_id, sym, sig.get('explanation',''), sig.get('signal_type','neutral'),
             sig.get('risk_level','medium'), sig.get('confidence',50),
             sig.get('key_observation',''), sig.get('disclaimer','For educational purposes only.'))
        )
        generated += 1
        print(f'  {sym}: {sig.get(\"signal_type\")} / {sig.get(\"risk_level\")}')
        time.sleep(2)
    except Exception as e:
        print(f'  ERROR {sym}: {e}')
print(f'Done: {generated} signals')
"
```

> **Note:** Wait ~30 seconds after starting the backend before running the seed script.
> The pre-fetch job runs at startup (30s delay) and populates the card cache needed for seeding.

---

## Stopping Servers

```bash
# Windows — find and kill by port
netstat -ano | findstr :8000
netstat -ano | findstr :5173
taskkill /PID <pid> /F
```

Or just close the terminal windows.

---

## Key Notes

- **Gemini free tier**: 20 requests/day. After exhaustion, signals fall back to neutral/medium until the next day.
- **NSE bulk deals**: Only published on trading days (Mon–Fri, market hours). On weekends/holidays the radar uses the 7-day lookback, then seeds from popular stocks.
- **DB location**: Always at `backend/data/falcon.db` — never run uvicorn from the project root.
