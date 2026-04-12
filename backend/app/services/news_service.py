import httpx

from app.core.config import settings


class NewsService:
    BASE_URL = "https://newsapi.org/v2/everything"

    def get_company_news(self, ticker: str, page_size: int = 10) -> list[dict]:
        params = {
            "q": ticker,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": settings.newsapi_key,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        return payload.get("articles", [])
