import httpx
from app.core.config import settings

class NewsService:
    def get_company_news(self, ticker: str, page_size: int = 10) -> list[dict]:
        import datetime
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
