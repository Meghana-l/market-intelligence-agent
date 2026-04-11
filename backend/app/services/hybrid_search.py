from dataclasses import dataclass

from rank_bm25 import BM25Okapi


@dataclass
class SearchHit:
    id: str
    text: str
    score: float
    metadata: dict


class HybridSearchService:
    """Combines BM25 lexical scoring with vector similarity and MMR reranking."""

    @staticmethod
    def bm25_rank(query: str, corpus: list[dict], top_k: int) -> list[SearchHit]:
        tokenized_corpus = [doc["text"].lower().split() for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(query.lower().split())

        ranked = sorted(zip(corpus, scores), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            SearchHit(id=doc["id"], text=doc["text"], score=float(score), metadata=doc.get("metadata", {}))
            for doc, score in ranked
        ]

    @staticmethod
    def mmr_rerank(query_embedding: list[float], candidates: list[SearchHit], lambda_param: float, top_k: int) -> list[SearchHit]:
        # Placeholder for true cosine/MMR implementation.
        # The interface is ready for a production-grade reranker.
        del query_embedding, lambda_param
        return sorted(candidates, key=lambda c: c.score, reverse=True)[:top_k]
