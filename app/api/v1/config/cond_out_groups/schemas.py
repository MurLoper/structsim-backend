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
    created_at: int
    updated_at: int


class AddConditionToGroupRequest(BaseModel):
    """添加工况到组合请求"""
    condition_def_id: int = Field(..., description="工况定义ID")
    config_data: Optional[Dict[str, Any]] = Field(None, description="工况配置数据")
    sort: Optional[int] = Field(100, description="排序")


class AddOutputToGroupRequest(BaseModel):
    """添加输出到组合请求"""
    output_def_id: int = Field(..., description="输出定义ID")
    sort: Optional[int] = Field(100, description="排序")


class ConditionInGroupResponse(BaseModel):
    """组合中的工况响应"""
    id: int
    cond_out_group_id: int
    condition_def_id: int
    config_data: Optional[Dict[str, Any]]
    sort: int
    created_at: int
    # 工况定义信息
    condition_name: Optional[str] = None
    condition_code: Optional[str] = None
    condition_schema: Optional[Dict[str, Any]] = None


class OutputInGroupResponse(BaseModel):
    """组合中的输出响应"""
    id: int
    cond_out_group_id: int
    output_def_id: int
    sort: int
    created_at: int
    # 输出定义信息
    output_name: Optional[str] = None
    output_code: Optional[str] = None
    unit: Optional[str] = None
    val_type: Optional[int] = None


class CondOutGroupDetailResponse(BaseModel):
    """工况输出组合详情响应（包含工况和输出列表）"""
    id: int
    name: str
    description: Optional[str]
    valid: int
    sort: int
    created_at: int
    updated_at: int
    conditions: List[ConditionInGroupResponse] = []
    outputs: List[OutputInGroupResponse] = []

