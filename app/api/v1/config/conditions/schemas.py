"""
工况配置管理 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ConditionConfigCreateRequest(BaseModel):
    """创建工况配置请求"""
    name: str = Field(..., description="工况名称")
    code: Optional[str] = Field(None, description="工况编码")
    fold_type_id: int = Field(..., description="姿态ID")
    sim_type_id: int = Field(..., description="仿真类型ID")
    param_group_ids: Optional[List[int]] = Field(default=[], description="参数组ID列表")
    output_group_ids: Optional[List[int]] = Field(default=[], description="输出组ID列表")
    default_param_group_id: Optional[int] = Field(None, description="默认参数组ID")
    default_output_group_id: Optional[int] = Field(None, description="默认输出组ID")
    default_solver_id: Optional[int] = Field(None, description="默认求解器ID")
    sort: Optional[int] = Field(100, description="排序")
    remark: Optional[str] = Field(None, description="备注")


class ConditionConfigUpdateRequest(BaseModel):
    """更新工况配置请求"""
    name: Optional[str] = Field(None, description="工况名称")
    code: Optional[str] = Field(None, description="工况编码")
    param_group_ids: Optional[List[int]] = Field(None, description="参数组ID列表")
    output_group_ids: Optional[List[int]] = Field(None, description="输出组ID列表")
    default_param_group_id: Optional[int] = Field(None, description="默认参数组ID")
    default_output_group_id: Optional[int] = Field(None, description="默认输出组ID")
    default_solver_id: Optional[int] = Field(None, description="默认求解器ID")
    valid: Optional[int] = Field(None, description="是否有效")
    sort: Optional[int] = Field(None, description="排序")
    remark: Optional[str] = Field(None, description="备注")


class ConditionConfigResponse(BaseModel):
    """工况配置响应"""
    id: int
    name: str
    code: Optional[str] = None
    fold_type_id: int
    sim_type_id: int
    param_group_ids: Optional[List[int]] = []
    output_group_ids: Optional[List[int]] = []
    default_param_group_id: Optional[int] = None
    default_output_group_id: Optional[int] = None
    default_solver_id: Optional[int] = None
    valid: int
    sort: int
    remark: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
