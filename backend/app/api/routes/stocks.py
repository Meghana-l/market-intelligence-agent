import asyncio
import httpx
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from app.models.schemas import NewsArticle, StockQuote
from app.services.market_data import MarketDataService
from app.services.news_service import NewsService
from app.core.config import settings

router = APIRouter()
market_data_service = MarketDataService()
news_service = NewsService()

def get_company_profile(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker.upper()}"
        params = {"modules": "summaryProfile,summaryDetail,price"}
        headers = {"User-Agent": "Mozilla/5.0"}
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params, headers=headers)
            data = response.json()
        result = data.get("quoteSummary", {}).get("result", [{}])[0]
        profile = result.get("summaryProfile", {})
        price_data = result.get("price", {})
        detail = result.get("summaryDetail", {})
        return {
            "name": price_data.get("longName") or price_data.get("shortName", ticker),
            "finnhubIndustry": profile.get("industry", "—"),
            "marketCapitalization": price_data.get("marketCap", {}).get("raw", 0) / 1e6 if price_data.get("marketCap") else None,
            "weburl": profile.get("website", ""),
            "beta": detail.get("beta", {}).get("raw"),
        }
    except Exception as e:
        print(f"Yahoo profile error for {ticker}: {e}")
        return {}

def get_stock_metric(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker.upper()}"
        params = {"modules": "summaryDetail,defaultKeyStatistics"}
        headers = {"User-Agent": "Mozilla/5.0"}
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params, headers=headers)
            data = response.json()
        result = data.get("quoteSummary", {}).get("result", [{}])[0]
        detail = result.get("summaryDetail", {})
        stats = result.get("defaultKeyStatistics", {})
        return {
            "52WeekHigh": detail.get("fiftyTwoWeekHigh", {}).get("raw"),
            "52WeekLow": detail.get("fiftyTwoWeekLow", {}).get("raw"),
            "beta": detail.get("beta", {}).get("raw") or stats.get("beta", {}).get("raw"),
        }
    except Exception as e:
        print(f"Yahoo metrics error for {ticker}: {e}")
        return {}

@router.get("/quote/{ticker}")
def get_stock_quote(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker.upper()}"
        params = {"modules": "summaryProfile,summaryDetail,price,defaultKeyStatistics"}
        headers = {"User-Agent": "Mozilla/5.0"}
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params, headers=headers)
            data = response.json()

        result = data.get("quoteSummary", {}).get("result", [{}])[0]
        profile = result.get("summaryProfile", {})
        price_data = result.get("price", {})
        detail = result.get("summaryDetail", {})
        stats = result.get("defaultKeyStatistics", {})

        current = price_data.get("regularMarketPrice", {}).get("raw", 0)
        previous = price_data.get("regularMarketPreviousClose", {}).get("raw", 0)
        change = current - previous
        change_percent = ((change / previous) * 100) if previous else 0

        market_cap_raw = price_data.get("marketCap", {}).get("raw", 0)
        if market_cap_raw:
            market_cap = f"${market_cap_raw/1e12:.2f}T" if market_cap_raw > 1e12 else f"${market_cap_raw/1e9:.0f}B"
        else:
            market_cap = "—"

        week_52_high = detail.get("fiftyTwoWeekHigh", {}).get("raw")
        week_52_low = detail.get("fiftyTwoWeekLow", {}).get("raw")
        week_52_range = f"${week_52_low:.2f}–${week_52_high:.2f}" if week_52_high and week_52_low else "—"

        beta = detail.get("beta", {}).get("raw") or stats.get("beta", {}).get("raw")

        return {
            "ticker": ticker.upper(),
            "current_price": current,
            "change_percent": round(change_percent, 2),
            "name": price_data.get("longName") or price_data.get("shortName", ticker),
            "sector": profile.get("sector", "—"),
            "market_cap": market_cap,
            "week_52_range": week_52_range,
            "beta": beta,
        }
    except Exception as e:
        print(f"Yahoo quote error: {e}")
        quote = market_data_service.get_quote(ticker)
        return {
            "ticker": quote.ticker,
            "current_price": quote.price,
            "change_percent": quote.change_percent,
            "name": ticker,
            "sector": "—",
            "market_cap": "—",
            "week_52_range": "—",
            "beta": None,
        }

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

@router.get("/search")
def search_ticker(q: str) -> dict:
    try:
        params = {"q": q, "token": settings.finnhub_api_key}
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://finnhub.io/api/v1/search", params=params)
            return response.json()
    except:
        return {"result": []}

@router.get("/stream")
def stream_quotes(ticker: str = "AAPL") -> EventSourceResponse:
    async def generator():
        while True:
            quote = market_data_service.get_quote(ticker)
            yield {"event": "quote", "data": quote.model_dump_json()}
            await asyncio.sleep(10)
    return EventSourceResponse(generator())
