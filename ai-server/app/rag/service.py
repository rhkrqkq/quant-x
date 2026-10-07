from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging
import hashlib

from langchain_core.documents import Document

from .store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    chunk_id: str
    doc_id: str
    title: str
    source: str
    published_at: str
    content: str
    score: float                                    # 0~1 (높을수록 유사)
    trust_level: str
    integrity_ok: bool


class RAGService:
    """Chroma 기반 RAG. 검색·격리·해시 검증을 제공."""

    def __init__(self, store: VectorStore | None = None):
        self.store = store or VectorStore()

    # ---------- 적재 ----------
    def ingest(self, chunks: List[Document]) -> List[str]:
        ids = self.store.add(chunks)
        logger.info("ingested %d chunks", len(chunks))
        return ids

    # ---------- 검색 ----------
    def search(
        self,
        query: str,
        scope: List[str],
        top_k: int = 5,
        min_score: float = 0.6,
        trust_levels: Optional[List[str]] = None,
        date_from: Optional[str] = None,) -> List[SearchHit]:
        # ① Scope 검사
        if "RAG_READ" not in scope:
            raise PermissionError("RAG_READ scope required")

        # ② 메타데이터 필터 구성
        where: Dict[str, Any] = {}
        if trust_levels:
            where["trust_level"] = {"$in": trust_levels}
        if date_from:
            where["published_at"] = {"$gte": date_from}

        # ③ Chroma 검색 (k는 여유 있게)
        raw = self.store.similarity_search(query, k=top_k * 2, where=where or None)

        hits: List[SearchHit] = []
        for doc, distance in raw:
            score = max(0.0, 1.0 - distance)        # cosine distance → similarity
            if score < min_score:
                continue
            integrity = self._verify_hash(doc)
            if not integrity:
                logger.warning("integrity check failed for %s", doc.metadata.get("chunk_id"))
                # 여기서 차단하거나 별도 알람. 본 과정에선 표시만 하고 결과에서 제외.
                continue
            hits.append(SearchHit(
                chunk_id=doc.metadata.get("chunk_id", ""),
                doc_id=doc.metadata.get("doc_id", ""),
                title=doc.metadata.get("title", ""),
                source=doc.metadata.get("source", ""),
                published_at=doc.metadata.get("published_at", ""),
                content=doc.page_content,
                score=score,
                trust_level=doc.metadata.get("trust_level", "MEDIUM"),
                integrity_ok=integrity,
            ))
            if len(hits) >= top_k:
                break
        return hits

    # ---------- 무결성 해시 검증 ----------
    @staticmethod
    def _verify_hash(doc: Document) -> bool:
        stored = doc.metadata.get("content_hash")
        if not stored:
            return True                              # 해시 없는 레거시 청크는 통과 (운영시 false 권장)
        actual = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
        return stored == actual