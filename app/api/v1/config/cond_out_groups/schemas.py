"""
工况输出组合管理 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CondOutGroupCreateRequest(BaseModel):
    """创建工况输出组合请求"""
    name: str = Field(..., min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    sort: Optional[int] = Field(100, description="排序")


class CondOutGroupUpdateRequest(BaseModel):
    """更新工况输出组合请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    valid: Optional[int] = Field(None, description="是否有效")
    sort: Optional[int] = Field(None, description="排序")


class CondOutGroupResponse(BaseModel):
    """工况输出组合响应"""
    id: int
    name: str
    description: Optional[str]
    valid: int
    sort: int
    createdAt: int
    updatedAt: int


class AddConditionToGroupRequest(BaseModel):
    """添加工况到组合请求"""
    conditionDefId: int = Field(..., description="工况定义ID")
    configData: Optional[Dict[str, Any]] = Field(None, description="工况配置数据")
    sort: Optional[int] = Field(100, description="排序")


class AddOutputToGroupRequest(BaseModel):
    """添加输出到组合请求"""
    outputDefId: int = Field(..., description="输出定义ID")
    sort: Optional[int] = Field(100, description="排序")


class ConditionInGroupResponse(BaseModel):
    """组合中的工况响应"""
    id: int
    condOutGroupId: int
    conditionDefId: int
    configData: Optional[Dict[str, Any]]
    sort: int
    createdAt: int
    # 工况定义信息
    conditionName: Optional[str] = None
    conditionCode: Optional[str] = None
    conditionSchema: Optional[Dict[str, Any]] = None  # 改名避免与 BaseModel.schema 冲突


class OutputInGroupResponse(BaseModel):
    """组合中的输出响应"""
    id: int
    condOutGroupId: int
    outputDefId: int
    sort: int
    createdAt: int
    # 输出定义信息
    outputName: Optional[str] = None
    outputCode: Optional[str] = None
    unit: Optional[str] = None
    valType: Optional[int] = None


class CondOutGroupDetailResponse(BaseModel):
    """工况输出组合详情响应（包含工况和输出列表）"""
    id: int
    name: str
    description: Optional[str]
    valid: int
    sort: int
    createdAt: int
    updatedAt: int
    conditions: List[ConditionInGroupResponse] = []
    outputs: List[OutputInGroupResponse] = []

