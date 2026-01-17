"""
提单初始化 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class OrderInitConfigRequest(BaseModel):
    """提单初始化配置请求"""
    projectId: int = Field(..., description="项目ID")
    simTypeId: Optional[int] = Field(None, description="仿真类型ID，不传则使用项目默认")


class ParamConfigResponse(BaseModel):
    """参数配置响应"""
    paramDefId: int
    paramName: str
    paramKey: str
    defaultValue: Optional[str]
    unit: Optional[str]
    valType: int
    required: int


class ConditionConfigResponse(BaseModel):
    """工况配置响应"""
    conditionDefId: int
    conditionName: str
    conditionCode: str
    configData: Optional[Dict[str, Any]]
    conditionSchema: Optional[Dict[str, Any]]


class OutputConfigResponse(BaseModel):
    """输出配置响应"""
    outputDefId: int
    outputName: str
    outputCode: str
    unit: Optional[str]
    valType: int


class SolverConfigResponse(BaseModel):
    """求解器配置响应"""
    solverId: int
    solverName: str
    solverCode: str
    solverVersion: Optional[str]


class ParamGroupOptionResponse(BaseModel):
    """参数组合选项响应"""
    paramGroupId: int
    paramGroupName: str
    isDefault: int
    params: List[ParamConfigResponse]


class CondOutGroupOptionResponse(BaseModel):
    """工况输出组合选项响应"""
    condOutGroupId: int
    condOutGroupName: str
    isDefault: int
    conditions: List[ConditionConfigResponse]
    outputs: List[OutputConfigResponse]


class SolverOptionResponse(BaseModel):
    """求解器选项响应"""
    solverId: int
    solverName: str
    solverCode: str
    solverVersion: Optional[str]
    isDefault: int


class OrderInitConfigResponse(BaseModel):
    """提单初始化配置响应"""
    projectId: int
    projectName: str
    simTypeId: int
    simTypeName: str
    simTypeCode: str
    
    # 默认配置
    defaultParamGroup: Optional[ParamGroupOptionResponse]
    defaultCondOutGroup: Optional[CondOutGroupOptionResponse]
    defaultSolver: Optional[SolverConfigResponse]
    
    # 所有可选配置
    paramGroupOptions: List[ParamGroupOptionResponse]
    condOutGroupOptions: List[CondOutGroupOptionResponse]
    solverOptions: List[SolverOptionResponse]

