"""
参数组合管理 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ParamGroupCreateRequest(BaseModel):
    """创建参数组合请求"""
    name: str = Field(..., min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    sort: Optional[int] = Field(100, description="排序")


class ParamGroupUpdateRequest(BaseModel):
    """更新参数组合请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    valid: Optional[int] = Field(None, description="是否有效")
    sort: Optional[int] = Field(None, description="排序")


class ParamGroupResponse(BaseModel):
    """参数组合响应"""
    id: int
    name: str
    description: Optional[str]
    valid: int
    sort: int
    createdAt: int
    updatedAt: int


class AddParamToGroupRequest(BaseModel):
    """添加参数到组合请求"""
    paramDefId: int = Field(..., description="参数定义ID")
    defaultValue: Optional[str] = Field(None, max_length=200, description="默认值")
    sort: Optional[int] = Field(100, description="排序")


class ParamInGroupResponse(BaseModel):
    """组合中的参数响应"""
    id: int
    paramGroupId: int
    paramDefId: int
    defaultValue: Optional[str]
    sort: int
    createdAt: int
    # 参数定义信息
    paramName: Optional[str] = None
    paramKey: Optional[str] = None
    unit: Optional[str] = None
    valType: Optional[int] = None


class ParamGroupDetailResponse(BaseModel):
    """参数组合详情响应（包含参数列表）"""
    id: int
    name: str
    description: Optional[str]
    valid: int
    sort: int
    createdAt: int
    updatedAt: int
    params: List[ParamInGroupResponse] = []

