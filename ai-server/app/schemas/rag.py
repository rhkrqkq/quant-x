from pydantic import BaseModel, Field
from typing import List, Optional


class RagSearchRequest(BaseModel):
    query: str = Field(..., max_length=1000)
    scope: List[str] = Field(default_factory=lambda: ["RAG_READ"])
    topK: int = 5
    minScore: float = 0.6
    trustLevels: Optional[List[str]] = None
    dateFrom: Optional[str] = None


class RagSearchHit(BaseModel):
    chunkId: str
    docId: str
    title: str
    source: str
    publishedAt: str
    content: str
    score: float
    trustLevel: str


class RagSearchResponse(BaseModel):
    items: List[RagSearchHit]
    total: int