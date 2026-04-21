from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional, List
from app.core.security import get_current_user_id
from app.services.search_service import perform_rag_search

router = APIRouter()


class SearchFilters(BaseModel):
    labels: Optional[List[str]] = None
    senders: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = None
    top_k: int = 10


class EmailCard(BaseModel):
    id: str
    subject: str
    sender_email: str
    sender_name: str
    snippet: str
    date: str
    labels: List[str]
    relevance_score: Optional[float] = None


class SearchResponse(BaseModel):
    answer: str
    sources: list[EmailCard]
    query_time_ms: int


@router.post("/search", response_model=SearchResponse, summary="Hybrid semantic + keyword search")
async def search_emails(req: SearchRequest, user_id: str = Depends(get_current_user_id)):
    """
    1. Embed query with sentence-transformers
    2. ANN search over pgvector (semantic)
    3. Full-text search over body_text (keyword)
    4. RRF fusion → top-k
    5. Groq LLM synthesis → grounded answer
    """
    result = await perform_rag_search(req.query, user_id, req.top_k)
    
    return SearchResponse(
        answer=result['answer'],
        sources=result['sources'],
        query_time_ms=result['query_time_ms'],
    )
