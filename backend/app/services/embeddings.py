import httpx
from app.core.config import settings

class EmbeddingService:
    def __init__(self) -> None:
        self.api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        self.hf_token = settings.hf_api_token

    def embed_text(self, text: str) -> list[float]:
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        response = httpx.post(
            self.api_url,
            headers=headers,
            json={"inputs": text, "options": {"wait_for_model": True}},
            timeout=30.0
        )
        result = response.json()
        if isinstance(result, list) and isinstance(result[0], list):
            return result[0]
        return result
