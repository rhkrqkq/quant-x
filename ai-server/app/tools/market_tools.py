"""Agent가 호출하는 시장 데이터 Tool 4종.
모든 Tool은 Tool Gateway를 통해서만 호출되어야 한다 (직접 import 금지).
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

import sqlalchemy as sa

from .db import get_engine                               # yfinance와 무관한 엔진 모듈
from .master_data import STOCK_MASTER, find_ticker


@dataclass
class StockPrice:
    ticker: str
    name: str
    trade_date: str
    close: float
    change_pct: Optional[float]


@dataclass
class FinancialMetrics:
    ticker: str
    name: str
    per: Optional[float]
    pbr: Optional[float]
    roe_pct: Optional[float]
    market_cap_won: Optional[float]


@dataclass
class MarketSummary:
    date: str
    sample_size: int                                     # 집계 대상 종목 수
    avg_change_pct: Optional[float]                      # 평균 등락률 (참고용; KOSPI 지수 피드와는 다름)
    top_gainers: List[StockPrice]
    top_losers: List[StockPrice]


# ----------------------------------------------------------------
# Tool 1: 종목 검색
# ----------------------------------------------------------------
def search_stock(query: str) -> List[dict]:
    """종목명/티커로 검색하여 매칭 결과 반환."""
    q = query.strip()
    results: list[dict] = []
    for s in STOCK_MASTER.values():
        if q == s.ticker or q in s.name_kr or q.lower() in s.name_en.lower():
            results.append({
                "ticker": s.ticker, "nameKr": s.name_kr, "nameEn": s.name_en,
                "market": s.market, "sector": s.sector,
            })
    return results[:10]


# ----------------------------------------------------------------
# Tool 2: 주가 조회
# ----------------------------------------------------------------
def get_stock_price(ticker_or_name: str, days: int = 1) -> List[StockPrice]:
    ticker = find_ticker(ticker_or_name)
    if ticker is None:
        return []
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(sa.text("""
            SELECT trade_date, close_price
            FROM market_data_sample
            WHERE ticker=:t AND trade_date >= :since
            ORDER BY trade_date DESC
            LIMIT :limit
        """), {"t": ticker, "since": date.today() - timedelta(days=days+5),
               "limit": days + 1}).all()

    name = STOCK_MASTER[ticker].name_kr
    out: List[StockPrice] = []
    for i, r in enumerate(rows):
        prev = rows[i+1].close_price if i+1 < len(rows) else None
        # close_price는 DECIMAL 컬럼이라 Decimal로 돌아온다.
        # float로 내리지 않으면 change_pct가 Decimal이 되어 JSON 직렬화에서 막힌다.
        change_pct = (
            None if prev is None
            else round((float(r.close_price) / float(prev) - 1) * 100, 2)
        )
        out.append(StockPrice(
            ticker=ticker, name=name,
            trade_date=str(r.trade_date), close=float(r.close_price),
            change_pct=change_pct,
        ))
    return out


# ----------------------------------------------------------------
# Tool 3: 재무지표 조회
# ----------------------------------------------------------------
def get_financial_metrics(ticker_or_name: str) -> Optional[FinancialMetrics]:
    ticker = find_ticker(ticker_or_name)
    if ticker is None:
        return None
    eng = get_engine()
    with eng.connect() as conn:
        r = conn.execute(sa.text("""
            SELECT per_ratio, pbr_ratio, roe_ratio, close_price, volume
            FROM market_data_sample
            WHERE ticker=:t
            ORDER BY trade_date DESC LIMIT 1
        """), {"t": ticker}).first()
    if r is None:
        return FinancialMetrics(ticker=ticker, name=STOCK_MASTER[ticker].name_kr,
                                per=None, pbr=None, roe_pct=None, market_cap_won=None)
    return FinancialMetrics(
        ticker=ticker,
        name=STOCK_MASTER[ticker].name_kr,
        per=float(r.per_ratio) if r.per_ratio else None,
        pbr=float(r.pbr_ratio) if r.pbr_ratio else None,
        roe_pct=float(r.roe_ratio) * 100 if r.roe_ratio else None,
        market_cap_won=None,                         # 발행주식수 필요 - 운영 시 별도 테이블
    )


# ----------------------------------------------------------------
# Tool 4: 시장 요약
# ----------------------------------------------------------------
def get_market_summary(target_date: Optional[str] = None) -> MarketSummary:
    """주어진 날짜(미지정이면 최근 거래일) 기준 KOSPI 요약."""
    eng = get_engine()
    with eng.connect() as conn:
        if target_date:
            ref = conn.execute(sa.text("""
                SELECT MAX(trade_date) AS d FROM market_data_sample WHERE trade_date <= :d
            """), {"d": target_date}).scalar()
        else:
            ref = conn.execute(sa.text(
                "SELECT MAX(trade_date) FROM market_data_sample")).scalar()

        if ref is None:
            return MarketSummary(date=str(date.today()), sample_size=0,
                                 avg_change_pct=None, top_gainers=[], top_losers=[])

        rows = conn.execute(sa.text("""
            SELECT m.ticker, m.close_price,
                   prev.close_price AS prev_close, sm.name_kr
            FROM market_data_sample m
            JOIN stock_master sm ON sm.ticker = m.ticker
            LEFT JOIN market_data_sample prev
              ON prev.ticker = m.ticker
             AND prev.trade_date = (SELECT MAX(trade_date)
                                    FROM market_data_sample
                                    WHERE ticker=m.ticker AND trade_date < m.trade_date)
            WHERE m.trade_date = :d
        """), {"d": ref}).all()

    enriched = []
    for r in rows:
        change_pct = None
        if r.prev_close is not None and r.prev_close > 0:
            change_pct = round((float(r.close_price) / float(r.prev_close) - 1) * 100, 2)
        enriched.append(StockPrice(
            ticker=r.ticker, name=r.name_kr, trade_date=str(ref),
            close=float(r.close_price), change_pct=change_pct,
        ))

    enriched_with_change = [e for e in enriched if e.change_pct is not None]
    enriched_with_change.sort(key=lambda x: x.change_pct or 0, reverse=True)
    top_gainers = enriched_with_change[:5]
    top_losers = list(reversed(enriched_with_change[-5:]))

    avg_change = (
        sum(e.change_pct for e in enriched_with_change) / len(enriched_with_change)
        if enriched_with_change else None
    )

    return MarketSummary(
        date=str(ref),
        sample_size=len(enriched_with_change),
        avg_change_pct=round(avg_change, 2) if avg_change is not None else None,
        top_gainers=top_gainers, top_losers=top_losers,
    )