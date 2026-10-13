from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, status
from ..deps import verify_internal_key, require_user_id
from ..schemas.research import ResearchRequest, JobStatus
from ..services.job_store import job_store
from ..agents.runner import run_agent_research
from ..graph.execution_store import list_executions      # ← 7장 추가
from ..safety import kill_switch                         # ← 9장 추가
from ..safety.audit import record_guardrail
from ..safety.context import set_request_uid
from ..safety.input_filter import check_input

router = APIRouter(prefix="/ai", tags=["research"])


@router.post(
    "/research",
    response_model=JobStatus,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_internal_key)],)
async def start_research(
    req: ResearchRequest,
    background: BackgroundTasks,
    user_id: str = Depends(require_user_id),
    x_request_id: str = Header(default=""),) -> JobStatus:
    # ① 요청 상관관계 ID를 먼저 심는다. 이후 모든 기록이 이 값을 달고 남는다
    request_uid = set_request_uid(x_request_id or None)

    # ② Kill Switch — 8장까지는 환경변수만 봤다. 이제 DB 상태를 본다
    active, reason = kill_switch.status()
    if active:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "KILL_SWITCH_ACTIVE", "reason": reason},
        )

    # ③ Input Filter — LLM에 닿기 전이다. 여기서 막히면 Agent는 시작조차 하지 않는다
    guard = check_input(req.query)
    record_guardrail("INPUT", guard, req.query, user_id=user_id,
                     request_id=req.requestId)
    if guard.shouldBlock:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "GUARDRAIL_BLOCKED",
                    "detectedIssues": guard.detectedIssues,
                    "requestUid": request_uid},
        )

    # 요청을 냈다는 사실은 Spring Boot가 이미 남겼다. 여기서는 Agent 쪽 기록만 더한다 —
    # 같은 일을 두 서버가 각자 남기면 감사에서 건수가 두 배로 보인다
    job = job_store.create()
    # [주의] BackgroundTasks는 별도 컨텍스트에서 돌기 때문에 contextvar가 따라가지 않는다.
    #        request_uid를 인자로 넘겨 백그라운드 쪽에서 다시 심는다
    #        마스킹을 마친 filteredText를 넘긴다 — 원문이 Agent로 흘러가면 필터를 만든 의미가 없다
    background.add_task(run_agent_research, job.jobId, guard.filteredText, user_id,
                        req.scope, req.requestId, request_uid)
    return job


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatus,
    dependencies=[Depends(verify_internal_key)],)
async def get_job(job_id: str) -> JobStatus:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    job.agentExecutions = list_executions(job_id)
    return job