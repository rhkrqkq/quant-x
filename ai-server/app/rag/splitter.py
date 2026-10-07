from __future__ import annotations
from typing import List
import hashlib
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    docs: List[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 100,) -> List[Document]:
    """금융 텍스트에 적합한 기본 분할. 규제 문서는 별도 함수 사용 권장."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # 한국어 금융 문서에 자주 나오는 구분자 우선순위
        separators=["\n\n", "\n", "。", ". ", "? ", "! ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(docs)
    # 각 청크에 chunk_id 부착
    indexed = []
    counters: dict[str, int] = {}
    for c in chunks:
        doc_id = c.metadata.get("doc_id", "unknown")
        counters[doc_id] = counters.get(doc_id, 0) + 1
        chunk_idx = counters[doc_id]
        c.metadata["chunk_id"] = f"{doc_id}#chunk-{chunk_idx}"
        c.metadata["chunk_index"] = chunk_idx
        c.metadata["content_hash"] = hashlib.sha256(
            c.page_content.encode("utf-8")
        ).hexdigest()
        indexed.append(c)
    return indexed