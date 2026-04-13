from app.core.config import settings
from app.models.schemas import DocumentChunk, QueryRequest

class RagPipeline:
    def __init__(self) -> None:
        self._embeddings = None
        self._vector_store = None
        self._hybrid = None

    def _get_embeddings(self):
        if self._embeddings is None:
            from app.services.embeddings import EmbeddingService
            self._embeddings = EmbeddingService()
        return self._embeddings

    def _get_vector_store(self):
        if self._vector_store is None:
            from app.services.pinecone_client import PineconeService
            self._vector_store = PineconeService()
        return self._vector_store

    def _get_hybrid(self):
        if self._hybrid is None:
            from app.services.hybrid_search import HybridSearchService
            self._hybrid = HybridSearchService()
        return self._hybrid

    def _build_metadata_filter(self, req: QueryRequest) -> dict:
        payload = {}
        if req.filters.ticker:
            payload["ticker"] = {"$eq": req.filters.ticker}
        if req.filters.sector:
            payload["sector"] = {"$eq": req.filters.sector}
        if req.filters.source:
            payload["source"] = {"$eq": req.filters.source}
        return payload

    def retrieve(self, req: QueryRequest) -> list[DocumentChunk]:
        from app.services.hybrid_search import SearchHit
        query_vector = self._get_embeddings().embed_text(req.question)
        metadata_filter = self._build_metadata_filter(req)
        vector_results = self._get_vector_store().query(
            vector=query_vector,
            top_k=settings.top_k_vector,
            metadata_filter=metadata_filter,
        )
        vector_hits = [
            SearchHit(
                id=match["id"],
                text=match["metadata"].get("text", ""),
                score=float(match.get("score", 0.0)),
                metadata=match.get("metadata", {}),
            )
            for match in vector_results.get("matches", [])
        ]
        lexical_hits = self._get_hybrid().bm25_rank(
            query=req.question,
            corpus=[{"id": h.id, "text": h.text, "metadata": h.metadata} for h in vector_hits],
            top_k=settings.top_k_bm25,
        )
        merged_hits = {hit.id: hit for hit in [*vector_hits, *lexical_hits]}
        reranked = self._get_hybrid().mmr_rerank(
            query_embedding=query_vector,
            candidates=list(merged_hits.values()),
            lambda_param=settings.mmr_lambda,
            top_k=settings.final_top_k,
        )
        return [DocumentChunk(id=h.id, text=h.text, score=h.score, metadata=h.metadata) for h in reranked]
