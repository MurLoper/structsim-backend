"""
结果分析模块 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RoundsQueryParams(BaseModel):
    """轮次查询参数"""
    page: int = Field(1, ge=1, description="页码")
    pageSize: int = Field(100, ge=1, le=500, description="每页数量，最大500")
    status: Optional[int] = Field(None, description="状态筛选: 1=待处理,2=运行中,3=成功,4=失败")


class SimTypeResultResponse(BaseModel):
    """仿真类型结果响应"""
    id: int
    orderId: int
    simTypeId: int
    simTypeName: str
    status: int
    progress: int
    curNodeId: Optional[int]
    stuckNodeId: Optional[int]
    stuckModuleId: Optional[int]
    bestExists: int
    bestRuleId: Optional[int]
    bestRoundIndex: Optional[int]
    bestMetrics: Optional[Dict[str, Any]]
    totalRounds: int
    completedRounds: int
    failedRounds: int
    createdAt: int
    updatedAt: int


class RoundResponse(BaseModel):
    """轮次响应"""
    id: int
    simTypeResultId: int
    roundIndex: int
    status: int
    progress: int
    paramValues: Optional[Dict[str, Any]]
    conditionConfig: Optional[Dict[str, Any]]
    outputResults: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    errorMsg: Optional[str]
    startedAt: Optional[int]
    finishedAt: Optional[int]
    createdAt: int


class RoundsPaginatedResponse(BaseModel):
    """轮次分页响应"""
    items: List[RoundResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int


class UpdateStatusRequest(BaseModel):
    """更新状态请求"""
    status: int = Field(..., ge=1, le=4, description="状态: 1=待处理,2=运行中,3=成功,4=失败")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    errorMsg: Optional[str] = Field(None, description="错误信息")
