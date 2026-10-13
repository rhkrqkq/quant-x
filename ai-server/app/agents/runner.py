from ..graph.build import get_research_graph
from ..safety.audit import record_audit, record_guardrail          # ← 9장 추가
from ..safety.context import set_request_uid
from ..safety.output_filter import filter_report
from ..services.job_store import job_store


async def run_agent_research(job_id: str, query: str, user_id: str,
                             scope: List[str], request_id: int = 0,
                             request_uid: Optional[str] = None) -> None:
    # 백그라운드 태스크는 새 컨텍스트에서 시작한다. 라우터가 심어 둔 contextvar가
    # 여기까지 따라오지 않으므로 다시 심는다 (9장)
    set_request_uid(request_uid)

    # ... (7장 그래프 실행 부분은 그대로) ...

    # ← 9장: Output Filter. 사용자에게 나가는 마지막 한 지점이다.
    #   그래프 안이 아니라 여기서 거는 이유가 있다. 반려 루프로 write가 몇 번을 돌든
    #   검사는 job_store에 넣기 직전 한 번이면 되고, 7장 그래프를 손대지 않아도 된다.
    filtered, guard = filter_report(report)
    record_guardrail("OUTPUT", guard, report.get("body") or "",
                     user_id=user_id, agent_id="report_writer", request_id=request_id)
    record_audit("AGENT_EXECUTION", user_id=user_id, request_id=request_id,
                 payload={"jobId": job_id, "riskLevel": guard.riskLevel,
                          "citations": len(report.get("citations") or [])})

    job_store.update(job_id, status="COMPLETED", progress=1.0,
                     currentStep="DONE", result={"report": filtered})