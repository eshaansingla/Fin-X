<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,40:1a2744,100:6d28d9&height=220&section=header&text=FIN-X&fontSize=90&fontColor=ffffff&fontAlignY=38&desc=India%27s%20AI-Powered%20NSE%20Market%20Intelligence%20Platform&descAlignY=60&descSize=19&descColor=a78bfa&animation=fadeIn" width="100%"/>

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq_Llama--3.3--70b--versatile-AI_Primary-8E75B2?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
[![GPT-4o mini](https://img.shields.io/badge/GPT--4o_mini-AI_Fallback-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![Tests](https://img.shields.io/badge/Tests-22_passing-22c55e?style=for-the-badge&logo=pytest&logoColor=white)](#-testing)
[![Auth](https://img.shields.io/badge/Auth-JWT_+_Google_OAuth-F59E0B?style=for-the-badge&logo=jsonwebtokens&logoColor=black)](https://jwt.io)
[![ET Hackathon](https://img.shields.io/badge/ET_Hackathon-AI_Fintech_Track-FF6B00?style=for-the-badge)](https://economictimes.indiatimes.com)

<br/>

### *"90 million Indians have demat accounts.*
### *Almost none can read what the smart money is actually doing."*

<br/>

**FIN-X is the explanation layer.**

Real-time NSE institutional bulk & block deal tracking, run through a 3-tier AI stack,
surfacing what it all *means* — in plain language, before the broader market reacts.

<br/>

[**Screenshots**](#-screenshots) · [**Architecture**](#-architecture) · [**Quick Start**](#-quick-start) · [**API Docs**](#-api-reference) · [**Security**](#-security)

<br/>
</div>

---

## 📸 Screenshots

### Landing Page & Auth
> Production-grade dark UI with Google OAuth 2.0 and email/password login. Real stats: 500+ NSE stocks, 3-tier AI fallback, <50ms price latency, live WebSocket feed.

<img width="1440" height="778" alt="Screenshot 2026-03-28 at 2 54 26 PM" src="https://github.com/user-attachments/assets/e658ee95-a6d0-4f81-b7c5-b024d6c95342" />


---

### Opportunity Radar — Live NSE Signal Feed
> Real-time bulk & block deal scanner with AI-generated explanations, risk levels, and institutional pattern detection. Filterable by High / Medium / Low risk. Expandable signal cards with key observations and technical context.

<img src="screenshots/radar-dark.png" width="100%" alt="Radar Dark"/>

---

### FinPulse Intelligence
> Finance news with AI sentiment classification (POSITIVE / NEUTRAL / NEGATIVE), keyword extraction, and direct NSE symbol mapping. News linked to affected stocks — not just headlines.

<img src="screenshots/FinPulse.png" width="100%" alt="FinPulse"/>

---

### NSE Signal Card — Per-Stock Deep Analysis
> Live price chart across 5 timeframes (1D / 1W / 1M / 1Y / 5Y / ALL), RSI, EMA-20/50, MACD, Bollinger Bands — with full AI technical snapshot. Search any NSE ticker.

<img src="screenshots/signal-card-dark.png" width="100%" alt="Signal Card Dark"/>

---

### AI Market Chat — Context-Injected, Never Hallucinated
> Every answer grounded in live NSE prices, today's bulk deals, Nifty 50 snapshot, and real-time news sentiment. Built-in prompt suggestions for common queries.

<img src="screenshots/chat.png" width="100%" alt="Market Chat"/>

---

### Light Mode — Full Theme Support
> Complete dark/light toggle across all pages. Same live data, two aesthetics.

<img src="screenshots/signal-card-light.png" width="100%" alt="Signal Card Light"/>

---

## 🧠 The Problem

Every day, institutions — mutual funds, FIIs, proprietary trading desks — move thousands of crores in NSE bulk and block deals. This data is technically public. But it's buried in raw CSVs, stripped of context, and gone before most retail investors even see it.

The result: a two-tier market where institutions act on signals retail investors can't decode.

**FIN-X closes that gap. Not with predictions — with *explanations*.**

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 🔭 Opportunity Radar
Real-time NSE bulk & block deal scanner. Detects institutional accumulation and distribution patterns with AI-generated signal explanations, risk levels (High / Medium / Low), and confidence scores. Refreshed hourly via APScheduler. Filterable. Expandable signal cards with key observations.

</td>
<td width="50%" valign="top">

### 📊 AI Signal Cards
Per-stock deep analysis on demand: live price chart across 5 timeframes, full technicals (EMA-20/50, RSI, MACD, Bollinger Bands), AI sentiment score, news impact rating, pattern success rate, institutional cluster detection, and management tone shift analysis.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 💬 AI Market Chat
Ask anything about the Indian market. Every answer is grounded in live NSE prices, today's Nifty 50 snapshot, active radar signals, and real-time news sentiment — context-injected on every query. Prompt suggestions built in.

</td>
<td width="50%" valign="top">

### 📰 FinPulse Intelligence
Finance news with AI sentiment classification (POSITIVE / NEUTRAL / NEGATIVE), keyword extraction, and direct NSE symbol mapping to affected stocks. News is never just a headline.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🔐 Production Auth System
Email + password with Brevo transactional verification, Google OAuth 2.0, JWT access + refresh tokens with silent rotation, bcrypt 12-round hashing, per-IP rate limiting, and 5 security headers on every response.

</td>
<td width="50%" valign="top">

### 🔍 Instant Smart Search
Debounced 7-step fuzzy NSE search across 100+ symbols with dropdown suggestions and keyboard navigation. Two-phase loading: live price appears in &lt;200 ms from scheduler-warmed cache, full AI card follows seamlessly. Re-visiting a stock within 5 min is instant — no network call.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📡 Live Market Feed
Real-time price streaming per symbol via WebSocket (`/market/ws/{symbol}`). Market movers (gainers, losers, cheapest, most expensive) polled every 5 s during market hours. IST open/closed awareness with adaptive polling rates across all components.

</td>
</tr>
</table>

---

## 🏗 Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                           FIN-X                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   ┌──────────────────  REACT 18 FRONTEND  ──────────────────┐    ║
║   │                                                         │    ║
║   │  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐   │    ║
║   │  │  Radar   │  │  Signal  │  │  Chat   │  │FinPulse │   │    ║
║   │  │   Page   │  │  Cards   │  │   AI    │  │  Page   │   │    ║
║   │  └────┬─────┘  └────┬─────┘  └────┬────┘  └────┬────┘   │    ║
║   │       └─────────────┴─────────────┴─────────────┘       │    ║
║   │             Axios + JWT Bearer + Silent Refresh         │    ║
║   │             AuthContext · ThemeContext (dark/light)     │    ║
║   └────────────────────────┬────────────────────────────────┘    ║
║                            │ HTTP / WebSocket                    ║
║   ┌────────────────────────┴─────────────────────────────────┐   ║
║   │                   FASTAPI BACKEND                        │   ║
║   │                                                          │   ║
║   │  /api/v2/auth/*   ──  JWT + Google OAuth 2.0             │   ║
║   │  /api/signals     ──  NSE Radar Engine                   │   ║
║   │  /api/card/*      ──  AI Signal Card Generator           │   ║
║   │  /api/chat        ──  Grounded Market Chat               │   ║
║   │  /api/market/*    ──  Live Prices + WebSocket Feed       │   ║
║   │  /api/finpulse    ──  News Intelligence                  │   ║
║   │                                                          │   ║
║   │  ┌────────────────────────────────────────────────────┐  │   ║
║   │  │                3-TIER AI STACK                     │  │   ║
║   │  │                                                    │  │   ║
║   │  │  Tier 1  Groq Llama-3.3-70b-versatile  ←  Primary  │  │   ║
║   │  │             ↓ (on quota / error)                   │  │   ║
║   │  │  Tier 2  GPT-4o mini            ←  Fallback        │  │   ║
║   │  │             ↓ (on quota / error)                   │  │   ║
║   │  │  Tier 3  Rule Engine            ←  Always-on       │  │   ║
║   │  └────────────────────────────────────────────────────┘  │   ║
║   │                                                          │   ║
║   │  APScheduler: hourly radar · 2s live quotes · 3s movers  │   ║
║   │  SQLite (dev) → PostgreSQL (prod) via SQLAlchemy         │   ║
║   └──────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════╝
```

### Signal Data Flow

```
  NSE Bulk & Block Deals (raw CSV)
            │
            ▼
  ┌──────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
  │   NSE Scraper    │────▶│   3-Tier AI Stack   │────▶│  Signal Store    │
  │  (hourly cron)   │     │  Groq → GPT-4o mini │     │  SQLite / PG     │
  └──────────────────┘     │   → Rule fallback   │     └────────┬─────────┘
                           └─────────────────────┘              │
                                                                ▼
                                              ┌──────────────────────────────-┐
                                              │       API Response Layer      │
                                              │                               │
                                              │  Signal explanation           │
                                              │  Confidence score             │
                                              │  Risk level (H / M / L)       │
                                              │  Institutional cluster        │
                                              │  Live technicals              │
                                              │  News sentiment               │
                                              └───────────────┬───────────────┘
                                                              │
                                         ┌────────────────────┼────────────────────┐
                                         ▼                    ▼                    ▼
                                    React UI             WebSocket            Chat Context
                                    (Radar)              (Live Feed)          (Grounded AI)
```

---

## 🔐 Auth Flow

```
  EMAIL SIGNUP                              GOOGLE OAUTH 2.0
  ─────────────                             ────────────────

  POST /signup                           GET /google/login
    │  bcrypt hash (12 rounds)                │  redirect → Google consent
    │  Brevo verification email               │
    ▼                                         ▼
  GET /verify-email?token=               GET /google/callback
    │  mark is_verified = true               │  fetch email + name
    │  redirect → frontend                   │  upsert user record
    ▼                                        ▼
  POST /login                            issue JWT pair
    │  validate credentials                   │
    │  check is_verified                      │
    ▼                                         ▼
    └──────────────────┬──────────────────────┘
                       │
            { access_token, refresh_token }
                       │
               stored in localStorage
               Bearer header on all requests
                       │
               ┌───────┴────────┐
               │  401 detected  │
               │ silent refresh │  ← old token instantly invalidated
               │ rotate tokens  │  ← version-locked refresh
               └────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend** | React 18, Tailwind CSS, Vite, Recharts | SPA, code-split builds, dark/light theme |
| **Backend** | FastAPI, Uvicorn, APScheduler | Async API, hourly scheduling, WebSockets |
| **Database** | SQLite → PostgreSQL via SQLAlchemy | Auto-switch via `DATABASE_URL` |
| **AI — Primary** | Groq Llama-3.3-70b-versatile | Market analysis, chat grounding |
| **AI — Fallback** | GPT-4o mini | Quota resilience, zero downtime |
| **AI — Hard fallback** | Custom rule engine | Always-on, no API dependency |
| **Auth** | JWT (python-jose), bcrypt, Google OAuth 2.0 | Authlib, silent token rotation |
| **Email** | Brevo SMTP | Transactional verification emails |
| **Market Data** | NSE India, yfinance, custom scrapers | Live prices, bulk/block deals |
| **Testing** | pytest, FastAPI TestClient, StaticPool | 22 tests across 7 suites |
| **Deploy** | Render (backend), Vercel/Netlify (frontend) | `render.yaml` included |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Clone

```bash
git clone https://github.com/eshaansingla/FIN-X.git
cd FIN-X
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env
```

**`.env` reference:**

```env
# ── FIN-X AI Settings ─────────────────────────────────────────────────────────
# Primary: Groq — fast, free tier, Llama-3.3-70B
# Get your key at https://console.groq.com/
GROQ_API_KEY=your-groq-api-key-starting-with-gsk_
# Groq is auto-detected when key starts with "gsk_"
# LLAMA_BASE_URL and LLAMA_MODEL are set automatically for Groq keys.
# Override only if using a different provider:
LLAMA_API_KEY=
LLAMA_BASE_URL=https://api.groq.com/openai/v1
LLAMA_MODEL=llama-3.3-70b-versatile
NEWS_API_KEY=your-newsapi-key
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=data/finx.db
CORS_ORIGINS=http://localhost:5173
RADAR_INTERVAL_HOURS=1

# ── Auth v2 — JWT ─────────────────────────────────────────────────────────────
# Generate a strong random key: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=replace-with-a-random-secret-at-least-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=14

# ── Auth v2 — App URLs ────────────────────────────────────────────────────────
APP_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

# ── Auth v2 — SMTP (email verification) ──────────────────────────────────────
# Gmail: create an App Password at Google Account > Security > 2-Step Verification > App passwords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.address@gmail.com
SMTP_PASS=your-16-char-app-password

# ── Auth v2 — Google OAuth (optional) ────────────────────────────────────────
# Create credentials at console.cloud.google.com > APIs & Services > Credentials
# Authorised redirect URI (dev): http://localhost:5173/api/v2/auth/google/callback
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:5173/api/v2/auth/google/callback

```

```bash
uvicorn main:app --reload
# API  → http://localhost:8000
# Docs → http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000/api" > .env.local
npm run dev
# App → http://localhost:5173
```

---

## 📡 API Reference

### Auth — `/api/v2/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/signup` | Register — bcrypt hash + Brevo verification email |
| `GET` | `/verify-email?token=` | Activate account via email link |
| `POST` | `/login` | Credentials → access + refresh JWT pair |
| `POST` | `/refresh` | Rotate tokens — old token instantly invalidated |
| `GET` | `/me` | Current authenticated user |
| `GET` | `/google/login` | Start Google OAuth 2.0 flow |
| `GET` | `/google/callback` | OAuth callback — issues JWT pair |

### Market — `/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/signals` | All active radar signals |
| `POST` | `/signals/refresh` | Force radar refresh |
| `GET` | `/card/{symbol}` | Full AI signal card for a stock |
| `GET` | `/market/price/{symbol}` | Ultra-fast price + OHLCV only — &lt;50 ms from cache |
| `GET` | `/market/live/{symbol}` | Live NSE quote + intraday (price + OHLCV + chart data) |
| `GET` | `/market/chart/{symbol}` | OHLCV chart data |
| `WS` | `/market/ws/{symbol}` | Real-time WebSocket price feed |
| `GET` | `/market/movers` | Top gainers, losers, cheapest, most expensive |
| `GET` | `/market/status` | Market open / closed |
| `POST` | `/chat` | Grounded market chat (context-injected) |
| `GET` | `/finpulse` | AI-augmented finance news |
| `GET` | `/search?q=` | Symbol search |
| `GET` | `/analytics/success-rate/{symbol}` | Pattern success stats |
| `GET` | `/analytics/clusters` | Institutional cluster map |

> Full interactive Swagger UI at `/docs` · ReDoc at `/redoc`

---

## 🧪 Testing

```bash
cd backend
pytest tests/test_auth.py -v
# ✓ 22 passed in 6.97s
```

| Suite | What's covered |
|---|---|
| **Signup** | Valid signup, duplicate email, 4 weak password variants |
| **Login** | Unverified block, correct credentials, wrong password, unknown email, JWT format |
| **`/me` endpoint** | Authenticated, missing token, invalid token |
| **Token refresh** | Successful rotation, old token rejected, invalid token |
| **Email verification** | Invalid token redirect, valid token activation |
| **Rate limiting** | 429 response after 10 failed attempts per IP |
| **Security headers** | All 5 headers present on every response |

---

## 🛡 Security

| Feature | Implementation |
|---|---|
| Password hashing | bcrypt, 12 rounds |
| Token signing | HS256 JWT via python-jose |
| Refresh rotation | Version-locked — old tokens instantly invalidated on use |
| Rate limiting | Per-IP, 10 attempts / 60 seconds |
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy` |
| CORS | Explicit origin whitelist via `CORS_ORIGINS` env var |
| Secrets | `.env` only — nothing hardcoded in source |

---

## ☁️ Deployment

### Backend → Render

`render.yaml` included at `backend/render.yaml`. Connect repo on Render, set env vars in dashboard.

```env
DATABASE_URL=postgresql+psycopg2://user:pass@host/db
```
App auto-switches from SQLite via SQLAlchemy — no code changes needed.

### Frontend → Vercel / Netlify

```bash
cd frontend && npm run build
# Set: VITE_API_URL=https://your-backend.onrender.com/api
```

---

## 📁 Project Structure

```
FIN-X/
├── backend/
│   ├── main.py                    app factory, middleware, router registration
│   ├── database.py                SQLite layer (v1 routes)
│   ├── scheduler.py               APScheduler — hourly radar refresh
│   ├── core/
│   │   ├── config.py              Pydantic settings (reads .env)
│   │   ├── db.py                  SQLAlchemy engine + session
│   │   └── security.py            bcrypt + JWT create/decode
│   ├── models/user.py             auth_users SQLAlchemy model
│   ├── schemas/auth.py            Pydantic request/response schemas
│   ├── routes/auth.py             all /api/v2/auth/* endpoints
│   ├── routers/                   signals, cards, chat, market, finpulse
│   ├── services/                  15+ modules: NSE, AI, email, OAuth
│   ├── tests/test_auth.py         22 pytest tests
│   ├── prompts/                   AI prompt templates
│   ├── .env.example
│   ├── render.yaml
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx                loading guard + route switch
    │   ├── api/index.js           Axios client + silent token refresh
    │   ├── context/
    │   │   ├── AuthContext.jsx    tokens, session restore, Google callback
    │   │   └── ThemeContext.jsx   dark/light mode
    │   ├── components/            Navbar, SignalCard, ChatInterface
    │   └── pages/                 Landing, Radar, Card, Chat, FinPulse
    ├── vite.config.js             code-split: react/chart/http vendors
    └── package.json
```

---

## 🏆 Why FIN-X

| The old way | The FIN-X way |
|---|---|
| Raw NSE bulk deal CSV — no context | AI-explained signal with risk level and confidence score |
| Single AI model — single point of failure | 3-tier stack: Gemini → GPT-4o mini → rules. Zero downtime. |
| Stock screeners that predict | Explanation-first: *why* it happened, not just *what* |
| Generic financial chatbots | Context-injected: live prices + deals + news in every answer |
| No auth or basic sessions | Production JWT + Google OAuth + bcrypt + rate limiting |
| Ship and hope | 22 passing pytest tests across 7 suites before prod |

---

<div align="center">

**Built for the Economic Times AI Fintech Hackathon — AI Fintech Track**

*Educational use only · Not SEBI-registered investment advice · Data: NSE India*

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:6d28d9,50:1a2744,100:0f172a&height=120&section=footer&animation=fadeIn" width="100%"/>

</div>
