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
        params = {"symbol": ticker.upper(), "token": settings.finnhub_api_key}
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://finnhub.io/api/v1/stock/profile2", params=params)
            return response.json()
    except:
        return {}

def get_stock_metric_finnhub(ticker: str) -> dict:
    try:
        params = {"symbol": ticker.upper(), "metric": "all", "token": settings.finnhub_api_key}
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://finnhub.io/api/v1/stock/metric", params=params)
            data = response.json()
            return data.get("metric", {})
    except:
        return {}

def get_stock_metric_twelvedata(ticker: str) -> dict:
    try:
        params = {"symbol": ticker.upper(), "apikey": settings.twelvedata_api_key}
        with httpx.Client(timeout=10.0) as client:
            stats = client.get("https://api.twelvedata.com/statistics", params=params).json()
            profile = client.get("https://api.twelvedata.com/profile", params=params).json()
        result = {}
        valuation = stats.get("statistics", {}).get("valuations_metrics", {})
        technicals = stats.get("statistics", {}).get("stock_statistics", {})
        result["52WeekHigh"] = technicals.get("52_week_high")
        result["52WeekLow"] = technicals.get("52_week_low")
        result["beta"] = technicals.get("beta")
        result["market_cap"] = valuation.get("market_capitalization")
        result["sector"] = profile.get("sector", "—")
        result["name"] = profile.get("name", ticker)
        return result
    except:
        return {}

@router.get("/quote/{ticker}")
def get_stock_quote(ticker: str) -> dict:
    quote = market_data_service.get_quote(ticker)
    profile = get_company_profile(ticker)
    metrics = get_stock_metric_finnhub(ticker)

    # If Finnhub returns no profile data, fall back to Twelve Data
    if not profile.get("name") or quote.price == 0:
        td = get_stock_metric_twelvedata(ticker)
        name = td.get("name", ticker)
        sector = td.get("sector", "—")
        market_cap_raw = td.get("market_cap")
        market_cap = f"${float(market_cap_raw)/1e12:.2f}T" if market_cap_raw and float(market_cap_raw) > 1e12 else (f"${float(market_cap_raw)/1e9:.0f}B" if market_cap_raw else "—")
        week_52_high = td.get("52WeekHigh")
        week_52_low = td.get("52WeekLow")
        week_52_range = f"${float(week_52_low):.2f}–${float(week_52_high):.2f}" if week_52_high and week_52_low else "—"
        beta = td.get("beta")

        # Get price from Twelve Data if Finnhub returned 0
        if quote.price == 0:
            try:
                params = {"symbol": ticker.upper(), "apikey": settings.twelvedata_api_key}
                with httpx.Client(timeout=10.0) as client:
                    price_data = client.get("https://api.twelvedata.com/price", params=params).json()
                current_price = float(price_data.get("price", 0))
                change_percent = 0.0
            except:
                current_price = 0
                change_percent = 0.0
        else:
            current_price = quote.price
            change_percent = quote.change_percent

        return {
            "ticker": ticker.upper(),
            "current_price": current_price,
            "change_percent": change_percent,
            "name": name,
            "sector": sector,
            "market_cap": market_cap,
            "week_52_range": week_52_range,
            "beta": beta,
        }

    # Finnhub data available
    market_cap = profile.get("marketCapitalization")
    if market_cap:
        market_cap = f"${market_cap/1000:.2f}T" if market_cap > 1000 else f"${market_cap:.0f}B"
    week_52_high = metrics.get("52WeekHigh")
    week_52_low = metrics.get("52WeekLow")
    week_52_range = f"${week_52_low:.2f}–${week_52_high:.2f}" if week_52_high and week_52_low else "—"
    beta = metrics.get("beta")

    return {
        "ticker": quote.ticker,
        "current_price": quote.price,
        "change_percent": quote.change_percent,
        "name": profile.get("name", ticker),
        "sector": profile.get("finnhubIndustry", "—"),
        "market_cap": market_cap or "—",
        "week_52_range": week_52_range,
        "beta": beta,
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
