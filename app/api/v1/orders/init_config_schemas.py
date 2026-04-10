"""
提单项目上下文初始化 schema。
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OrderProjectInitConfigRequest(BaseModel):
    """项目上下文初始化请求。"""

    projectId: int = Field(..., description="项目 ID")
    simTypeId: Optional[int] = Field(None, description="仿真类型 ID，可选")


class ParamConfigResponse(BaseModel):
    paramDefId: int
    paramName: str
    paramKey: str
    defaultValue: Optional[str]
    unit: Optional[str]
    valType: int
    required: int


class ConditionConfigResponse(BaseModel):
    conditionDefId: int
    conditionName: str
    conditionCode: str
    configData: Optional[Dict[str, Any]]
    conditionSchema: Optional[Dict[str, Any]]


class OutputConfigResponse(BaseModel):
    outputDefId: int
    outputName: str
    outputCode: str
    unit: Optional[str]
    valType: int


class SolverConfigResponse(BaseModel):
    solverId: int
    solverName: str
    solverCode: str
    solverVersion: Optional[str]


class ParamGroupOptionResponse(BaseModel):
    paramGroupId: int
    paramGroupName: str
    isDefault: int
    params: List[ParamConfigResponse]


class CondOutGroupOptionResponse(BaseModel):
    condOutGroupId: int
    condOutGroupName: str
    isDefault: int
    conditions: List[ConditionConfigResponse]
    outputs: List[OutputConfigResponse]


class SolverOptionResponse(BaseModel):
    solverId: int
    solverName: str
    solverCode: str
    solverVersion: Optional[str]
    isDefault: int


class PhaseOptionResponse(BaseModel):
    phaseId: int
    phaseName: str


class ResourcePoolOptionResponse(BaseModel):
    id: int
    name: str


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
    """项目上下文初始化响应。"""

    projectId: int
    projectName: str
    simTypeId: Optional[int]
    simTypeName: Optional[str]
    simTypeCode: Optional[str]
    phases: List[PhaseOptionResponse]
    defaultPhaseId: Optional[int]
    participantCandidates: List[ParticipantCandidateResponse]
    resourcePools: List[ResourcePoolOptionResponse]
    defaultResourceId: Optional[int]
    defaultParamGroup: Optional[ParamGroupOptionResponse]
    defaultCondOutGroup: Optional[CondOutGroupOptionResponse]
    defaultSolver: Optional[SolverConfigResponse]
    paramGroupOptions: List[ParamGroupOptionResponse]
    condOutGroupOptions: List[CondOutGroupOptionResponse]
    solverOptions: List[SolverOptionResponse]
