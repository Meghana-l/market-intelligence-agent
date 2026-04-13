from datetime import datetime, timezone
import httpx
from app.models.schemas import StockQuote

class MarketDataService:
    def get_quote(self, ticker: str) -> StockQuote:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}"
            headers = {"User-Agent": "Mozilla/5.0"}
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            result = data["chart"]["result"][0]
            meta = result["meta"]
            current = float(meta.get("regularMarketPrice", 0))
            previous = float(meta.get("previousClose", 0) or meta.get("chartPreviousClose", 0))
            change = current - previous
            change_percent = ((change / previous) * 100) if previous else 0

            return StockQuote(
                ticker=ticker.upper(),
                price=current,
                change=change,
                change_percent=change_percent,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            print(f"Yahoo Finance error for {ticker}: {e}")
            return StockQuote(
                ticker=ticker.upper(),
                price=0,
                change=0,
                change_percent=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
