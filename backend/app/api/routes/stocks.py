import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import NewsArticle, StockQuote
from app.services.market_data import MarketDataService
from app.services.news_service import NewsService

router = APIRouter()
market_data_service = MarketDataService()
news_service = NewsService()


@router.get("/quote/{ticker}", response_model=StockQuote)
def get_stock_quote(ticker: str) -> StockQuote:
    return market_data_service.get_quote(ticker)


@router.get("/news/{ticker}", response_model=list[NewsArticle])
def get_stock_news(ticker: str) -> list[NewsArticle]:
    articles = news_service.get_company_news(ticker)
    return [
        NewsArticle(
            source=article.get("source", {}).get("name", "unknown"),
            title=article.get("title", ""),
            description=article.get("description"),
            url=article.get("url", ""),
            published_at=article.get("publishedAt"),
        )
        for article in articles
    ]


@router.get("/stream")
def stream_quotes(ticker: str = "AAPL") -> EventSourceResponse:
    async def generator():
        while True:
            quote = market_data_service.get_quote(ticker)
            yield {"event": "quote", "data": quote.model_dump_json()}
            await asyncio.sleep(10)

    return EventSourceResponse(generator())
