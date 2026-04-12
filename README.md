# ARIA — Autonomous Research & Intelligence Agent

ARIA is a stock market intelligence web application with a FastAPI backend and React frontend. It combines retrieval-augmented generation (RAG), hybrid search, and agentic reasoning to produce grounded market insights.

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: React + Vite
- **Agent Brain**: Groq API (`llama3-70b-8192`)
- **Embeddings**: HuggingFace sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector Database**: Pinecone
- **Retrieval**: Hybrid BM25 + vector similarity
- **Reranking**: MMR (Maximal Marginal Relevance)
- **Workflow Automation**: n8n
- **Market Data**: Finnhub (live quote API)

---

## Project Structure

```text
.
├── .env.example
├── requirements.txt
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── health.py
│   │   │   ├── query.py
│   │   │   └── stocks.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── groq_agent.py
│   │   │   ├── embeddings.py
│   │   │   ├── hybrid_search.py
│   │   │   ├── market_data.py
│   │   │   ├── pinecone_client.py
│   │   │   ├── rag.py
│   │   │   └── news_service.py
│   │   └── main.py
│   └── tests/
│       └── test_health.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── styles.css
│       └── services/api.js
└── workflows/
    └── n8n/
        ├── README.md
        └── sample_market_ingestion_workflow.json
```

---

## System Architecture

### 1) Data Ingestion + Automation (n8n)

n8n orchestrates scheduled ingestion pipelines:
- Pull market news, filings, transcripts, and macro datasets.
- Normalize and chunk content.
- Generate embeddings via local HuggingFace sentence-transformers.
- Upsert vectors + metadata into Pinecone.

### 2) Real-Time Market Layer

FastAPI exposes market endpoints (`/api/stocks/quote/{ticker}` + SSE stream) backed by Finnhub and a NewsAPI endpoint (`/api/stocks/news/{ticker}`).

### 3) Retrieval Layer (RAG)

Given a user question:
1. Create query embedding with sentence-transformers.
2. Run vector search in Pinecone with metadata filters.
3. Run lexical BM25 scoring over candidate chunks.
4. Fuse results and rerank with MMR for diversity + relevance.
5. Send top context chunks to Groq (Llama 3 70B).

### 4) Agent Reasoning Layer (Groq)

Groq receives:
- User prompt
- Retrieved evidence chunks
- Optional portfolio/ticker constraints

It returns grounded analysis, bullish/bearish factors, risks, and likely scenarios.

### 5) Frontend UX (React)

The frontend provides:
- Ticker quote panel (real-time query)
- Analyst prompt panel (“Ask ARIA”)
- Result rendering with citations (ready for extension)

---

## Local Setup Guide (Step-by-Step)

### 1) Clone and enter the project
```bash
git clone <your-repo-url>
cd market-intelligence-agent
```

### 2) Create Python virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install backend dependencies
```bash
pip install -r requirements.txt
```

### 4) Configure environment variables
A full `.env` template is included at the project root with instructions for every key.

Required API keys:
- `GROQ_API_KEY`
- `PINECONE_API_KEY`
- `FINNHUB_API_KEY`
- `NEWS_API_KEY`

If needed, you can also regenerate from the sample:
```bash
cp .env.example .env
```

### 5) Run the FastAPI backend
```bash
uvicorn backend.app.main:app --reload
```
Backend runs at `http://localhost:8000`.

### 6) Install frontend dependencies
```bash
cd frontend
npm install
```

### 7) Run the React frontend
```bash
npm run dev
```
Frontend runs at `http://localhost:5173`.

### 8) Verify the app is healthy
In another terminal:
```bash
curl http://localhost:8000/api/health
```
Expected response:
```json
{"status":"ok"}
```

### 9) Try key endpoints
- Quote: `GET /api/stocks/quote/AAPL`
- News: `GET /api/stocks/news/AAPL`
- ARIA Query: `POST /api/query`

---

## API Endpoints

- `GET /api/health` — health check
- `GET /api/stocks/quote/{ticker}` — latest stock quote
- `GET /api/stocks/stream?ticker=AAPL` — SSE quote stream
- `GET /api/stocks/news/{ticker}` — latest company news from NewsAPI
- `POST /api/query` — ask ARIA with hybrid retrieval + Groq answer

### Example Query Payload

```json
{
  "question": "What are key near-term risks for NVIDIA?",
  "tickers": ["NVDA"],
  "filters": {
    "ticker": "NVDA",
    "sector": "Semiconductors"
  }
}
```

---

## Future Enhancements

- Portfolio-aware agent mode
- Multi-step tool-using agent plans
- Earnings event monitoring + alerts
- Backtesting and signal scoring
- Multi-source market data routing and failover
