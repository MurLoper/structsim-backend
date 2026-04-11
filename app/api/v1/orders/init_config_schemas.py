"""
鎻愬崟椤圭洰涓婁笂鏂囧垵濮嬪寲 schema銆?
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class OrderProjectInitConfigRequest(BaseModel):
    """椤圭洰涓婁笂鏂囧垵濮嬪寲璇锋眰銆?"""

    projectId: int = Field(..., description="椤圭洰 ID")


class PhaseOptionResponse(BaseModel):
    phaseId: int
    phaseName: str


class ParticipantCandidateResponse(BaseModel):
    id: str
    domainAccount: str
    userName: Optional[str] = None
    realName: Optional[str] = None
    displayName: Optional[str] = None
    email: Optional[str] = None
    departmentId: Optional[int] = None
    department: Optional[str] = None
    isProjectFrequent: bool = False
    projectFrequency: int = 0
    isCurrentUser: bool = False


class OrderProjectInitConfigResponse(BaseModel):
    """椤圭洰涓婁笂鏂囧垵濮嬪寲鍝嶅簲銆?"""

    projectId: int
    projectName: str
    phases: List[PhaseOptionResponse]
    defaultPhaseId: Optional[int]
    participantCandidates: List[ParticipantCandidateResponse]
