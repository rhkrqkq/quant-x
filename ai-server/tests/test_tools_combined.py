"""본 장의 Tool과 4장 RAG가 같은 보고서 한 문장에 합성될 수 있음을 시연.
6장 단일 Agent가 자동으로 수행할 동작을 미리 수동으로 본다.
"""
from app.tools.market_tools import get_stock_price, get_financial_metrics
from app.rag.service import RAGService


def test_combine_rag_and_tool():
    ticker = "005930"
    prices = get_stock_price(ticker, days=3)
    metrics = get_financial_metrics(ticker)
    rag_hits = RAGService().search(
        "삼성전자 반도체 전망", scope=["RAG_READ"], top_k=3, min_score=0.4,
    )

    print("\n=== 시세 ===")
    for p in prices:
        print(p)
    print("=== 재무 ===")
    print(metrics)
    print("=== RAG ===")
    for h in rag_hits:
        print(f"{h.score:.2f} | {h.title}")

    # 본 장에서는 실패하지 않는다는 것만 검증. 6장 이후 합성 품질 평가는 별도.
    assert isinstance(prices, list)
    assert metrics is None or hasattr(metrics, "ticker")