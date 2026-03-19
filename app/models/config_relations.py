"""
配置关联关系模型 - 组合配置和中间表
实现灵活的配置组合机制
"""
from datetime import datetime
from app import db
from app.models.base import ToDictMixin


class ParamGroup(db.Model, ToDictMixin):
    """参数组合表 - 将多个参数定义组合成可复用的参数组"""
    __tablename__ = 'param_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='组合名称')
    description = db.Column(db.Text, comment='组合描述')
    valid = db.Column(db.SmallInteger, default=1, comment='1=有效,0=禁用')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))


class ParamGroupProjectRel(db.Model, ToDictMixin):
    """参数组合-项目关联表（多对多）"""
    __tablename__ = 'param_group_project_rels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    param_group_id = db.Column(db.Integer, db.ForeignKey('param_groups.id'), nullable=False, comment='参数组合ID')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='项目ID')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class ConditionOutputGroup(db.Model, ToDictMixin):
    """工况输出组合表 - 将工况和输出组合成可复用的配置组"""
    __tablename__ = 'condition_output_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='组合名称')
    description = db.Column(db.Text, comment='组合描述')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), comment='关联项目ID, NULL=全局')
    alg_type = db.Column(db.SmallInteger, default=0, comment='算法类型: 0=通用, 1=贝叶斯优化, 2=DOE')
    valid = db.Column(db.SmallInteger, default=1, comment='1=有效,0=禁用')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))


class ProjectSimTypeRel(db.Model, ToDictMixin):
    """项目-仿真类型关联表"""
    __tablename__ = 'project_sim_type_rels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='项目ID')
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), nullable=False, comment='仿真类型ID')
    is_default = db.Column(db.SmallInteger, default=0, comment='是否为默认仿真类型')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class SimTypeParamGroupRel(db.Model, ToDictMixin):
    """仿真类型-参数组合关联表"""
    __tablename__ = 'sim_type_param_group_rels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), nullable=False, comment='仿真类型ID')
    param_group_id = db.Column(db.Integer, db.ForeignKey('param_groups.id'), nullable=False, comment='参数组合ID')
    is_default = db.Column(db.SmallInteger, default=0, comment='是否为默认参数组合')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class SimTypeCondOutGroupRel(db.Model, ToDictMixin):
    """仿真类型-工况输出组合关联表"""
    __tablename__ = 'sim_type_cond_out_group_rels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), nullable=False, comment='仿真类型ID')
    cond_out_group_id = db.Column(db.Integer, db.ForeignKey('condition_output_groups.id'), 
                                   nullable=False, comment='工况输出组合ID')
    is_default = db.Column(db.SmallInteger, default=0, comment='是否为默认工况输出组合')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class SimTypeSolverRel(db.Model, ToDictMixin):
    """仿真类型-求解器关联表"""
    __tablename__ = 'sim_type_solver_rels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), nullable=False, comment='仿真类型ID')
    solver_id = db.Column(db.Integer, db.ForeignKey('solvers.id'), nullable=False, comment='求解器ID')
    is_default = db.Column(db.SmallInteger, default=0, comment='是否为默认求解器')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class ParamGroupParamRel(db.Model, ToDictMixin):
    """参数组合-参数关联表"""
    __tablename__ = 'param_group_param_rels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    param_group_id = db.Column(db.Integer, db.ForeignKey('param_groups.id'), nullable=False, comment='参数组合ID')
    param_def_id = db.Column(db.Integer, db.ForeignKey('param_defs.id'), nullable=False, comment='参数定义ID')
    default_value = db.Column(db.String(200), comment='该参数在此组合中的默认值(通用)')
    min_val = db.Column(db.Float, comment='下限(覆盖参数定义)')
    max_val = db.Column(db.Float, comment='上限(覆盖参数定义)')
    enum_values = db.Column(db.String(500), comment='枚举值,逗号分隔(DOE遍历用)')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class CondOutGroupConditionRel(db.Model, ToDictMixin):
    """工况输出组合-工况关联表"""
    __tablename__ = 'cond_out_group_condition_rels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cond_out_group_id = db.Column(db.Integer, db.ForeignKey('condition_output_groups.id'),
                                   nullable=False, comment='工况输出组合ID')
    condition_def_id = db.Column(db.Integer, db.ForeignKey('condition_defs.id'),
                                  nullable=False, comment='工况定义ID')
    config_data = db.Column(db.JSON, comment='工况配置数据')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class CondOutGroupOutputRel(db.Model, ToDictMixin):
    """工况输出组合-输出关联表（含 resp_details 预配置）"""
    __tablename__ = 'cond_out_group_output_rels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cond_out_group_id = db.Column(db.Integer, db.ForeignKey('condition_output_groups.id'),
                                   nullable=False, comment='工况输出组合ID')
    output_def_id = db.Column(db.Integer, db.ForeignKey('output_defs.id'),
                               nullable=False, comment='输出定义ID')
    # ── resp_details 预配置字段 ──
    set_name = db.Column(db.String(100), default='push', comment='set集名称，默认push')
    component = db.Column(db.String(50), default='35', comment='component，默认35(other)')
    step_name = db.Column(db.String(100), comment='分析步名称，特殊输出才需要')
    section_point = db.Column(db.String(50), comment='积分点，特殊输出才需要')
    special_output_set = db.Column(db.String(100), comment='特殊输出set，仅component为特殊值时需要')
    description = db.Column(db.String(500), comment='输出描述')
    weight = db.Column(db.Float, default=1.0, comment='权重')
    multiple = db.Column(db.Float, default=1.0, comment='数量级')
    lower_limit = db.Column(db.Float, default=0.0, comment='下限')
    upper_limit = db.Column(db.Float, comment='上限')
    target_type = db.Column(db.SmallInteger, default=3, comment='1:最大化 2:最小化 3:靠近目标值')
    target_value = db.Column(db.Float, comment='目标值(target_type=3时)')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


class WorkingCondition(db.Model, ToDictMixin):
    """工况配置表 - 姿态+仿真类型的组合"""
    __tablename__ = 'working_conditions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='工况名称')
    code = db.Column(db.String(50), unique=True, comment='工况编码')
    fold_type_id = db.Column(db.Integer, db.ForeignKey('fold_types.id'),
                              nullable=False, comment='姿态类型ID')
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'),
                             nullable=False, comment='仿真类型ID')
    # 默认配置关联
    default_param_group_id = db.Column(db.Integer, db.ForeignKey('param_groups.id'),
                                        comment='默认参数组合ID')
    default_cond_out_group_id = db.Column(db.Integer, db.ForeignKey('condition_output_groups.id'),
                                           comment='默认工况输出组合ID')
    default_solver_id = db.Column(db.Integer, db.ForeignKey('solvers.id'),
                                   comment='默认求解器ID')
    # 扩展配置
    extra_config = db.Column(db.JSON, comment='扩展配置(JSON)')
    valid = db.Column(db.SmallInteger, default=1, comment='1=有效,0=禁用')
    sort = db.Column(db.Integer, default=100, comment='排序')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))


class FoldTypeSimTypeRel(db.Model, ToDictMixin):
    """姿态-仿真类型关联表 - 定义哪些姿态支持哪些仿真类型"""
    __tablename__ = 'fold_type_sim_type_rels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fold_type_id = db.Column(db.Integer, db.ForeignKey('fold_types.id'),
                              nullable=False, comment='姿态类型ID')
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'),
                             nullable=False, comment='仿真类型ID')
    is_default = db.Column(db.SmallInteger, default=0, comment='是否为该姿态的默认仿真类型')
    sort = db.Column(db.Integer, default=100, comment='排序')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))


