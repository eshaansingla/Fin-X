## Fin-X

> AI-powered financial copilot for retail investors

Fin-X helps users **understand markets, analyse portfolios, and make informed decisions** using explainable AI.

---

##  Features

- 💬 Conversational market assistant  
- 📊 AI-generated insight cards (sentiment, indicators, news impact)  
- 💼 Portfolio health analysis (risk, diversification, exposure)  
- 📬 Automated daily/weekly reports  

---

##  Key Idea

> Not prediction. **Explanation.**

Fin-X translates complex financial data into simple, actionable insights.

---

## Tech Stack

- **Frontend:** React, Tailwind  
- **Backend:** FastAPI, PostgreSQL  
- **AI:** Gemini / LLM + RAG  
- **Data:** NewsAPI

---

## Setup

```bash
git clone https://github.com/aishwarysrivastava1/Fin-X.git
cd Fin-X
```

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```
## Environment Example

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key
# Optional fallback to OpenAI if Gemini is unavailable
OPENAI_API_KEY="your_openai_api_key_here"
NEWSAPI_KEY=your_newsapi_key

# Database
DATABASE_URL=data/finx.db

# Configuration
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
RADAR_INTERVAL_HOURS=1

# Model
GEMINI_MODEL=gemini-2.0-flash-lite
```
