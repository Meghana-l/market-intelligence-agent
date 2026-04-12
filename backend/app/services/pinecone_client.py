from pinecone import Pinecone

from app.core.config import settings


class PineconeService:
    def __init__(self) -> None:
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.client.Index(settings.pinecone_index_name)

    def query(self, vector: list[float], top_k: int, metadata_filter: dict | None = None):
        return self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=settings.pinecone_namespace,
            filter=metadata_filter or {},
        )
