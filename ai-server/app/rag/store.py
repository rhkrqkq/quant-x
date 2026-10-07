from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .embeddings import build_embedding_provider


class VectorStore:
    """Chroma 기반 Vector Store. 운영 시 Qdrant/Milvus로 교체 가능."""

    COLLECTION = "financial_documents"

    def __init__(self, persist_dir: str | None = None):
        persist_dir = persist_dir or "./data/chroma"
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._embeddings = build_embedding_provider().get()
        self._chroma = Chroma(
            collection_name=self.COLLECTION,
            embedding_function=self._embeddings,
            persist_directory=persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )

    def add(self, documents: List[Document]) -> List[str]:
        return self._chroma.add_documents(documents)

    def similarity_search(
        self,
        query: str,
        k: int = 10,
        where: Optional[Dict[str, Any]] = None,) -> List[tuple[Document, float]]:
        # Chroma는 (Document, distance) 리스트 반환. distance 작을수록 유사.
        return self._chroma.similarity_search_with_score(
            query=query, k=k, filter=where
        )

    def delete_by_doc_id(self, doc_id: str) -> None:
        self._chroma.delete(where={"doc_id": doc_id})

    def reset(self) -> None:
        self._chroma.reset_collection()