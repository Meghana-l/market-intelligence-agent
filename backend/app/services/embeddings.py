import httpx
from app.core.config import settings

class EmbeddingService:
    def __init__(self) -> None:
        self.api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

    def embed_text(self, text: str) -> list[float]:
        response = httpx.post(self.api_url, json={"inputs": text})
        return response.json()
