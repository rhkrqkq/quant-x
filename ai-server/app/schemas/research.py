from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ResearchRequest(BaseModel):
    requestId: int
    userId: str
    query: str = Field(..., max_length=4000)
    scope: List[str] = Field(default_factory=list)
    options: Optional[Dict[str, Any]] = None


class JobStatus(BaseModel):
    jobId: str
    status: str                                  # RUNNING, COMPLETED, FAILED
    progress: float = 0.0
    currentStep: Optional[str] = None
    result: Optional[Dict[str, Any]] = None