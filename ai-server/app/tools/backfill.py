"""yfinance에서 종목 마스터의 90일 시세를 받아 DB에 적재.
개발/실습용. 운영은 사내 시세 피드 사용.
"""
from __future__ import annotations
import argparse
import logging
from datetime import date, timedelta

import sqlalchemy as sa
import yfinance as yf

from .db import get_engine
from .master_data import STOCK_MASTER

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def yf_symbol(ticker: str) -> str:
    """KOSPI 티커는 .KS 접미사."""
    return f"{ticker}.KS"


def _to_float(value) -> float:
    """yfinance가 0.2+ 버전에서 Series·MultiIndex 컬럼을 반환할 때 안전 추출."""
    try:
        return float(value)
    except (TypeError, ValueError):
        # Series인 경우 첫 원소
        return float(value.iloc[0])

def _fundamentals(ticker: str) -> tuple[float, float, float] | None:
    """EPS·BPS·ROE를 계산한다. 종목당 1회만 호출한다.
    한국 종목은 yfinance의 trailingEps·bookValue가 비어 있어 원재료로 직접 구한다.
        EPS = 당기순이익 / 발행주식수
        BPS = (당기순이익 / ROE) / 발행주식수      # 자기자본 = 순이익 / ROE
    """
    try:
        info = yf.Ticker(yf_symbol(ticker)).info
    except Exception as e:
        log.warning("yf info failed %s: %s", ticker, e)
        return None
    ni  = info.get("netIncomeToCommon")
    sh  = info.get("sharesOutstanding")
    roe = info.get("returnOnEquity")
    if not (ni and sh and roe):
        log.warning("fundamentals missing for %s", ticker)
        return None
    return ni / sh, (ni / roe) / sh, roe

def backfill(days: int = 90) -> None:
    eng = get_engine()
    end = date.today()
    start = end - timedelta(days=days)

    with eng.begin() as conn:
        # ① stock_master 동기화
        for s in STOCK_MASTER.values():
            conn.execute(sa.text("""
                INSERT INTO stock_master (ticker, name_kr, name_en, market, sector, industry, active)
                VALUES (:ticker, :name_kr, :name_en, :market, :sector, :industry, 1)
                ON DUPLICATE KEY UPDATE
                    name_kr=:name_kr, name_en=:name_en, market=:market,
                    sector=:sector, industry=:industry
            """), s.__dict__)

        # ② market_data_sample 적재
        for ticker in STOCK_MASTER:
            try:
                df = yf.download(
                    yf_symbol(ticker),
                    start=start, end=end,
                    progress=False,
                    auto_adjust=False,                   # OHLCV 원본값 유지
                    group_by="column",                   # MultiIndex 회피
                )
            except Exception as e:
                log.warning("yf failed %s: %s", ticker, e)
                continue
            if df.empty:
                continue
            # yfinance 0.2+ 호환: 컬럼이 MultiIndex면 평탄화
            if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
                df.columns = df.columns.get_level_values(0)

            fund = _fundamentals(ticker)
            for idx, row in df.iterrows():
                trade_date = idx.date() if hasattr(idx, "date") else idx
                close = _to_float(row["Close"])

                per = pbr = roe_val = None
                if fund:
                    eps, bps, roe_val = fund
                    # 적자 종목은 PER이 성립하지 않는다 (EPS < 0)
                    per = round(close / eps, 2) if eps > 0 else None
                    pbr = round(close / bps, 2) if bps > 0 else None

                conn.execute(sa.text("""
                    INSERT INTO market_data_sample
                        (ticker, trade_date, open_price, high_price, low_price,
                         close_price, volume, per_ratio, pbr_ratio, roe_ratio)
                    VALUES
                        (:ticker, :trade_date, :open, :high, :low,
                         :close, :volume, :per, :pbr, :roe)
                    ON DUPLICATE KEY UPDATE
                        open_price=:open, high_price=:high, low_price=:low,
                        close_price=:close, volume=:volume,
                        per_ratio=:per, pbr_ratio=:pbr, roe_ratio=:roe
                """), {
                    "ticker": ticker, "trade_date": trade_date,
                    "open":  _to_float(row["Open"]),
                    "high":  _to_float(row["High"]),
                    "low":   _to_float(row["Low"]),
                    "close": close,
                    "volume": int(_to_float(row["Volume"])),
                    "per": per, "pbr": pbr, "roe": roe_val,
                })
            log.info("%s: %d rows", ticker, len(df))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()
    backfill(args.days)