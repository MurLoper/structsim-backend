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
    project_id: Optional[int] = Field(None, description="关联项目ID, NULL=全局")
    alg_type: Optional[int] = Field(0, description="算法类型: 0=通用, 1=贝叶斯优化, 2=DOE")
    sort: Optional[int] = Field(100, description="排序")


class CondOutGroupUpdateRequest(BaseModel):
    """更新工况输出组合请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    project_id: Optional[int] = Field(None, description="关联项目ID")
    alg_type: Optional[int] = Field(None, description="算法类型")
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
    """添加输出到组合请求（含 resp_details 预配置）"""
    output_def_id: int = Field(..., description="输出定义ID")
    set_name: Optional[str] = Field('push', description="set集名称，默认push")
    component: Optional[str] = Field('18', description="后处理方式编码，默认 18(Other)")
    step_name: Optional[str] = Field(None, description="分析步名称，特殊输出才需要")
    section_point: Optional[str] = Field(None, description="积分点，特殊输出才需要")
    special_output_set: Optional[str] = Field(None, description="特殊输出set")
    description: Optional[str] = Field(None, description="输出描述")
    weight: Optional[float] = Field(1.0, description="权重")
    multiple: Optional[float] = Field(1.0, description="数量级")
    lower_limit: Optional[float] = Field(0.0, description="下限")
    upper_limit: Optional[float] = Field(None, description="上限")
    target_type: Optional[int] = Field(3, description="1:最大化 2:最小化 3:靠近目标值")
    target_value: Optional[float] = Field(None, description="目标值")
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
    """组合中的输出响应（含 resp_details 预配置）"""
    id: int
    cond_out_group_id: int
    output_def_id: int
    # resp_details 预配置
    set_name: Optional[str] = 'push'
    component: Optional[str] = '18'
    step_name: Optional[str] = None
    section_point: Optional[str] = None
    special_output_set: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = 1.0
    multiple: Optional[float] = 1.0
    lower_limit: Optional[float] = 0.0
    upper_limit: Optional[float] = None
    target_type: Optional[int] = 3
    target_value: Optional[float] = None
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
