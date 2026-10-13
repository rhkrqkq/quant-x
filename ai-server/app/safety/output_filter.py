"""Output Filter — 보고서가 사용자에게 나가기 전에 거른다.

규칙은 새로 쓰지 않는다. 7장에서 만든 `tools/compliance.py`가 이미 같은 표현을
잡고 있고, 그 파일 주석에도 "9장 Output Filter의 앞단계다"라고 적어 뒀다.
차이는 쓰이는 자리다.

| | 7장 compliance | 9장 Output Filter |
| 부르는 쪽 | Risk Reviewer(Agent) | 파이프라인 |
| 시점 | 초안 검토 중 | 사용자에게 나가기 직전 |
| 결과 | 지적 목록 → 반려 여부 | 차단 · 마스킹 · 재작성 판정 |

Agent가 검토를 건너뛰거나 지적을 무시해도 이쪽은 무조건 돈다.
**7장에서 배운 것 — 프롬프트는 지시이지 보장이 아니다.**
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Tuple

from ..schemas.guardrail import GuardrailResult
from ..tools.compliance import check_compliance_rules
from .moderation import get_moderation_checker

logger = logging.getLogger(__name__)

DISCLAIMER = "본 보고서는 AI 생성 결과이므로 담당자 확인이 필수입니다."

# 부록 A §6.1 정책 규칙 테이블 → 조치 매핑.
# compliance.py가 코드를 내고, 무엇을 할지는 여기서 정한다
_ACTION = {
    "GUARANTEE": "BLOCK",     # 불법 권유 — 수익·원금 보장
    "RECOMMEND": "BLOCK",     # 특정 종목 매매 권유
    "CERTAIN": "REWRITE",     # 과도한 확신 — 완화 표현으로
    "NO_SOURCE": "WARN",      # 근거 없는 수치
}

# 내부등급은 차단이 아니라 마스킹이다. 문장 전체를 버리면 나머지 분석까지 날아간다
_GRADE_RE = re.compile(r"(내부\s*등급|신용\s*등급|리스크\s*등급)\s*:?\s*[0-9A-Fa-f]{1,2}\s*등급?")
_GRADE_MASK = "[GRADE_MASKED]"


def mask_internal_grade(text: str) -> Tuple[str, List[str]]:
    if not _GRADE_RE.search(text):
        return text, []
    return _GRADE_RE.sub(_GRADE_MASK, text), ["INTERNAL_GRADE"]


def check_output(text: str, citation_count: int = 0) -> GuardrailResult:
    """출력 한 건을 판정한다.

    BLOCK이 하나라도 있으면 통째로 막는다. 문제 문장만 지우면 앞뒤 맥락이 어긋나
    "왜 이 결론인가"를 설명할 수 없는 보고서가 남는다.
    """
    masked, issues = mask_internal_grade(text)

    rule_result = check_compliance_rules(masked, citation_count=citation_count)
    codes = [i["code"] for i in rule_result["issues"]]
    issues.extend(codes)

    actions = {_ACTION.get(c, "WARN") for c in codes}
    should_block = "BLOCK" in actions
    should_rewrite = "REWRITE" in actions

    if should_block:
        risk = "BLOCKED"
    elif issues:
        risk = "WARNING"
    else:
        risk = "SAFE"

    moderation = get_moderation_checker().check(masked)
    if moderation and moderation.get("flagged"):
        issues.append("MODERATION_FLAGGED")
        risk, should_block = "BLOCKED", True

    return GuardrailResult(
        isSafe=(risk == "SAFE"),
        riskLevel=risk,
        detectedIssues=issues,
        filteredText=masked,
        shouldBlock=should_block,
        shouldRewrite=should_rewrite,
        moderation=moderation,
    )


def filter_report(report: Dict[str, Any]) -> Tuple[Dict[str, Any], GuardrailResult]:
    """보고서 본문을 걸러 (거른 보고서, 판정)을 돌려준다.

    차단된 보고서는 본문을 지우고 안내 문구로 바꾼다. 사용자에게 "왜 안 나오는지"는
    알려 주되 무엇이 걸렸는지는 상세히 보이지 않는다 — 그 목록 자체가 우회 힌트가 된다.
    """
    body = report.get("body") or ""
    result = check_output(body, citation_count=len(report.get("citations") or []))

    out = dict(report)
    if result.shouldBlock:
        out["body"] = ("규정 검사에서 걸러진 내용이 있어 보고서를 표시할 수 없습니다. "
                       "담당자에게 문의해 주세요.")
        out["blocked"] = True
    else:
        out["body"] = result.filteredText
        out["blocked"] = False

    out["guardrail"] = {
        "riskLevel": result.riskLevel,
        "detectedIssues": result.detectedIssues,
        "shouldRewrite": result.shouldRewrite,
    }

    # 면책 고지는 write_node가 이미 넣지만, 없으면 여기서 붙인다.
    # 통제는 앞단이 해 줬을 거라고 믿지 않는 편이 낫다 (부록 A §6)
    if not out.get("disclaimer"):
        out["disclaimer"] = DISCLAIMER

    return out, result