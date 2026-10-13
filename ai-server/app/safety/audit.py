"""감사 기록. audit_log · guardrail_event · agent_tool_call_log 세 테이블에 쓴다.

원칙 세 가지다.
① **기록이 실패해도 본래 작업은 계속한다.** 7장 execution_store, 8장 mock_core_log와 같다.
   감사 실패로 서비스가 멈추면 감사가 장애 원인이 된다. 대신 실패 사실은 로그에 남긴다.
② **원문은 저장하지 않는다.** 텍스트는 SHA-256 해시로, Tool 인자도 해시로 남긴다.
   주민번호를 걸러 낸 기록에 주민번호가 들어 있으면 필터를 만든 의미가 없다.
③ **전용 커넥션으로만 쓴다.** INSERT·SELECT만 가진 `quantx_audit` 계정이라
   이 경로로는 감사 로그를 고칠 수 없다.
"""
from __future__ import annotations
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from ..config import settings
from ..schemas.guardrail import GuardrailResult
from .context import get_execution_id, get_request_uid

logger = logging.getLogger(__name__)

_audit_engine: Optional[Engine] = None


def get_audit_engine() -> Engine:
    """감사 기록 전용 엔진.

    `tools/db.py`의 엔진을 재사용하지 않는다. 그쪽은 애플리케이션 계정이라 UPDATE·DELETE가
    되고, 그 커넥션으로 감사 로그를 쓰면 "고칠 수 있는 경로로 기록한다"는 뜻이 된다.
    쓰는 경로와 고칠 수 있는 경로를 나누는 것이 이 분리의 전부다.
    """
    global _audit_engine
    if _audit_engine is None:
        _audit_engine = sa.create_engine(
            settings.mariadb_audit_url, pool_pre_ping=True, future=True)
    return _audit_engine


def sha256(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def record_audit(type_: str, *, user_id: Optional[str] = None,
                 agent_id: Optional[str] = None, request_id: Optional[int] = None,
                 payload: Optional[Dict[str, Any]] = None) -> None:
    """audit_log 한 줄. payload에는 요약만 넣는다 — 원문·PII는 넣지 않는다."""
    body = json.dumps(payload or {}, ensure_ascii=False)
    try:
        with get_audit_engine().begin() as conn:
            conn.execute(sa.text("""
                INSERT INTO audit_log
                    (type, request_uid, user_id, agent_id, request_id,
                     payload_json, payload_hash)
                VALUES
                    (:type, :uid, :user_id, :agent_id, :request_id,
                     :payload, :payload_hash)
            """), {
                "type": type_, "uid": get_request_uid(), "user_id": user_id,
                "agent_id": agent_id, "request_id": request_id,
                "payload": body, "payload_hash": sha256(body),
            })
    except Exception as e:
        # 트레이스백은 남기지 않는다. 요청마다 도는 자리라 DB가 내려가 있으면 로그가 스택으로 덮인다
        logger.error("audit_log 기록 실패: type=%s (%s: %s)", type_, type(e).__name__, e)


def record_guardrail(kind: str, result: GuardrailResult, original_text: str, *,
                     user_id: Optional[str] = None, agent_id: Optional[str] = None,
                     request_id: Optional[int] = None) -> None:
    """guardrail_event 한 줄. kind는 INPUT 또는 OUTPUT."""
    try:
        with get_audit_engine().begin() as conn:
            conn.execute(sa.text("""
                INSERT INTO guardrail_event
                    (type, severity, request_uid, user_id, agent_id, request_id,
                     detected_issues, payload_hash, filtered_text, blocked)
                VALUES
                    (:type, :severity, :uid, :user_id, :agent_id, :request_id,
                     :issues, :payload_hash, :filtered, :blocked)
            """), {
                "type": kind, "severity": result.riskLevel, "uid": get_request_uid(),
                "user_id": user_id, "agent_id": agent_id, "request_id": request_id,
                "issues": json.dumps(result.detectedIssues, ensure_ascii=False),
                # 원본은 해시만. 마스킹을 마친 filtered_text는 남겨도 된다
                "payload_hash": sha256(original_text),
                "filtered": result.filteredText[:60000],
                "blocked": result.shouldBlock,
            })
    except Exception as e:
        logger.error("guardrail_event 기록 실패: type=%s (%s: %s)", kind, type(e).__name__, e)

    if result.shouldBlock:
        record_audit("GUARDRAIL_BLOCKED", user_id=user_id, agent_id=agent_id,
                     request_id=request_id,
                     payload={"kind": kind, "issues": result.detectedIssues})


def record_tool_call(*, tool_name: str, agent_id: str, user_id: str,
                     scope: List[str], scope_pass: bool, params: Dict[str, Any],
                     result_summary: str, duration_ms: int,
                     error: Optional[str]) -> None:
    """agent_tool_call_log 한 줄. 7장까지 메모리에 있던 기록이 여기로 온다.

    execution_id는 contextvar에서 가져온다. Worker가 아니라 `/ai/tools/{name}/invoke`로
    직접 부른 경우에는 실행 자체가 없으므로 NULL이 된다.
    """
    try:
        with get_audit_engine().begin() as conn:
            conn.execute(sa.text("""
                INSERT INTO agent_tool_call_log
                    (request_uid, execution_id, agent_id, user_id, tool_name,
                     scope_json, scope_pass, params_hash, result_summary,
                     duration_ms, error_message)
                VALUES
                    (:uid, :execution_id, :agent_id, :user_id, :tool_name,
                     :scope, :scope_pass, :params_hash, :summary,
                     :duration_ms, :error)
            """), {
                "uid": get_request_uid(), "execution_id": get_execution_id(),
                "agent_id": agent_id, "user_id": user_id, "tool_name": tool_name,
                "scope": json.dumps(scope, ensure_ascii=False),
                "scope_pass": scope_pass,
                "params_hash": sha256(json.dumps(params, ensure_ascii=False,
                                                 sort_keys=True, default=str)),
                "summary": (result_summary or "")[:60000],
                "duration_ms": duration_ms, "error": error,
            })
    except Exception as e:
        logger.error("agent_tool_call_log 기록 실패: tool=%s (%s: %s)",
                     tool_name, type(e).__name__, e)