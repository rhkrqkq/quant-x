"""Input Filter — 사용자 질문이 LLM에 닿기 전에 거른다.

순서는 마스킹 → 인젝션 탐지다. 반대로 하면 인젝션 패턴이 계좌번호를 품고 있을 때
탐지 결과 문자열에 원본 PII가 섞여 들어간다. 거른 기록에 거를 대상이 남으면 안 된다.

[보안] 마스킹은 '지우는 것'이지 '복원 가능한 치환'이 아니다. 되돌릴 수 있게 만들면
       그 매핑 테이블이 곧 유출 경로가 된다.
"""
from __future__ import annotations
import logging
import re
from typing import List, Tuple

from ..schemas.guardrail import GuardrailResult
from .moderation import get_moderation_checker
from .patterns import BLOCKING_INJECTION_CODES, INJECTION_PATTERNS, PII_PATTERNS

logger = logging.getLogger(__name__)


def mask_pii(text: str) -> Tuple[str, List[str]]:
    """PII를 마스킹 태그로 바꾸고 무엇을 찾았는지 돌려준다.

    예외 패턴에 걸리는 매치는 건드리지 않는다 (계좌번호 정규식이 삼키는 날짜 등).
    """
    issues: List[str] = []
    masked = text

    for code, pattern, tag, exempt in PII_PATTERNS:
        def _sub(m: "re.Match[str]", _tag=tag, _code=code, _exempt=exempt) -> str:
            if _exempt is not None and _exempt.match(m.group(0)):
                return m.group(0)
            issues.append(f"PII_DETECTED:{_code}")
            return _tag

        masked = pattern.sub(_sub, masked)

    return masked, issues


def detect_injection(text: str) -> List[str]:
    """Prompt Injection 후보를 찾는다. 원문 기준이 아니라 마스킹된 텍스트를 넣는다."""
    return [f"INJECTION:{code}" for code, pattern, _ in INJECTION_PATTERNS
            if pattern.search(text)]


def check_input(text: str) -> GuardrailResult:
    """입력 한 건을 판정한다. 기록은 부르는 쪽(audit)이 남긴다.

    판정 규칙:
    - PII가 하나라도 있으면 BLOCKED. 금융권에서 개인신용정보는 마스킹했다고 보내도 되는 게 아니라
      애초에 나가면 안 되는 값이다 (신용정보법 제40조의2, 부록 A §4.1)
    - Injection은 코드에 따라 갈린다. 지시 무시·프롬프트 노출·역할 태그는 BLOCKED,
      나머지는 WARNING으로 통과시킨다. 오탐으로 정상 질문까지 막으면 아무도 안 쓴다
    """
    masked, pii_issues = mask_pii(text)
    injection_issues = detect_injection(masked)
    issues = pii_issues + injection_issues

    blocking_injection = [i for i in injection_issues
                          if i.split(":", 1)[1] in BLOCKING_INJECTION_CODES]
    should_block = bool(pii_issues) or bool(blocking_injection)

    if should_block:
        risk = "BLOCKED"
    elif issues:
        risk = "WARNING"
    else:
        risk = "SAFE"

    moderation = get_moderation_checker().check(masked)

    # Moderation이 켜져 있고 flagged면 판정을 올린다. 규칙이 못 잡는 것을 모델이 잡는 자리다
    if moderation and moderation.get("flagged"):
        issues.append("MODERATION_FLAGGED")
        risk, should_block = "BLOCKED", True

    return GuardrailResult(
        isSafe=(risk == "SAFE"),
        riskLevel=risk,
        detectedIssues=issues,
        filteredText=masked,
        shouldBlock=should_block,
        moderation=moderation,
    )