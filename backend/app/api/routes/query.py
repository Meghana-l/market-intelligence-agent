from fastapi import APIRouter

from app.models.schemas import QueryRequest, QueryResponse
from app.services.groq_agent import GroqAgentService
from app.services.rag import RagPipeline

router = APIRouter()
rag = RagPipeline()
agent = GroqAgentService()


@router.post("", response_model=QueryResponse)
def ask_aria(request: QueryRequest) -> QueryResponse:
    chunks = rag.retrieve(request)
    answer = agent.answer_question(request.question, chunks)
    citations = [chunk.id for chunk in chunks]
    return QueryResponse(answer=answer, citations=citations, retrieved_chunks=chunks)
