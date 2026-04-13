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
    FoldType,
    ModelLevel,
    CareDevice,
    SolverResource,
    Department,
    ConditionConfig
)

# 配置关联关系模型
from app.models.config_relations import (
    ParamGroup,
    ParamGroupProjectRel,
    ConditionOutputGroup,
    ProjectSimTypeRel,
    SimTypeParamGroupRel,
    SimTypeCondOutGroupRel,
    SimTypeSolverRel,
    ParamGroupParamRel,
    CondOutGroupConditionRel,
    CondOutGroupOutputRel,
    WorkingCondition,
    FoldTypeSimTypeRel
)

# 订单模型
from app.models.order import (
    Order,
    OrderResult
)
from app.models.case_opti import OrderCaseOpti, CaseConditionOpti

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
from app.models.platform import (
    PlatformSetting,
    Announcement,
    PrivacyPolicyAcceptance,
    TrackingEvent,
)

# 上传模型
from app.models.upload import UploadFile
from app.models.upload_chunk import UploadChunk

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
    'ModelLevel',
    'CareDevice',
    'SolverResource',
    'Department',
    'ConditionConfig',
    # 配置关联关系
    'ParamGroup',
    'ParamGroupProjectRel',
    'ConditionOutputGroup',
    'ProjectSimTypeRel',
    'SimTypeParamGroupRel',
    'SimTypeCondOutGroupRel',
    'SimTypeSolverRel',
    'ParamGroupParamRel',
    'CondOutGroupConditionRel',
    'CondOutGroupOutputRel',
    'WorkingCondition',
    'FoldTypeSimTypeRel',
    # 订单
    'Order',
    'OrderResult',
    'OrderCaseOpti',
    'CaseConditionOpti',
    # 结果
    'SimTypeResult',
    'Round',
    # 权限
    'User',
    'Role',
    'Permission',
    'Menu',
    'PlatformSetting',
    'Announcement',
    'PrivacyPolicyAcceptance',
    'TrackingEvent',
    # 上传
    'UploadFile',
    'UploadChunk'
]
