"""앱 시작 시 Market Tool들을 Gateway에 등록."""
from .gateway import gateway, ToolSpec
from . import market_tools as mt
from . import rag_tools as rt


def register_default_tools() -> None:
    gateway.register(ToolSpec(
        name="search_stock",
        func=mt.search_stock,
        required_scopes=["MARKET_DATA_READ"],
        description="종목명 또는 티커로 검색",
    ))
    gateway.register(ToolSpec(
        name="get_stock_price",
        func=mt.get_stock_price,
        required_scopes=["MARKET_DATA_READ"],
        description="주가 조회 (최근 N일)",
    ))
    gateway.register(ToolSpec(
        name="get_financial_metrics",
        func=mt.get_financial_metrics,
        required_scopes=["MARKET_DATA_READ"],
        description="PER/PBR/ROE 등 재무지표",
    ))
    gateway.register(ToolSpec(
        name="get_market_summary",
        func=mt.get_market_summary,
        required_scopes=["MARKET_DATA_READ"],
        description="시장 요약 (Top 상승/하락)",
    ))
    gateway.register(ToolSpec(                     # ← 6장 추가
        name="search_documents",
        func=rt.search_documents,
        required_scopes=["RAG_READ"],
        description="사내 리서치 문서 검색 (4장 RAG)",
    ))