"""3장에서는 InMemory Job Store. 9장에서 DB/Redis로 확장 가능."""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from ..schemas.research import JobStatus


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobStatus] = {}

    def create(self) -> JobStatus:
        job_id = str(uuid.uuid4())
        job = JobStatus(jobId=job_id, status="RUNNING", progress=0.0,
                        currentStep="INITIALIZING")
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> JobStatus | None:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs: Any) -> None:
        job = self._jobs[job_id]
        for k, v in kwargs.items():
            setattr(job, k, v)


job_store = JobStore()


async def run_dummy_research(job_id: str, query: str) -> None:
    """3장에서는 5초간 진행률 흉내. 6장에서 실제 Agent 호출로 교체."""
    steps = [
        (0.2, "RESEARCH"),
        (0.5, "MARKET_ANALYSIS"),
        (0.8, "RISK_REVIEW"),
        (1.0, "REPORT_WRITING"),
    ]
    for progress, step in steps:
        await asyncio.sleep(1.2)
        job_store.update(job_id, progress=progress, currentStep=step)

    dummy_result = {
        "report": {
            "title": f"[Dummy] {query[:30]}... 분석 보고서",
            "summary": "이것은 3장 더미 응답입니다. 실제 멀티 에이전트 분석은 7장에서 구현됩니다.",
            "sections": [
                {"title": "기업 개요", "content": "...", "citations": []},
                {"title": "시장 분석", "content": "...", "citations": []},
            ],
            "disclaimer": "본 보고서는 AI 생성 결과이므로 담당자 확인이 필수입니다.",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
    }
    job_store.update(job_id, status="COMPLETED", progress=1.0, result=dummy_result)