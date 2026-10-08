"""4장 RAG 검색을 Tool Gateway에 등록하기 위한 래퍼."""
from __future__ import annotations
from typing import List, Optional
import threading

from ..rag.service import RAGService

_service: Optional[RAGService] = None
_lock = threading.Lock()


def _get_service() -> RAGService:
    """임베딩 모델 로딩 비용이 크므로 프로세스당 1회만 생성한다.
    [주의] LangChain이 sync tool을 스레드풀에서 실행하므로 락이 필요하다.
    """
    global _service
    if _service is None:
        with _lock:
            if _service is None:               # 이중 검사
                _service = RAGService()
    return _service


def search_documents(query: str, top_k: int = 5) -> List[dict]:
    """사내 문서 검색. Scope 검사는 Tool Gateway가 이미 수행했다."""
    hits = _get_service().search(
        query=query,
        scope=["RAG_READ"],
        top_k=min(max(top_k, 1), 10),
        min_score=0.4,
        trust_levels=["HIGH", "MEDIUM"],          # [보안] LOW 신뢰도 문서는 근거로 쓰지 않는다
    )
    return [
        {
            "citation": f"[{h.chunk_id}]",         # 4장과 동일한 인용 형식
            "title": h.title,
            "score": round(h.score, 2),
            "content": h.content[:200],            # 컨텍스트 보호 (요약 상한 안에 5건이 들어가도록)
        }
        for h in hits
    ]