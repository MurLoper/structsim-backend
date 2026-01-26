"""
配置表模型 - 项目、仿真类型、参数定义、模板集等
按照 requirement_and_design.md 规范设计
"""
from datetime import datetime
from app import db


class Project(db.Model):
    """项目表"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='项目名称')
    code = db.Column(db.String(50), unique=True, comment='项目编码')
    default_sim_type_id = db.Column(db.Integer, comment='默认仿真类型ID')
    default_solver_id = db.Column(db.Integer, comment='默认求解器ID')
    valid = db.Column(db.SmallInteger, default=1, comment='1=有效,0=禁用')
    sort = db.Column(db.Integer, default=100, comment='排序')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'defaultSimTypeId': self.default_sim_type_id,
            'defaultSolverId': self.default_solver_id,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }


class SimType(db.Model):
    """仿真类型表"""
    __tablename__ = 'sim_types'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='仿真类型名称')
    code = db.Column(db.String(50), unique=True, comment='类型编码')
    category = db.Column(db.String(50), comment='分类: STRUCTURE/THERMAL/MODAL等')
    default_param_tpl_set_id = db.Column(db.Integer, comment='默认参数模板集ID')
    default_cond_out_set_id = db.Column(db.Integer, comment='默认工况输出集ID')
    default_solver_id = db.Column(db.Integer, comment='默认求解器ID')
    support_alg_mask = db.Column(db.Integer, default=3, comment='支持算法位掩码:1=DOE,2=BAYES,4=...')
    node_icon = db.Column(db.String(50), comment='节点图标')
    color_tag = db.Column(db.String(20), comment='颜色标签')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'defaultParamTplSetId': self.default_param_tpl_set_id,
            'defaultCondOutSetId': self.default_cond_out_set_id,
            'defaultSolverId': self.default_solver_id,
            'supportAlgMask': self.support_alg_mask,
            'nodeIcon': self.node_icon,
            'colorTag': self.color_tag,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class ParamDef(db.Model):
    """参数定义表 - 全局基础参数"""
    __tablename__ = 'param_defs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='参数名称')
    key = db.Column(db.String(50), nullable=False, unique=True, comment='参数键名')
    val_type = db.Column(db.SmallInteger, default=1, comment='1=number,2=int,3=string,4=enum')
    unit = db.Column(db.String(20), comment='单位')
    min_val = db.Column(db.Float, comment='最小值')
    max_val = db.Column(db.Float, comment='最大值')
    precision = db.Column(db.SmallInteger, default=3, comment='精度')
    default_val = db.Column(db.String(100), comment='默认值')
    enum_options = db.Column(db.JSON, comment='枚举选项列表')
    required = db.Column(db.SmallInteger, default=1, comment='是否必填')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'key': self.key,
            'valType': self.val_type,
            'unit': self.unit,
            'minVal': self.min_val,
            'maxVal': self.max_val,
            'precision': self.precision,
            'defaultVal': self.default_val,
            'enumOptions': self.enum_options,
            'required': self.required,
            'valid': self.valid,
            'sort': self.sort
        }


class ParamTplSet(db.Model):
    """参数模板集"""
    __tablename__ = 'param_tpl_sets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), comment='关联仿真类型')
    name = db.Column(db.String(100), nullable=False, comment='模板集名称')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'simTypeId': self.sim_type_id,
            'name': self.name,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class ParamTplItem(db.Model):
    """参数模板明细"""
    __tablename__ = 'param_tpl_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tpl_set_id = db.Column(db.Integer, db.ForeignKey('param_tpl_sets.id'), nullable=False)
    tpl_name = db.Column(db.String(100), nullable=False, comment='模板名称')
    param_vals = db.Column(db.JSON, comment='参数值映射 {"param_id": value}')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'tplSetId': self.tpl_set_id,
            'tplName': self.tpl_name,
            'paramVals': self.param_vals,
            'valid': self.valid,
            'sort': self.sort
        }


class ConditionDef(db.Model):
    """工况定义表"""
    __tablename__ = 'condition_defs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='工况名称')
    code = db.Column(db.String(50), unique=True, comment='工况编码')
    category = db.Column(db.String(50), comment='工况分类')
    unit = db.Column(db.String(20), comment='单位')
    condition_schema = db.Column(db.JSON, comment='工况参数schema定义')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'unit': self.unit,
            'conditionSchema': self.condition_schema,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }


class OutputDef(db.Model):
    """输出定义表"""
    __tablename__ = 'output_defs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='输出名称')
    code = db.Column(db.String(50), unique=True, comment='输出编码')
    val_type = db.Column(db.SmallInteger, default=1, comment='1=number,2=int,3=string')
    unit = db.Column(db.String(20), comment='单位')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'valType': self.val_type,
            'unit': self.unit,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class CondOutSet(db.Model):
    """工况输出集"""
    __tablename__ = 'cond_out_sets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), comment='关联仿真类型')
    name = db.Column(db.String(100), nullable=False, comment='集合名称')
    cond_items = db.Column(db.JSON, comment='工况配置列表')
    output_ids = db.Column(db.JSON, comment='输出ID列表')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'simTypeId': self.sim_type_id,
            'name': self.name,
            'condItems': self.cond_items,
            'outputIds': self.output_ids,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class Solver(db.Model):
    """求解器配置表"""
    __tablename__ = 'solvers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='求解器名称')
    code = db.Column(db.String(50), unique=True, comment='求解器编码')
    version = db.Column(db.String(20), comment='版本')
    cpu_core_min = db.Column(db.Integer, default=1, comment='最小CPU核数')
    cpu_core_max = db.Column(db.Integer, default=256, comment='最大CPU核数')
    cpu_core_default = db.Column(db.Integer, default=16, comment='默认CPU核数')
    memory_min = db.Column(db.Integer, default=1, comment='最小内存GB')
    memory_max = db.Column(db.Integer, default=1024, comment='最大内存GB')
    memory_default = db.Column(db.Integer, default=64, comment='默认内存GB')
    params_schema = db.Column(db.JSON, comment='其他参数schema')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'version': self.version,
            'cpuCoreMin': self.cpu_core_min,
            'cpuCoreMax': self.cpu_core_max,
            'cpuCoreDefault': self.cpu_core_default,
            'memoryMin': self.memory_min,
            'memoryMax': self.memory_max,
            'memoryDefault': self.memory_default,
            'paramsSchema': self.params_schema,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class Workflow(db.Model):
    """工作流配置表"""
    __tablename__ = 'workflows'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='工作流名称')
    code = db.Column(db.String(50), unique=True, comment='工作流编码')
    type = db.Column(db.String(20), comment='类型: ORDER/SIM_TYPE/ROUND')
    nodes = db.Column(db.JSON, comment='节点列表')
    edges = db.Column(db.JSON, comment='边列表')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'type': self.type,
            'nodes': self.nodes,
            'edges': self.edges,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class StatusDef(db.Model):
    """状态定义表"""
    __tablename__ = 'status_defs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='状态名称')
    code = db.Column(db.String(30), unique=True, comment='状态编码')
    type = db.Column(db.String(20), comment='类型: PROCESS/FINAL')
    color = db.Column(db.String(100), comment='颜色样式')
    icon = db.Column(db.String(100), comment='图标样式')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'statusType': self.type,
            'colorTag': self.color,
            'icon': self.icon,
            'color': self.color,
            'valid': self.valid,
            'sort': self.sort
        }


class AutomationModule(db.Model):
    """自动化模块配置表"""
    __tablename__ = 'automation_modules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='模块名称')
    code = db.Column(db.String(50), unique=True, comment='模块编码')
    category = db.Column(db.String(50), comment='分类')
    version = db.Column(db.String(20), comment='版本')
    timeout_sec = db.Column(db.Integer, default=7200, comment='超时秒数')
    retry_max = db.Column(db.Integer, default=2, comment='最大重试次数')
    retry_backoff_sec = db.Column(db.Integer, default=60, comment='重试间隔秒')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'version': self.version,
            'timeoutSec': self.timeout_sec,
            'retryMax': self.retry_max,
            'retryBackoffSec': self.retry_backoff_sec,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class FoldType(db.Model):
    """姿态/折叠类型配置表"""
    __tablename__ = 'fold_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='姿态名称')
    code = db.Column(db.String(30), unique=True, comment='姿态编码')
    angle = db.Column(db.Integer, comment='角度值')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'angle': self.angle,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class ModelLevel(db.Model):
    """模型层级表"""
    __tablename__ = 'model_levels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='模型层级名称')
    code = db.Column(db.String(20), unique=True, comment='层级编码')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class CareDevice(db.Model):
    """关注器件表"""
    __tablename__ = 'care_devices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='器件名称')
    code = db.Column(db.String(50), unique=True, comment='器件编码')
    category = db.Column(db.String(50), comment='器件分类')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'valid': self.valid,
            'sort': self.sort,
            'remark': self.remark
        }


class SolverResource(db.Model):
    """求解器资源池表"""
    __tablename__ = 'solver_resources'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='资源池名称')
    code = db.Column(db.String(50), unique=True, comment='资源池编码')
    description = db.Column(db.Text, comment='资源池描述')
    cpu_cores = db.Column(db.Integer, comment='CPU核心数')
    memory_gb = db.Column(db.Integer, comment='内存大小GB')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'cpuCores': self.cpu_cores,
            'memoryGb': self.memory_gb,
            'valid': self.valid,
            'sort': self.sort
        }


class Department(db.Model):
    """部门表"""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='部门名称')
    code = db.Column(db.String(50), unique=True, comment='部门编码')
    parent_id = db.Column(db.Integer, default=0, comment='父部门ID')
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'parentId': self.parent_id,
            'valid': self.valid,
            'sort': self.sort
        }

