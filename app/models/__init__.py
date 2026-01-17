"""
数据模型模块
按照 requirement_and_design.md 规范设计
"""

# 配置表模型
from app.models.config import (
    Project,
    SimType,
    ParamDef,
    ParamTplSet,
    ParamTplItem,
    ConditionDef,
    OutputDef,
    CondOutSet,
    Solver,
    Workflow,
    StatusDef,
    AutomationModule,
    FoldType
)

# 配置关联关系模型
from app.models.config_relations import (
    ParamGroup,
    ConditionOutputGroup,
    ProjectSimTypeRel,
    SimTypeParamGroupRel,
    SimTypeCondOutGroupRel,
    SimTypeSolverRel,
    ParamGroupParamRel,
    CondOutGroupConditionRel,
    CondOutGroupOutputRel
)

# 订单模型
from app.models.order import (
    Order,
    OrderResult
)

# 结果模型
from app.models.result import (
    SimTypeResult,
    Round
)

# 权限模型
from app.models.auth import (
    User,
    Role,
    Permission,
    Menu
)

__all__ = [
    # 配置表
    'Project',
    'SimType',
    'ParamDef',
    'ParamTplSet',
    'ParamTplItem',
    'ConditionDef',
    'OutputDef',
    'CondOutSet',
    'Solver',
    'Workflow',
    'StatusDef',
    'AutomationModule',
    'FoldType',
    # 配置关联关系
    'ParamGroup',
    'ConditionOutputGroup',
    'ProjectSimTypeRel',
    'SimTypeParamGroupRel',
    'SimTypeCondOutGroupRel',
    'SimTypeSolverRel',
    'ParamGroupParamRel',
    'CondOutGroupConditionRel',
    'CondOutGroupOutputRel',
    # 订单
    'Order',
    'OrderResult',
    # 结果
    'SimTypeResult',
    'Round',
    # 权限
    'User',
    'Role',
    'Permission',
    'Menu'
]

