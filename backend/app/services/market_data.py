from datetime import datetime, timezone
import httpx
from app.core.config import settings
from app.models.schemas import StockQuote

class MarketDataService:
    BASE_URL = "https://finnhub.io/api/v1"

    def get_quote(self, ticker: str) -> StockQuote:
        params = {"symbol": ticker.upper(), "token": settings.finnhub_api_key}
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{self.BASE_URL}/quote", params=params)
            response.raise_for_status()
            payload = response.json()
        current = float(payload.get("c", 0) or 0)
        previous_close = float(payload.get("pc", 0) or 0)
        change = current - previous_close
        change_percent = ((change / previous_close) * 100) if previous_close else 0
        return StockQuote(
            ticker=ticker.upper(),
            price=current,
            change=change,
            change_percent=change_percent,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
