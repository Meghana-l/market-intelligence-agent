import httpx

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.model_name = settings.embedding_model_name
        self.base_url = settings.huggingface_inference_base_url.rstrip("/")
        self.api_key = settings.huggingface_api_key

    def embed_text(self, text: str) -> list[float]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "inputs": {
                "source_sentence": text,
                "sentences": [text],
            }
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/{self.model_name}",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list) or not data:
            raise ValueError(f"Unexpected Hugging Face embedding response: {data}")

        vector = data[0]
        if not isinstance(vector, list):
            raise ValueError(f"Unexpected Hugging Face embedding vector payload: {vector}")

        return [float(value) for value in vector]
