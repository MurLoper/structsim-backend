"""
配置关联关系管理 - Pydantic Schemas
职责：请求/响应数据校验
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============ 项目-仿真类型关联 ============

class ProjectSimTypeRelCreateRequest(BaseModel):
    """创建项目-仿真类型关联请求"""
    simTypeId: int = Field(..., description="仿真类型ID")
    isDefault: Optional[int] = Field(0, description="是否为默认仿真类型")
    sort: Optional[int] = Field(100, description="排序")


class ProjectSimTypeRelResponse(BaseModel):
    """项目-仿真类型关联响应"""
    id: int
    projectId: int
    simTypeId: int
    isDefault: int
    sort: int
    createdAt: int
    # 仿真类型信息
    simTypeName: Optional[str] = None
    simTypeCode: Optional[str] = None


# ============ 仿真类型-参数组合关联 ============

class SimTypeParamGroupRelCreateRequest(BaseModel):
    """创建仿真类型-参数组合关联请求"""
    paramGroupId: int = Field(..., description="参数组合ID")
    isDefault: Optional[int] = Field(0, description="是否为默认参数组合")
    sort: Optional[int] = Field(100, description="排序")


class SimTypeParamGroupRelResponse(BaseModel):
    """仿真类型-参数组合关联响应"""
    id: int
    simTypeId: int
    paramGroupId: int
    isDefault: int
    sort: int
    createdAt: int
    # 参数组合信息
    paramGroupName: Optional[str] = None
    paramGroupDescription: Optional[str] = None


# ============ 仿真类型-工况输出组合关联 ============

class SimTypeCondOutGroupRelCreateRequest(BaseModel):
    """创建仿真类型-工况输出组合关联请求"""
    condOutGroupId: int = Field(..., description="工况输出组合ID")
    isDefault: Optional[int] = Field(0, description="是否为默认工况输出组合")
    sort: Optional[int] = Field(100, description="排序")


class SimTypeCondOutGroupRelResponse(BaseModel):
    """仿真类型-工况输出组合关联响应"""
    id: int
    simTypeId: int
    condOutGroupId: int
    isDefault: int
    sort: int
    createdAt: int
    # 工况输出组合信息
    condOutGroupName: Optional[str] = None
    condOutGroupDescription: Optional[str] = None


# ============ 仿真类型-求解器关联 ============

class SimTypeSolverRelCreateRequest(BaseModel):
    """创建仿真类型-求解器关联请求"""
    solverId: int = Field(..., description="求解器ID")
    isDefault: Optional[int] = Field(0, description="是否为默认求解器")
    sort: Optional[int] = Field(100, description="排序")


class SimTypeSolverRelResponse(BaseModel):
    """仿真类型-求解器关联响应"""
    id: int
    simTypeId: int
    solverId: int
    isDefault: int
    sort: int
    createdAt: int
    # 求解器信息
    solverName: Optional[str] = None
    solverCode: Optional[str] = None
    solverVersion: Optional[str] = None


# ============ 设置默认配置请求 ============

class SetDefaultRequest(BaseModel):
    """设置默认配置请求"""
    isDefault: int = Field(1, description="是否为默认，1=是，0=否")

