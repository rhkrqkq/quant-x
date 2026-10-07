import logging
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import verify_internal_key, require_user_id
from ..schemas.rag import RagSearchRequest, RagSearchHit, RagSearchResponse
from ..rag.service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/rag", tags=["rag"])

_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _service
    if _service is None:
        _service = RAGService()
    return _service


@router.post(
    "/search",
    response_model=RagSearchResponse,
    dependencies=[Depends(verify_internal_key)],)
def search(
    req: RagSearchRequest,
    user_id: str = Depends(require_user_id),       # 검색자 추적 (9장 Audit에 사용)
    svc: RAGService = Depends(get_rag_service),) -> RagSearchResponse:
    try:
        hits = svc.search(
            query=req.query,
            scope=req.scope,
            top_k=req.topK,
            min_score=req.minScore,
            trust_levels=req.trustLevels,
            date_from=req.dateFrom,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    logger.info(
        "rag_search user=%s query_len=%d hits=%d",
        user_id, len(req.query), len(hits),
    )

    items = [
        RagSearchHit(
            chunkId=h.chunk_id, docId=h.doc_id, title=h.title, source=h.source,
            publishedAt=h.published_at, content=h.content, score=h.score,
            trustLevel=h.trust_level,
        ) for h in hits
    ]
    return RagSearchResponse(items=items, total=len(items))