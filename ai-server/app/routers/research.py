from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from ..deps import verify_internal_key, require_user_id
from ..schemas.research import ResearchRequest, JobStatus
from ..services.job_store import job_store
from ..config import settings
from ..agents.runner import run_agent_research
from ..graph.execution_store import list_executions          # ← 7장 추가

router = APIRouter(prefix="/ai", tags=["research"])


@router.post(
    "/research",
    response_model=JobStatus,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_internal_key)],)
async def start_research(
    req: ResearchRequest,
    background: BackgroundTasks,
    user_id: str = Depends(require_user_id),) -> JobStatus:
    if settings.kill_switch_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kill Switch is active",
        )
    job = job_store.create()
    # 실행 이력에 남길 requestId를 다섯 번째 인자로 더한다      # ← 7장 추가
    background.add_task(run_agent_research, job.jobId, req.query,
                        user_id, req.scope, req.requestId)
    return job


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatus,
    dependencies=[Depends(verify_internal_key)],)
async def get_job(job_id: str) -> JobStatus:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    job.agentExecutions = list_executions(job_id)             # ← 7장 추가
    return job