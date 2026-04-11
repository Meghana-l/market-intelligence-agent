from typing import Any

from pydantic import BaseModel, Field


class MetadataFilters(BaseModel):
    sector: str | None = None
    source: str | None = None
    ticker: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    tickers: list[str] = Field(default_factory=list)
    filters: MetadataFilters = Field(default_factory=MetadataFilters)


class DocumentChunk(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    retrieved_chunks: list[DocumentChunk] = Field(default_factory=list)


class StockQuote(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    timestamp: str


class NewsArticle(BaseModel):
    source: str
    title: str
    description: str | None = None
    url: str
    published_at: str | None = None
