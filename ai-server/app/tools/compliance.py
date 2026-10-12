"""보고서 초안에서 규정 위반 후보를 찾는 규칙 기반 검사.
LLM을 쓰지 않으므로 같은 입력에는 항상 같은 결과가 나온다.
9장 Output Filter의 앞단계다.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple

_RULES: List[Tuple[str, str, str]] = [
    ("GUARANTEE",
     r"(수익|원금)[^.\n]{0,10}(보장|확실|틀림없)",
     "수익·원금 보장으로 읽힐 수 있는 표현"),
    ("RECOMMEND",
     r"(매수|매도)\s*(추천|권장|하세요|하시기)|(사|팔)(세요|야 한다|아야 한다)",
     "매매 권유로 읽힐 수 있는 표현"),
    ("CERTAIN",
     r"(반드시|무조건|확실히)[^.\n]{0,10}(상승|하락|오를|내릴|급등|급락)",
     "단정적 전망"),
]

_NUMBER_RE = re.compile(r"\d[\d,]*\.?\d*\s*(원|%|배|억|조)")


def check_compliance_rules(text: str, citation_count: int = 0) -> Dict[str, Any]:
    """초안 텍스트에서 규정 위반 후보를 찾는다.
    Scope 검사는 Tool Gateway가 이미 마쳤으므로 여기서는 텍스트만 본다.
    """
    issues: List[Dict[str, str]] = []

    for code, pattern, message in _RULES:
        for m in re.finditer(pattern, text):
            start = max(0, m.start() - 15)
            issues.append({
                "code": code,
                "message": message,
                "snippet": text[start:m.end() + 15].replace("\n", " "),
            })

    # 수치를 제시하면서 인용이 하나도 없으면 근거 없는 단정으로 본다
    if citation_count == 0 and _NUMBER_RE.search(text):
        issues.append({
            "code": "NO_SOURCE",
            "message": "수치를 제시했지만 인용이 하나도 없다",
            "snippet": "",
        })

    return {"passed": not issues, "issues": issues[:10]}