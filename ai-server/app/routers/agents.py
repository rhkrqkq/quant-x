"""개발/디버깅용 Agent 직접 실행 엔드포인트.
운영에서는 /ai/research를 통해서만 호출된다. 9장에서 Senior 권한으로 제한한다.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..agents.definitions import AGENTS, get_agent
from ..deps import require_user_id, verify_internal_key
from ..llm.call_log import llm_call_log
from ..schemas.agent import AgentResult, AgentRunRequest

router = APIRouter(prefix="/ai/agents", tags=["agents"])


@router.get("/", dependencies=[Depends(verify_internal_key)])
def list_agents() -> List[Dict[str, Any]]:
    return [
        {"agentId": a.agent_id, "description": a.description, "tools": a.tool_names}
        for a in AGENTS.values()
    ]


@router.post("/{agent_id}/run", dependencies=[Depends(verify_internal_key)],
             response_model=AgentResult)
async def run_agent(
    agent_id: str,
    req: AgentRunRequest,
    user_id: str = Depends(require_user_id),) -> AgentResult:
    agent = get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return await agent.run(req.query, user_id=user_id, scope=req.scope)


@router.get("/llm-calls/recent", dependencies=[Depends(verify_internal_key)])
def recent_llm_calls() -> List[Dict[str, Any]]:
    """LLM 호출 기록. 5장의 /ai/tools/calls/recent 와 짝을 이뢬다.
    10장에서 /ai/llm/calls/recent 로 이관하고 provider별 비용·지연 비교에 사용한다.
    """
    return [r.__dict__ for r in llm_call_log.recent()]