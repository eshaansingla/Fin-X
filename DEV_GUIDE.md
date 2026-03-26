# FIN-X Dev Guide

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
DATABASE_URL=data/finx.db
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

**Always run backend from the `backend/` directory** (so the DB path `data/finx.db` resolves correctly).

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

## First-run Warmup (auto-seeding)

FIN-X automatically warms up on startup:

1. Pre-fetches AI insight cards for popular stocks.
2. Attempts to fetch the last 7 days of NSE bulk/block deals.
3. If signals are still empty (e.g., weekend/holiday or NSE API issues), it generates initial radar signals from the top popular stocks so the UI is never blank.

In the frontend, you should see a banner: `FIN-X is warming up...` with progress updates. After warmup completes, the Opportunity Radar should show signals automatically.

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
- **DB location**: Always at `backend/data/finx.db` — never run uvicorn from the project root.
