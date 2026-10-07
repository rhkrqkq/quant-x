import pytest
from app.tools.normalizer import (
    parse_krw, format_krw,
    parse_rate_change,
    parse_quarter, parse_date,
    expand_glossary,
)
from datetime import date


def test_parse_krw_simple():
    assert parse_krw("2조 5,300억원") == pytest.approx(2.53e12)
    assert parse_krw("5,000만원") == 5e7
    assert parse_krw("350조") == 3.5e14
    assert parse_krw("12.3억") == pytest.approx(1.23e9)


def test_format_krw_auto():
    assert format_krw(2.53e12) == "2.53조 원"
    assert format_krw(5e7).endswith("억 원") or format_krw(5e7).endswith("원")


def test_parse_rate_change_bp():
    r = parse_rate_change("35bp 상승")
    assert r.value_pp == pytest.approx(0.35)
    r2 = parse_rate_change("150bp 하락")
    assert r2.value_pp == pytest.approx(-1.50)


def test_parse_rate_change_pp():
    r = parse_rate_change("+2.5%p")
    assert r.value_pp == pytest.approx(2.5)


def test_parse_quarter():
    assert parse_quarter("'25년2분기") == "2025-Q2"
    assert parse_quarter("2024년 4분기") == "2024-Q4"


def test_parse_date_eom():
    assert parse_date("24.03 말") == date(2024, 3, 31)
    assert parse_date("25.6.30") == date(2025, 6, 30)


def test_expand_glossary():
    out = expand_glossary("이 회사는 PER 14배, PBR 1.2배 수준이다.")
    assert "주가수익비율" in out
    assert "주가순자산비율" in out