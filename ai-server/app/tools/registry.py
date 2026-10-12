"""앱 시작 시 Market Tool들을 Gateway에 등록."""
from .gateway import gateway, ToolSpec
from . import market_tools as mt
from . import rag_tools as rt
from . import compliance as cp
from . import mock_core_client as mc   


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
    # register_default_tools() 마지막에 추가
    gateway.register(ToolSpec(                     # ← 7장 추가
        name="check_compliance_rules",
        func=cp.check_compliance_rules,
        required_scopes=["REPORT_READ"],
        description="보고서 초안의 규정 위반 후보 검사",
    ))
    gateway.register(ToolSpec(
    name="get_account",
    func=mc.mock_core_client.get_account,
    required_scopes=["ACCOUNT_READ"],
    description="가상 계좌 정보 조회 (Core Zone)",
    ))
    gateway.register(ToolSpec(
    name="get_balance",
    func=mc.mock_core_client.get_balance,
    required_scopes=["ACCOUNT_READ"],
    description="가상 계좌 잔고 조회 (Core Zone)",
    ))
    gateway.register(ToolSpec(
    name="list_orders",
    func=mc.mock_core_client.list_orders,
    required_scopes=["ACCOUNT_READ"],
    description="주문 내역 조회 (Core Zone)",
    ))