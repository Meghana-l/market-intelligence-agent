from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model_name)

    def embed_text(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
