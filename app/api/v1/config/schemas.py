"""
配置中心 - Pydantic Schema定义
用于请求参数校验和响应数据序列化
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


# ============ 项目配置 ============
class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    code: Optional[str] = Field(None, max_length=50, description="项目编码")
    default_sim_type_id: Optional[int] = Field(None, description="默认仿真类型ID")
    default_solver_id: Optional[int] = Field(None, description="默认求解器ID")
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    default_sim_type_id: Optional[int] = None
    default_solver_id: Optional[int] = None
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 仿真类型 ============
class SimTypeCreate(BaseModel):
    """创建仿真类型请求"""
    name: str = Field(..., min_length=1, max_length=100, description="仿真类型名称")
    code: Optional[str] = Field(None, max_length=50, description="类型编码")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    support_alg_mask: int = Field(default=3, ge=0, description="支持算法位掩码")
    node_icon: Optional[str] = Field(None, max_length=50)
    color_tag: Optional[str] = Field(None, max_length=20)
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class SimTypeUpdate(BaseModel):
    """更新仿真类型请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    support_alg_mask: Optional[int] = Field(None, ge=0)
    node_icon: Optional[str] = None
    color_tag: Optional[str] = None
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 参数定义 ============
class ParamDefCreate(BaseModel):
    """创建参数定义请求"""
    name: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=50)
    val_type: int = Field(default=1, ge=1, le=5, description="1=float,2=int,3=string,4=enum,5=bool")
    unit: Optional[str] = Field(None, max_length=20)
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    default_val: Optional[str] = None
    precision: int = Field(default=3, ge=0, le=10)
    enum_options: Optional[List[Any]] = None
    required: int = Field(default=1, ge=0, le=1)
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None

    @field_validator('max_val')
    @classmethod
    def validate_max_val(cls, v, info):
        min_val = info.data.get('min_val')
        if v is not None and min_val is not None and v < min_val:
            raise ValueError('max_val must be >= min_val')
        return v


class ParamDefUpdate(BaseModel):
    """更新参数定义请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    key: Optional[str] = Field(None, min_length=1, max_length=50)
    val_type: Optional[int] = Field(None, ge=1, le=5, alias='valType')
    unit: Optional[str] = None
    min_val: Optional[float] = Field(None, alias='minVal')
    max_val: Optional[float] = Field(None, alias='maxVal')
    default_val: Optional[str] = Field(None, alias='defaultVal')
    precision: Optional[int] = Field(None, ge=0, le=10)
    enum_options: Optional[List[Any]] = Field(None, alias='enumOptions')
    required: Optional[int] = Field(None, ge=0, le=1)
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None

    class Config:
        populate_by_name = True  # 允许使用字段名或别名


# ============ 求解器 ============
class SolverCreate(BaseModel):
    """创建求解器请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    version: Optional[str] = Field(None, max_length=20)
    cpu_core_min: int = Field(default=1, ge=1)
    cpu_core_max: int = Field(default=256, ge=1)
    cpu_core_default: int = Field(default=16, ge=1)
    memory_min: int = Field(default=1, ge=1)
    memory_max: int = Field(default=1024, ge=1)
    memory_default: int = Field(default=64, ge=1)
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class SolverUpdate(BaseModel):
    """更新求解器请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    version: Optional[str] = None
    cpu_core_min: Optional[int] = Field(None, ge=1)
    cpu_core_max: Optional[int] = Field(None, ge=1)
    cpu_core_default: Optional[int] = Field(None, ge=1)
    memory_min: Optional[int] = Field(None, ge=1)
    memory_max: Optional[int] = Field(None, ge=1)
    memory_default: Optional[int] = Field(None, ge=1)
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 工况定义 ============
class ConditionDefCreate(BaseModel):
    """创建工况定义请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = None
    unit: Optional[str] = None
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class ConditionDefUpdate(BaseModel):
    """更新工况定义请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 输出定义 ============
class OutputDefCreate(BaseModel):
    """创建输出定义请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = None
    val_type: int = Field(default=1, ge=1, le=3)  # 1=number,2=int,3=string
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class OutputDefUpdate(BaseModel):
    """更新输出定义请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    unit: Optional[str] = None
    val_type: Optional[int] = Field(None, ge=1, le=3)
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 姿态类型 ============
class FoldTypeCreate(BaseModel):
    """创建姿态类型请求"""
    name: str = Field(..., min_length=1, max_length=50)
    code: Optional[str] = Field(None, max_length=30)
    angle: int = Field(default=0)
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class FoldTypeUpdate(BaseModel):
    """更新姿态类型请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = None
    angle: Optional[int] = None
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 模型层级 ============
class ModelLevelCreate(BaseModel):
    """创建模型层级请求"""
    name: str = Field(..., min_length=1, max_length=50)
    code: Optional[str] = Field(None, max_length=20)
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class ModelLevelUpdate(BaseModel):
    """更新模型层级请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = None
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 关注器件 ============
class CareDeviceCreate(BaseModel):
    """创建关注器件请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    sort: int = Field(default=100, ge=0)
    remark: Optional[str] = None


class CareDeviceUpdate(BaseModel):
    """更新关注器件请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    category: Optional[str] = None
    sort: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


# ============ 求解器资源池 ============
class SolverResourceCreate(BaseModel):
    """创建求解器资源池请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    cpu_cores: Optional[int] = Field(None, ge=1)
    memory_gb: Optional[int] = Field(None, ge=1)
    sort: int = Field(default=100, ge=0)


class SolverResourceUpdate(BaseModel):
    """更新求解器资源池请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    description: Optional[str] = None
    cpu_cores: Optional[int] = Field(None, ge=1)
    memory_gb: Optional[int] = Field(None, ge=1)
    sort: Optional[int] = Field(None, ge=0)


# ============ 部门 ============
class DepartmentCreate(BaseModel):
    """创建部门请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    parent_id: int = Field(default=0, ge=0)
    sort: int = Field(default=100, ge=0)


class DepartmentUpdate(BaseModel):
    """更新部门请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    parent_id: Optional[int] = Field(None, ge=0)
    sort: Optional[int] = Field(None, ge=0)

