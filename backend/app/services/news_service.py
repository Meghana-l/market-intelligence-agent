import httpx
import datetime
from app.core.config import settings

class NewsService:
    def get_company_news(self, ticker: str, page_size: int = 10) -> list[dict]:
        # Try NewsAPI first
        try:
            articles = self._get_newsapi(ticker, page_size)
            if articles:
                return articles
        except Exception as e:
            print(f"NewsAPI failed, falling back to Finnhub: {e}")

        # Fallback to Finnhub
        try:
            return self._get_finnhub(ticker, page_size)
        except Exception as e:
            print(f"Finnhub news also failed: {e}")
            return []

    def _get_newsapi(self, ticker: str, page_size: int) -> list[dict]:
        params = {
            "q": ticker,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": settings.newsapi_key,
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://newsapi.org/v2/everything", params=params)
            response.raise_for_status()
            return response.json().get("articles", [])

    def _get_finnhub(self, ticker: str, page_size: int) -> list[dict]:
        today = datetime.date.today().isoformat()
        month_ago = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        params = {
            "symbol": ticker.upper(),
            "from": month_ago,
            "to": today,
            "token": settings.finnhub_api_key,
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://finnhub.io/api/v1/company-news", params=params)
            response.raise_for_status()
            articles = response.json()
        return [
            {
                "title": a.get("headline", ""),
                "description": a.get("summary", ""),
                "url": a.get("url", ""),
                "source": {"name": a.get("source", "Finnhub")},
                "publishedAt": a.get("datetime", ""),
            }
            for a in articles[:page_size]
            if a.get("headline")
        ]
