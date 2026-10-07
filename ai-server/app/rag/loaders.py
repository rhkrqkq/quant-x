from __future__ import annotations
from typing import Iterator, List
from pathlib import Path
import hashlib

from langchain_core.documents import Document


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_huggingface_dataset(
    name: str = "nmixx-fin/synthetic_financial_report_korean",
    split: str = "train",
    limit: int = 200,
    text_field: str = "text",) -> Iterator[Document]:
    """HuggingFace 데이터셋을 LangChain Document로 변환.
    한국어 합성 금융 리포트 (개발/실습용).
    """
    from datasets import load_dataset
    ds = load_dataset(name, split=split)
    for i, row in enumerate(ds):
        if i >= limit:
            break
        text = row.get(text_field, "")
        if not text:
            continue
        doc_id = f"hf-{name.replace('/', '_')}-{i}"
        title = row.get("title") or row.get("company") or f"리포트 #{i}"
        yield Document(
            page_content=text,
            metadata={
                "doc_id": doc_id,
                "title": str(title)[:500],
                "doc_type": "report",
                "source": f"huggingface://{name}#{i}",
                "published_at": row.get("date") or "2025-01-01",
                "trust_level": "MEDIUM",
                "scope_required": "RAG_READ",
                "content_hash": _hash(text),
            },
        )


def load_local_pdf(path: str | Path) -> List[Document]:
    """로컬 PDF (예: 금융위 가이드)를 페이지 단위 Document로."""
    from langchain_community.document_loaders import PyPDFLoader
    p = Path(path)
    docs = PyPDFLoader(str(p)).load()
    doc_id = f"local-{p.stem}"
    for i, d in enumerate(docs):
        d.metadata.update({
            "doc_id": doc_id,
            "title": p.stem,
            "doc_type": "regulation" if "보안" in p.name or "가이드" in p.name else "report",
            "source": f"file://{p.name}",
            "published_at": "2024-01-01",
            "trust_level": "HIGH",                 # 사내/공식 문서로 간주
            "scope_required": "RAG_READ",
            "page": i + 1,
            "content_hash": _hash(d.page_content),
        })
    return docs


def load_local_markdown(path: str | Path) -> List[Document]:
    from langchain_community.document_loaders import TextLoader
    p = Path(path)
    docs = TextLoader(str(p), encoding="utf-8").load()
    doc_id = f"local-{p.stem}"
    for d in docs:
        d.metadata.update({
            "doc_id": doc_id,
            "title": p.stem,
            "doc_type": "report",
            "source": f"file://{p.name}",
            "published_at": "2025-01-01",
            "trust_level": "HIGH",
            "scope_required": "RAG_READ",
            "content_hash": _hash(d.page_content),
        })
    return docs