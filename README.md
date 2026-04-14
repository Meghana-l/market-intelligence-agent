# ARIA — Autonomous Research & Intelligence Agent

> **Live Demo:** [market-intelligence-agent-aria.vercel.app](https://market-intelligence-agent-aria.vercel.app/)

ARIA is an AI-powered stock market intelligence web app. Ask any question about the market in plain English — ARIA fetches live data, retrieves relevant context using RAG, and delivers a structured analysis with real-time prices, news, sentiment, and an investment calculator.

---

## Screenshots

### Landing Page

<img width="915" height="592" alt="Screenshot 2026-04-13 205148" src="https://github.com/user-attachments/assets/05329cc4-80f7-4f0a-92e9-b0c4a83273fe" />
*Ask ARIA anything about the market — natural language search with example prompts*

---

### Dashboard

<img width="1886" height="881" alt="Screenshot 2026-04-13 205248" src="https://github.com/user-attachments/assets/fbfa864e-a8b1-45e2-90aa-2465ba91151e" />
<img width="1874" height="702" alt="Screenshot 2026-04-13 205330" src="https://github.com/user-attachments/assets/62987ed3-cfb6-46ac-a8a6-38bc8d71912c" />
*Live stock data, ARIA's AI analysis, investment calculator, market mood, and news — all in one view*

- Live stock price, % change, market cap, sector, 52-week range, risk score
- ARIA's Analysis — AI-generated breakdown with key points, risks, and actionable takeaways
- What ARIA is Doing — animated pipeline showing each step of the agent process
- Investment Calculator — enter shares and buy price, get live P&L instantly
- Market Mood — bullish/neutral/bearish sentiment derived from live price data
- Latest Market News — real headlines from Finnhub and NewsAPI

---

### Chat with ARIA

<img width="366" height="496" alt="Screenshot 2026-04-13 205541" src="https://github.com/user-attachments/assets/4bf8e840-4ef2-4332-92eb-a668616e0ea4" />
*Conversational AI — ask follow-up questions about any stock or market event in real time*

---

### My Watchlist

<img width="1919" height="902" alt="Screenshot 2026-04-13 210221" src="https://github.com/user-attachments/assets/30e9c8ab-b816-4bde-8f88-e96e1404611c" />
*Track multiple stocks with live prices and percentage change for the session*
- Add any ticker and track live prices for the session
- See real-time price and % change for all your stocks at once

---

### News Feed

<img width="1754" height="771" alt="Screenshot 2026-04-13 210313" src="https://github.com/user-attachments/assets/0d21eb93-5af8-491a-a765-f048419c5eab" />
*Search the latest market news for any ticker — powered by Finnhub and NewsAPI*

- Search latest news for any ticker
- Powered by Finnhub with NewsAPI fallback

---

### Geopolitical Map

<img width="1917" height="919" alt="Screenshot 2026-04-13 210355" src="https://github.com/user-attachments/assets/46d916c3-9fb9-4722-90f0-d2b321403925" />
*Global events affecting financial markets with HIGH / MEDIUM / LOW market impact ratings*
- Global events affecting financial markets with HIGH/MEDIUM/LOW impact ratings
- Linked to relevant tickers affected by each event


---

### Architecture Diagram
<img width="773" height="740" alt="Screenshot 2026-04-13 210843" src="https://github.com/user-attachments/assets/93c59108-de8b-4e68-ad52-3db341129eb3" />

---

## What It Does

Type a question like *"Should I invest in NVDA right now?"* and ARIA:

1. Detects the ticker automatically from your natural language query
2. Fetches live price, market cap, sector, and 52-week range from Finnhub
3. Retrieves recent news articles and embeds them using HuggingFace
4. Runs hybrid search (BM25 + vector) + MMR reranking across the knowledge base
5. Passes retrieved context to Groq (LLaMA 3.3 70B) to generate a structured analysis
6. Displays everything in a clean dashboard with calculator, market mood, and live news

---

## Features

**Calculator**
- Standalone investment calculator for any stock
- Fetches live price, computes current value, gain/loss, and cost basis


**Agent Log**
- Full session history of all queries made to ARIA

**Chat with ARIA**
- Conversational AI chat powered by Groq
- Context-aware — ARIA knows the current ticker being analyzed

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript — deployed on Vercel |
| Backend | Python FastAPI — deployed on Render |
| AI Brain | Groq API (LLaMA 3.3 70b Versatile) |
| Vector Database | Pinecone (dimension 384, cosine similarity) |
| Embeddings | HuggingFace Inference API (all-MiniLM-L6-v2) |
| RAG | Hybrid Search (BM25 + Vector) + MMR Reranking + Metadata Filters |
| Stock Data | Finnhub API |
| News | NewsAPI + Finnhub Company News (fallback) |
| Workflow Orchestration | n8n (configured) |

---

## Architecture

<img width="872" height="739" alt="Screenshot 2026-04-13 192034" src="https://github.com/user-attachments/assets/f7bb60f6-e38c-4126-a617-4acde3450590" />

---

## RAG Concepts Used

**Hybrid Search (BM25 + Vector Embeddings)**
Combines keyword precision (BM25) with semantic meaning (vector search) for more accurate retrieval. Neither approach alone is sufficient — hybrid search gives the best of both worlds.

**MMR — Maximal Marginal Relevance**
Reranks retrieved chunks to maximize diversity. Prevents the LLM context from being flooded with near-identical documents, ensuring ARIA draws from a broader range of information.

**Metadata Filters**
Filters the vector store by ticker, sector, source, and date before retrieval. ARIA only searches relevant context for the specific company being analyzed — not the entire knowledge base.

---

## Project Structure

```
market-intelligence-agent/
├── frontend/
│   └── index.html              # Full frontend (single file)
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── query.py        # /api/query — main ARIA endpoint
│   │   │   ├── stocks.py       # /api/stocks/* — price, news, search
│   │   │   └── health.py       # /api/health
│   │   ├── services/
│   │   │   ├── groq_agent.py   # Groq LLM integration
│   │   │   ├── rag.py          # RAG pipeline
│   │   │   ├── embeddings.py   # HuggingFace embeddings
│   │   │   ├── pinecone_client.py
│   │   │   ├── hybrid_search.py
│   │   │   ├── market_data.py  # Finnhub stock data
│   │   │   └── news_service.py # NewsAPI + Finnhub news
│   │   ├── models/schemas.py
│   │   └── core/config.py
│   ├── seed_data.py            # Pinecone data seeding script
│   └── requirements.txt
└── workflows/n8n/              # n8n workflow configs
```

---

## Environment Variables

**Backend (Render):**

```
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
PINECONE_API_KEY=
PINECONE_INDEX_NAME=aria-market-intelligence
PINECONE_ENVIRONMENT=us-east-1
PINECONE_NAMESPACE=default
FINNHUB_API_KEY=
NEWS_API_KEY=
HF_API_TOKEN=
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

**Frontend (Vercel):**
```
VITE_API_BASE_URL=https://your-render-url.onrender.com
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/stocks/quote/{ticker}` | Live price + company profile |
| GET | `/api/stocks/news/{ticker}` | Latest news for ticker |
| GET | `/api/stocks/search?q=` | Search ticker by company name |
| POST | `/api/query` | ARIA analysis (RAG + Groq) |

---

## Built With

- [Groq](https://groq.com/) — ultra-fast LLM inference
- [Pinecone](https://pinecone.io/) — vector database
- [Finnhub](https://finnhub.io/) — real-time stock data
- [NewsAPI](https://newsapi.org/) — market news
- [HuggingFace](https://huggingface.co/) — open-source embeddings
- [n8n](https://n8n.io/) — workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) — Python backend
- [Vercel](https://vercel.com/) — frontend hosting
- [Render](https://render.com/) — backend hosting

---

## Author

**Meghana Lakshminarayana Swamy**
M.S. Business Analytics — University of New Haven

[GitHub](https://github.com/Meghana-l) · [LinkedIn](https://www.linkedin.com/in/meghana-lakshminarayana-swamy)
