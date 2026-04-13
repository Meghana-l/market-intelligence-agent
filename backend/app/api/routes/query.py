from fastapi import APIRouter
from app.models.schemas import QueryRequest, QueryResponse
from app.services.groq_agent import GroqAgentService
from app.services.rag import RagPipeline
from app.services.news_service import NewsService
from app.services.market_data import MarketDataService
from app.models.schemas import DocumentChunk

router = APIRouter()
rag = RagPipeline()
agent = GroqAgentService()
news_service = NewsService()
market_data = MarketDataService()

@router.post("", response_model=QueryResponse)
def ask_aria(request: QueryRequest) -> QueryResponse:
    # 1. Get ticker from request
    ticker = request.tickers[0] if request.tickers else (request.filters.ticker or "")

    # 2. Fetch live news for this ticker
    live_news = []
    if ticker:
        try:
            articles = news_service.get_company_news(ticker, page_size=5)
            live_news = [
                DocumentChunk(
                    id=f"news-live-{i}",
                    text=f"{a.get('title','')}. {a.get('description','')}",
                    score=1.0,
                    metadata={"source": a.get("source", {}).get("name", ""), "ticker": ticker}
                )
                for i, a in enumerate(articles) if a.get("title")
            ]
        except Exception as e:
            print(f"News fetch error: {e}")

    # 3. Get RAG chunks from Pinecone (company context)
    rag_chunks = []
    try:
        rag_chunks = rag.retrieve(request)
    except Exception as e:
        print(f"RAG error: {e}")

    # 4. Combine live news + RAG context
    all_chunks = live_news + rag_chunks

    # 5. If no chunks at all, still answer using Groq with just the question
    answer = agent.answer_question(request.question, all_chunks)
    citations = [chunk.id for chunk in all_chunks]

    return QueryResponse(answer=answer, citations=citations, retrieved_chunks=all_chunks)
