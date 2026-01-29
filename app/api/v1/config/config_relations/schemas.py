"""
配置关联关系管理 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============ 项目-仿真类型关联 ============

class ProjectSimTypeRelCreateRequest(BaseModel):
    """创建项目-仿真类型关联请求"""
    sim_type_id: int = Field(..., description="仿真类型ID")
    is_default: Optional[int] = Field(0, description="是否为默认仿真类型")
    sort: Optional[int] = Field(100, description="排序")


class ProjectSimTypeRelResponse(BaseModel):
    """项目-仿真类型关联响应"""
    id: int
    project_id: int
    sim_type_id: int
    is_default: int
    sort: int
    created_at: int
    # 仿真类型信息
    sim_type_name: Optional[str] = None
    sim_type_code: Optional[str] = None


# ============ 仿真类型-参数组合关联 ============

class SimTypeParamGroupRelCreateRequest(BaseModel):
    """创建仿真类型-参数组合关联请求"""
    param_group_id: int = Field(..., description="参数组合ID")
    is_default: Optional[int] = Field(0, description="是否为默认参数组合")
    sort: Optional[int] = Field(100, description="排序")


class SimTypeParamGroupRelResponse(BaseModel):
    """仿真类型-参数组合关联响应"""
    id: int
    sim_type_id: int
    param_group_id: int
    is_default: int
    sort: int
    created_at: int
    # 参数组合信息
    param_group_name: Optional[str] = None
    param_group_description: Optional[str] = None


# ============ 仿真类型-工况输出组合关联 ============

class SimTypeCondOutGroupRelCreateRequest(BaseModel):
    """创建仿真类型-工况输出组合关联请求"""
    cond_out_group_id: int = Field(..., description="工况输出组合ID")
    is_default: Optional[int] = Field(0, description="是否为默认工况输出组合")
    sort: Optional[int] = Field(100, description="排序")


class SimTypeCondOutGroupRelResponse(BaseModel):
    """仿真类型-工况输出组合关联响应"""
    id: int
    sim_type_id: int
    cond_out_group_id: int
    is_default: int
    sort: int
    created_at: int
    # 工况输出组合信息
    cond_out_group_name: Optional[str] = None
    cond_out_group_description: Optional[str] = None


# ============ 仿真类型-求解器关联 ============

class SimTypeSolverRelCreateRequest(BaseModel):
    """创建仿真类型-求解器关联请求"""
    solver_id: int = Field(..., description="求解器ID")
    is_default: Optional[int] = Field(0, description="是否为默认求解器")
    sort: Optional[int] = Field(100, description="排序")


class SimTypeSolverRelResponse(BaseModel):
    """仿真类型-求解器关联响应"""
    id: int
    sim_type_id: int
    solver_id: int
    is_default: int
    sort: int
    created_at: int
    # 求解器信息
    solver_name: Optional[str] = None
    solver_code: Optional[str] = None
    solver_version: Optional[str] = None


# ============ 设置默认配置请求 ============

class SetDefaultRequest(BaseModel):
    """设置默认配置请求"""
    is_default: int = Field(1, description="是否为默认，1=是，0=否")

