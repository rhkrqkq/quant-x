"""종목 마스터와 금융 약어 사전. 본 과정 10종목.
운영 환경에서는 별도 마스터 DB(KRX/Coscom)에서 동기화한다.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class StockInfo:
    ticker: str
    name_kr: str
    name_en: str
    market: str
    sector: str
    industry: str


# 본 과정 표준 10종목.
# 운영 환경에서는 사내 마스터 DB(KRX/Coscom)에서 startup 시 30~수천 개를 로드한다.
# 학습용으로는 본 10개로 충분하며, 본인이 원하면 동일 형식으로 자유롭게 확장한다.
STOCK_MASTER: dict[str, StockInfo] = {
    "005930": StockInfo("005930", "삼성전자", "Samsung Electronics", "KOSPI", "IT", "Semiconductor"),
    "000660": StockInfo("000660", "SK하이닉스", "SK Hynix",          "KOSPI", "IT", "Semiconductor"),
    "035720": StockInfo("035720", "카카오",     "Kakao",             "KOSPI", "Comm.", "Internet"),
    "035420": StockInfo("035420", "NAVER",      "Naver",             "KOSPI", "Comm.", "Internet"),
    "005380": StockInfo("005380", "현대차",     "Hyundai Motor",     "KOSPI", "Industrials", "Auto"),
    "051910": StockInfo("051910", "LG화학",     "LG Chem",           "KOSPI", "Materials", "Chemicals"),
    "068270": StockInfo("068270", "셀트리온",   "Celltrion",         "KOSPI", "Healthcare", "Biotech"),
    "207940": StockInfo("207940", "삼성바이오로직스", "Samsung Biologics", "KOSPI", "Healthcare", "Biotech"),
    "373220": StockInfo("373220", "LG에너지솔루션", "LG Energy Solution", "KOSPI", "Industrials", "Battery"),
    "000270": StockInfo("000270", "기아",       "Kia",                "KOSPI", "Industrials", "Auto"),
}

# 종목명 → 티커 역매핑 (검색용)
NAME_TO_TICKER: dict[str, str] = {}
for s in STOCK_MASTER.values():
    NAME_TO_TICKER[s.name_kr] = s.ticker
    NAME_TO_TICKER[s.name_en.lower()] = s.ticker


def find_ticker(query: str) -> str | None:
    """티커 또는 종목명으로 티커 조회."""
    q = query.strip()
    if q in STOCK_MASTER:
        return q
    if q in NAME_TO_TICKER:
        return NAME_TO_TICKER[q]
    if q.lower() in NAME_TO_TICKER:
        return NAME_TO_TICKER[q.lower()]
    # 부분 일치 (가장 짧은 것 우선)
    cands = [s for s in STOCK_MASTER.values() if q in s.name_kr or q.lower() in s.name_en.lower()]
    if not cands:
        return None
    cands.sort(key=lambda s: len(s.name_kr))
    return cands[0].ticker