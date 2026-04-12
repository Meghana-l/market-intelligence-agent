import os
import uuid
import requests
from datetime import datetime, timedelta

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.environ.get("PINECONE_INDEX_HOST")  # full host URL from Pinecone dashboard
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
HF_API_KEY = os.environ.get("HF_API_TOKEN")  # add this to Railway variables

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX",
    "AMD", "INTC", "ORCL", "CRM", "ADBE", "PYPL", "UBER", "LYFT",
    "JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "AXP",
    "JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "CVS",
    "XOM", "CVX", "BP", "SHEL", "TTE", "COP",
    "BABA", "TSM", "SONY", "SAP", "ASML", "NVO",
    "WMT", "TGT", "COST", "HD", "LOW", "AMZN",
    "BA", "CAT", "GE", "HON", "MMM", "LMT", "RTX",
    "SPY", "QQQ", "DIA", "IWM", "GLD", "SLV", "USO",
]

COMPANY_INFO = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "description": "Apple designs and sells consumer electronics, software, and online services. Known for iPhone, Mac, iPad, and services like iCloud and Apple Music."},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "description": "Microsoft develops software, cloud services, and hardware. Azure cloud platform, Office 365, and Windows are core products."},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "description": "Alphabet is Google's parent company. Revenue driven by Google Search, YouTube ads, and Google Cloud."},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "description": "Amazon operates e-commerce, AWS cloud, and advertising. AWS is the world's leading cloud provider."},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "description": "Meta owns Facebook, Instagram, and WhatsApp. Revenue primarily from digital advertising across its social platforms."},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "description": "NVIDIA designs GPUs for gaming, AI, and data centers. Dominant supplier of AI chips used in training large language models."},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automotive", "description": "Tesla manufactures electric vehicles, solar panels, and energy storage. Also developing full self-driving software and AI robotics."},
    "NFLX": {"name": "Netflix Inc.", "sector": "Communication Services", "description": "Netflix is a streaming entertainment service with over 260 million subscribers globally."},
    "AMD": {"name": "Advanced Micro Devices", "sector": "Technology", "description": "AMD produces CPUs and GPUs competing with Intel and NVIDIA in consumer and data center markets."},
    "INTC": {"name": "Intel Corp.", "sector": "Technology", "description": "Intel manufactures semiconductor chips for PCs, servers, and data centers. Transitioning to foundry services."},
    "JPM": {"name": "JPMorgan Chase", "sector": "Finance", "description": "JPMorgan is the largest US bank by assets, offering investment banking, consumer banking, and asset management."},
    "BAC": {"name": "Bank of America", "sector": "Finance", "description": "Bank of America provides banking, investing, and financial services to individuals, businesses, and institutions."},
    "GS": {"name": "Goldman Sachs", "sector": "Finance", "description": "Goldman Sachs is a leading global investment bank offering financial services in investment banking, securities, and asset management."},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "description": "J&J develops pharmaceuticals, medical devices, and consumer health products globally."},
    "PFE": {"name": "Pfizer Inc.", "sector": "Healthcare", "description": "Pfizer is a global pharmaceutical company known for COVID-19 vaccines and a wide portfolio of prescription medicines."},
    "XOM": {"name": "ExxonMobil", "sector": "Energy", "description": "ExxonMobil is one of the world's largest oil and gas companies, involved in exploration, production, and refining."},
    "CVX": {"name": "Chevron Corp.", "sector": "Energy", "description": "Chevron is an integrated energy company involved in oil, gas, and renewable energy production globally."},
    "BABA": {"name": "Alibaba Group", "sector": "Technology", "description": "Alibaba is China's largest e-commerce and cloud computing company, operating Taobao, Tmall, and Alibaba Cloud."},
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Technology", "description": "TSMC is the world's largest contract chip manufacturer, producing chips for Apple, NVIDIA, AMD, and others."},
    "WMT": {"name": "Walmart Inc.", "sector": "Consumer Staples", "description": "Walmart is the world's largest retailer by revenue, operating thousands of stores and a growing e-commerce business."},
    "SPY": {"name": "S&P 500 ETF", "sector": "ETF", "description": "SPY tracks the S&P 500 index, representing 500 of the largest US publicly traded companies."},
    "QQQ": {"name": "Nasdaq 100 ETF", "sector": "ETF", "description": "QQQ tracks the Nasdaq 100 index, heavily weighted toward technology companies."},
    "GLD": {"name": "Gold ETF", "sector": "Commodity", "description": "GLD tracks the price of gold bullion, used as a hedge against inflation and market uncertainty."},
    "USO": {"name": "Oil ETF", "sector": "Commodity", "description": "USO tracks the price of West Texas Intermediate crude oil futures."},
}

def embed_text(text):
    response = requests.post(
        "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={"inputs": text, "options": {"wait_for_model": True}}
    )
    result = response.json()
    if isinstance(result[0], list):
        return result[0]
    return result

def upsert_to_pinecone(vectors):
    url = f"https://{PINECONE_INDEX_HOST}/vectors/upsert"
    headers = {"Api-Key": PINECONE_API_KEY, "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json={"vectors": vectors})
    return response.json()

def fetch_news(ticker, company_name):
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://newsapi.org/v2/everything?q={company_name}+stock&from={from_date}&sortBy=relevancy&pageSize=5&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get("articles", [])

def seed():
    print("Starting Pinecone seed...")
    all_vectors = []

    # 1. Embed company descriptions
    print("Embedding company descriptions...")
    for ticker, info in COMPANY_INFO.items():
        text = f"{info['name']} ({ticker}) - {info['sector']}: {info['description']}"
        try:
            embedding = embed_text(text)
            all_vectors.append({
                "id": f"company-{ticker}",
                "values": embedding,
                "metadata": {
                    "ticker": ticker,
                    "type": "company_info",
                    "sector": info["sector"],
                    "source": "static",
                    "text": text
                }
            })
            print(f"  ✓ {ticker}")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")

    # 2. Fetch and embed recent news
    print("\nFetching news articles...")
    for ticker, info in COMPANY_INFO.items():
        try:
            articles = fetch_news(ticker, info["name"])
            for article in articles:
                if not article.get("title") or not article.get("description"):
                    continue
                text = f"{article['title']}. {article.get('description', '')}. {article.get('content', '')[:200]}"
                embedding = embed_text(text)
                all_vectors.append({
                    "id": f"news-{ticker}-{uuid.uuid4().hex[:8]}",
                    "values": embedding,
                    "metadata": {
                        "ticker": ticker,
                        "type": "news",
                        "sector": info["sector"],
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "text": text,
                        "published_at": article.get("publishedAt", "")
                    }
                })
            print(f"  ✓ {ticker} — {len(articles)} articles")
        except Exception as e:
            print(f"  ✗ {ticker} news: {e}")

    # 3. Upsert in batches of 50
    print(f"\nUpserting {len(all_vectors)} vectors to Pinecone...")
    batch_size = 50
    for i in range(0, len(all_vectors), batch_size):
        batch = all_vectors[i:i+batch_size]
        result = upsert_to_pinecone(batch)
        print(f"  Batch {i//batch_size + 1}: {result}")

    print("\nDone! Pinecone is populated.")

if __name__ == "__main__":
    seed()
