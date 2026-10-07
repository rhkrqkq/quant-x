"""임베딩 Provider 추상화. LLM Adapter와 같은 패턴.
10장에서 BGE-M3 (폐쇄망)와 OpenAI를 환경변수로 전환할 수 있게 한다.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import os

from langchain_core.embeddings import Embeddings


class EmbeddingProvider(ABC):
    @abstractmethod
    def get(self) -> Embeddings: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str = "text-embedding-3-small"):
        from langchain_openai import OpenAIEmbeddings
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set")
        self._model = model
        self._embeddings = OpenAIEmbeddings(model=model)

    def get(self) -> Embeddings:
        return self._embeddings

    @property
    def model_name(self) -> str:
        return f"openai:{self._model}"


class BgeM3EmbeddingProvider(EmbeddingProvider):
    """폐쇄망용 (10장에서 본격 사용). HF Sentence-Transformers 기반.
    langchain-huggingface 패키지 사용 (langchain_community.embeddings의 것은 deprecated).
    """
    def __init__(self, model: str = "BAAI/bge-m3"):
        from langchain_huggingface import HuggingFaceEmbeddings
        self._model = model
        self._embeddings = HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": "cpu"},          # GPU 환경: "cuda"
            encode_kwargs={"normalize_embeddings": True},
        )

    def get(self) -> Embeddings:
        return self._embeddings

    @property
    def model_name(self) -> str:
        return f"bge:{self._model}"


def build_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    if provider == "openai":
        return OpenAIEmbeddingProvider(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
    elif provider in ("bge", "bge-m3", "huggingface"):
        return BgeM3EmbeddingProvider(
            model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
        )
    raise ValueError(f"Unknown embedding provider: {provider}")