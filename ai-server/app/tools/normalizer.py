"""한국 금융 텍스트 정규화.
원화 단위, bp/%, 분기 표기를 표준 형식으로 변환한다.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


# ============================================================
# 1. 원화 단위 정규화
# ============================================================
_KRW_UNITS = {
    "조": 1_000_000_000_000,
    "억": 100_000_000,
    "천만": 10_000_000,
    "백만": 1_000_000,
    "만": 10_000,
    "K": 1_000,
    "M": 1_000_000,
    "B": 1_000_000_000,
}

_KRW_PATTERN = re.compile(
    r"""(?P<num>[\d,]+(?:\.\d+)?)        # 숫자 (콤마 허용)
        \s*
        (?P<unit>조|억|천만|백만|만|K|M|B)?   # 단위 (옵션)
        \s*
        (?:원|KRW|krw)?                  # 통화 (옵션)
    """,
    re.VERBOSE,
)


def parse_krw(text: str) -> Optional[float]:
    """텍스트에서 첫 번째 원화 금액을 원 단위 float로 파싱.
    예: '2조 5,300억원' → 2.53e12
        '5,000만원' → 5e7
    """
    text = text.strip()
    # 복합 단위 처리: "2조 5,300억"
    total = 0.0
    matched_any = False
    pos = 0
    for m in _KRW_PATTERN.finditer(text):
        if m.start() < pos:
            continue
        num_str = m.group("num").replace(",", "")
        if not num_str:
            continue
        try:
            num = float(num_str)
        except ValueError:
            continue
        unit = m.group("unit")
        multiplier = _KRW_UNITS.get(unit, 1)
        total += num * multiplier
        pos = m.end()
        matched_any = True
    return total if matched_any else None


def format_krw(amount_won: float, unit: str = "auto") -> str:
    """원 단위 → 표시 형식. unit='auto'면 가장 적절한 단위 자동 선택."""
    abs_a = abs(amount_won)
    if unit == "auto":
        if abs_a >= 1e12:
            unit = "조"
        elif abs_a >= 1e8:
            unit = "억"
        else:
            unit = "원"
    if unit == "조":
        return f"{amount_won/1e12:,.2f}조 원"
    if unit == "억":
        return f"{amount_won/1e8:,.0f}억 원"
    return f"{amount_won:,.0f} 원"


# ============================================================
# 2. 금리/스프레드: bp ↔ %p
# ============================================================
_BP_PATTERN = re.compile(
    r"(?P<sign>[+\-]?)\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>bp|%p|%)"
    r"\s*(?P<dir>(?:상승|하락|증가|감소))?",
    re.IGNORECASE,
)


@dataclass
class RateChange:
    value_pp: float                                  # %p 단위 (양수=상승, 음수=하락)

    def __str__(self) -> str:
        sign = "+" if self.value_pp >= 0 else ""
        return f"{sign}{self.value_pp:.2f}%p"


def parse_rate_change(text: str) -> Optional[RateChange]:
    """'35bp 상승' / '-150bp' / '+2.5%p' 등을 RateChange로 정규화.
    %는 %p로 간주 (금리 컨텍스트 가정).
    """
    m = _BP_PATTERN.search(text)
    if not m:
        return None
    num = float(m.group("num"))
    unit = m.group("unit").lower()
    sign = m.group("sign") or "+"
    direction = m.group("dir") or ""

    if unit == "bp":
        pp = num / 100.0                             # 1bp = 0.01%p
    else:
        pp = num                                     # %p와 %는 동일 취급 (주의: 금리 한정)

    if sign == "-" or direction in ("하락", "감소"):
        pp = -abs(pp)
    else:
        pp = abs(pp)
    return RateChange(value_pp=pp)


# ============================================================
# 3. 날짜/분기 표준화
# ============================================================
_QUARTER_PATTERN = re.compile(
    r"""(?:'|′|‘)?(?P<yy>\d{2,4})년?\s*
        (?P<q>[1-4])\s*분기""",
    re.VERBOSE,
)
_DATE_PATTERNS = [
    re.compile(r"(?P<yy>\d{2,4})[.\-/](?P<mm>\d{1,2})[.\-/](?P<dd>\d{1,2})"),
    re.compile(r"(?P<yy>\d{2,4})[.\-/](?P<mm>\d{1,2})\s*말"),
]


def _normalize_year(yy: str) -> int:
    n = int(yy)
    if n < 100:
        # 2자리 연도: 25 → 2025, 99 → 1999 (간단 cutoff: 50)
        return 2000 + n if n < 50 else 1900 + n
    return n


def parse_quarter(text: str) -> Optional[str]:
    """'25년2분기' → '2025-Q2'"""
    m = _QUARTER_PATTERN.search(text)
    if not m:
        return None
    year = _normalize_year(m.group("yy"))
    q = int(m.group("q"))
    return f"{year}-Q{q}"


def parse_date(text: str) -> Optional[date]:
    """'24.03 말' → 2024-03-31, '25.6.30' → 2025-06-30"""
    for pat in _DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        year = _normalize_year(m.group("yy"))
        month = int(m.group("mm"))
        if "dd" in m.groupdict() and m.group("dd"):
            return date(year, month, int(m.group("dd")))
        # 월말 추정
        from calendar import monthrange
        last = monthrange(year, month)[1]
        return date(year, month, last)
    return None


# ============================================================
# 4. 약어/티커 매핑 (사전 데이터는 별도 모듈에서 로드)
# ============================================================
FIN_GLOSSARY: dict[str, str] = {
    "PER": "주가수익비율 (Price/Earnings Ratio)",
    "PBR": "주가순자산비율 (Price/Book Ratio)",
    "EPS": "주당순이익",
    "ROE": "자기자본이익률",
    "ROA": "총자산이익률",
    "NIM": "순이자마진",
    "LTV": "담보인정비율",
    "QoQ": "전분기 대비",
    "YoY": "전년 동기 대비",
    "YTD": "연초 대비",
    "FY":  "회계연도",
}


def expand_glossary(text: str) -> str:
    """텍스트 안의 약어를 풀어쓰기. (LLM 프롬프트 보강용)"""
    out = text
    for abbr, full in FIN_GLOSSARY.items():
        out = re.sub(rf"\b{abbr}\b", f"{abbr}({full})", out)
    return out