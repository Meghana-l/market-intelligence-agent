import traceback
from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, DocumentChunk
from app.services.groq_agent import GroqAgentService
from app.services.news_service import NewsService

router = APIRouter()
agent = GroqAgentService()
news_service = NewsService()

@router.post("", response_model=QueryResponse)
def ask_aria(request: QueryRequest) -> QueryResponse:
    try:
        ticker = request.tickers[0] if request.tickers else (request.filters.ticker or "")

        # Fetch live news
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
                print(f"Fetched {len(live_news)} news articles for {ticker}")
            except Exception as e:
                print(f"News fetch error: {e}")

        # Try RAG
        rag_chunks = []
        try:
            from app.services.rag import RagPipeline
            rag = RagPipeline()
            rag_chunks = rag.retrieve(request)
            print(f"RAG returned {len(rag_chunks)} chunks")
        except Exception as e:
            print(f"RAG error (skipping): {e}")
            traceback.print_exc()

        all_chunks = live_news + rag_chunks
        print(f"Total chunks: {len(all_chunks)}, calling Groq...")
        
        answer = agent.answer_question(request.question, all_chunks)
        print(f"Groq answered successfully")
        
        citations = [chunk.id for chunk in all_chunks]
        return QueryResponse(answer=answer, citations=citations, retrieved_chunks=all_chunks)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
