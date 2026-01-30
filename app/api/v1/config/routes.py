"""
配置中心 - 路由层
职责：路由定义 + 参数校验 + 调用Service + 返回Response
禁止：复杂业务逻辑、直接SQL操作
"""
from flask import Blueprint, request
from pydantic import ValidationError

from app.common import success, error
from app.constants import ErrorCode
from app.common.errors import NotFoundError, BusinessError
from .schemas import (
    ProjectCreate, ProjectUpdate,
    SimTypeCreate, SimTypeUpdate,
    ParamDefCreate, ParamDefUpdate,
    SolverCreate, SolverUpdate,
    ConditionDefCreate, ConditionDefUpdate,
    OutputDefCreate, OutputDefUpdate,
    FoldTypeCreate, FoldTypeUpdate,
    ModelLevelCreate, ModelLevelUpdate,
    CareDeviceCreate, CareDeviceUpdate,
    SolverResourceCreate, SolverResourceUpdate,
    DepartmentCreate, DepartmentUpdate,
    StatusDefUpdate
)
from .service import config_service

config_bp = Blueprint('config', __name__, url_prefix='/config')


# ============ 项目配置 CRUD ============
@config_bp.route('/projects', methods=['GET'])
def list_projects():
    """获取所有项目"""
    data = config_service.get_projects()
    return success(data)


@config_bp.route('/projects/<int:id>', methods=['GET'])
def get_project(id: int):
    """获取单个项目"""
    try:
        data = config_service.get_project(id)
        return success(data)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/projects', methods=['POST'])
def create_project():
    """创建项目"""
    try:
        validated = ProjectCreate(**request.get_json())
        result = config_service.create_project(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e.errors()), http_status=400)


@config_bp.route('/projects/<int:id>', methods=['PUT'])
def update_project(id: int):
    """更新项目"""
    try:
        validated = ProjectUpdate(**request.get_json())
        result = config_service.update_project(id, validated.model_dump(exclude_unset=True))
        return success(result, "更新成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e.errors()), http_status=400)


@config_bp.route('/projects/<int:id>', methods=['DELETE'])
def delete_project(id: int):
    """删除项目（软删除）"""
    try:
        config_service.delete_project(id)
        return success(None, "删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 仿真类型 CRUD ============
@config_bp.route('/sim-types', methods=['GET'])
def list_sim_types():
    """获取所有仿真类型"""
    data = config_service.get_sim_types()
    return success(data)


@config_bp.route('/sim-types/<int:id>', methods=['GET'])
def get_sim_type(id: int):
    """获取单个仿真类型"""
    try:
        data = config_service.get_sim_type(id)
        return success(data)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/sim-types', methods=['POST'])
def create_sim_type():
    """创建仿真类型"""
    try:
        validated = SimTypeCreate(**request.get_json())
        result = config_service.create_sim_type(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/sim-types/<int:id>', methods=['PUT'])
def update_sim_type(id: int):
    """更新仿真类型"""
    try:
        validated = SimTypeUpdate(**request.get_json())
        result = config_service.update_sim_type(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/sim-types/<int:id>', methods=['DELETE'])
def delete_sim_type(id: int):
    """删除仿真类型"""
    try:
        config_service.delete_sim_type(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 参数定义 CRUD ============
@config_bp.route('/param-defs', methods=['GET'])
def list_param_defs():
    """获取所有参数定义"""
    data = config_service.get_param_defs()
    return success(data)


@config_bp.route('/param-defs', methods=['POST'])
def create_param_def():
    """创建参数定义"""
    try:
        validated = ParamDefCreate(**request.get_json())
        result = config_service.create_param_def(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/param-defs/<int:id>', methods=['PUT'])
def update_param_def(id: int):
    """更新参数定义"""
    try:
        request_data = request.get_json()
        print(f"🔵 [update_param_def] 接收到的原始数据: {request_data}")

        validated = ParamDefUpdate(**request_data)
        update_data = validated.model_dump(exclude_none=True)
        print(f"🔵 [update_param_def] 验证后的数据: {update_data}")

        result = config_service.update_param_def(id, update_data)
        print(f"🔵 [update_param_def] 更新后的结果: {result}")

        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/param-defs/<int:id>', methods=['DELETE'])
def delete_param_def(id: int):
    """删除参数定义"""
    try:
        config_service.delete_param_def(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 求解器 CRUD ============
@config_bp.route('/solvers', methods=['GET'])
def list_solvers():
    """获取所有求解器"""
    data = config_service.get_solvers()
    return success(data)


@config_bp.route('/solvers', methods=['POST'])
def create_solver():
    """创建求解器"""
    try:
        validated = SolverCreate(**request.get_json())
        result = config_service.create_solver(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/solvers/<int:id>', methods=['PUT'])
def update_solver(id: int):
    """更新求解器"""
    try:
        validated = SolverUpdate(**request.get_json())
        result = config_service.update_solver(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/solvers/<int:id>', methods=['DELETE'])
def delete_solver(id: int):
    """删除求解器"""
    try:
        config_service.delete_solver(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 工况定义 CRUD ============
@config_bp.route('/condition-defs', methods=['GET'])
def list_condition_defs():
    """获取所有工况定义"""
    data = config_service.get_condition_defs()
    return success(data)


@config_bp.route('/condition-defs', methods=['POST'])
def create_condition_def():
    """创建工况定义"""
    try:
        validated = ConditionDefCreate(**request.get_json())
        result = config_service.create_condition_def(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/condition-defs/<int:id>', methods=['PUT'])
def update_condition_def(id: int):
    """更新工况定义"""
    try:
        validated = ConditionDefUpdate(**request.get_json())
        result = config_service.update_condition_def(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/condition-defs/<int:id>', methods=['DELETE'])
def delete_condition_def(id: int):
    """删除工况定义"""
    try:
        config_service.delete_condition_def(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 输出定义 CRUD ============
@config_bp.route('/output-defs', methods=['GET'])
def list_output_defs():
    """获取所有输出定义"""
    data = config_service.get_output_defs()
    return success(data)


@config_bp.route('/output-defs', methods=['POST'])
def create_output_def():
    """创建输出定义"""
    try:
        validated = OutputDefCreate(**request.get_json())
        result = config_service.create_output_def(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/output-defs/<int:id>', methods=['PUT'])
def update_output_def(id: int):
    """更新输出定义"""
    try:
        validated = OutputDefUpdate(**request.get_json())
        result = config_service.update_output_def(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/output-defs/<int:id>', methods=['DELETE'])
def delete_output_def(id: int):
    """删除输出定义"""
    try:
        config_service.delete_output_def(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 姿态类型 CRUD ============
@config_bp.route('/fold-types', methods=['GET'])
def list_fold_types():
    """获取所有姿态类型"""
    data = config_service.get_fold_types()
    return success(data)


@config_bp.route('/fold-types', methods=['POST'])
def create_fold_type():
    """创建姿态类型"""
    try:
        validated = FoldTypeCreate(**request.get_json())
        result = config_service.create_fold_type(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/fold-types/<int:id>', methods=['PUT'])
def update_fold_type(id: int):
    """更新姿态类型"""
    try:
        validated = FoldTypeUpdate(**request.get_json())
        result = config_service.update_fold_type(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/fold-types/<int:id>', methods=['DELETE'])
def delete_fold_type(id: int):
    """删除姿态类型"""
    try:
        config_service.delete_fold_type(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 模板集查询 ============
@config_bp.route('/param-tpl-sets', methods=['GET'])
def list_param_tpl_sets():
    """获取参数模板集"""
    sim_type_id = request.args.get('simTypeId', type=int)
    data = config_service.get_param_tpl_sets(sim_type_id)
    return success(data)


@config_bp.route('/cond-out-sets', methods=['GET'])
def list_cond_out_sets():
    """获取工况输出集"""
    sim_type_id = request.args.get('simTypeId', type=int)
    data = config_service.get_cond_out_sets(sim_type_id)
    return success(data)


# ============ 其他配置查询 ============
@config_bp.route('/workflows', methods=['GET'])
def list_workflows():
    """获取工作流"""
    workflow_type = request.args.get('type')
    data = config_service.get_workflows(workflow_type)
    return success(data)


@config_bp.route('/status-defs', methods=['GET'])
def list_status_defs():
    """获取状态定义"""
    data = config_service.get_status_defs()
    return success(data)


@config_bp.route('/status-defs/<int:id>', methods=['PUT'])
def update_status_def(id: int):
    """更新状态定义"""
    try:
        validated = StatusDefUpdate(**request.get_json())
        result = config_service.update_status_def(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/automation-modules', methods=['GET'])
def list_automation_modules():
    """获取自动化模块"""
    category = request.args.get('category')
    data = config_service.get_automation_modules(category)
    return success(data)


# ============ 聚合接口 ============
@config_bp.route('/base-data', methods=['GET'])
def get_base_data():
    """获取所有基础配置数据（聚合接口）"""
    data = config_service.get_base_data()
    return success(data)


# ============ 模型层级 CRUD ============
@config_bp.route('/model-levels', methods=['GET'])
def list_model_levels():
    """获取所有模型层级"""
    data = config_service.get_model_levels()
    return success(data)


@config_bp.route('/model-levels', methods=['POST'])
def create_model_level():
    """创建模型层级"""
    try:
        validated = ModelLevelCreate(**request.get_json())
        result = config_service.create_model_level(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/model-levels/<int:id>', methods=['PUT'])
def update_model_level(id: int):
    """更新模型层级"""
    try:
        validated = ModelLevelUpdate(**request.get_json())
        result = config_service.update_model_level(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/model-levels/<int:id>', methods=['DELETE'])
def delete_model_level(id: int):
    """删除模型层级"""
    try:
        config_service.delete_model_level(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 关注器件 CRUD ============
@config_bp.route('/care-devices', methods=['GET'])
def list_care_devices():
    """获取所有关注器件"""
    data = config_service.get_care_devices()
    return success(data)


@config_bp.route('/care-devices', methods=['POST'])
def create_care_device():
    """创建关注器件"""
    try:
        validated = CareDeviceCreate(**request.get_json())
        result = config_service.create_care_device(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/care-devices/<int:id>', methods=['PUT'])
def update_care_device(id: int):
    """更新关注器件"""
    try:
        validated = CareDeviceUpdate(**request.get_json())
        result = config_service.update_care_device(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/care-devices/<int:id>', methods=['DELETE'])
def delete_care_device(id: int):
    """删除关注器件"""
    try:
        config_service.delete_care_device(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 求解器资源池 CRUD ============
@config_bp.route('/solver-resources', methods=['GET'])
def list_solver_resources():
    """获取所有求解器资源池"""
    data = config_service.get_solver_resources()
    return success(data)


@config_bp.route('/solver-resources', methods=['POST'])
def create_solver_resource():
    """创建求解器资源池"""
    try:
        validated = SolverResourceCreate(**request.get_json())
        result = config_service.create_solver_resource(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/solver-resources/<int:id>', methods=['PUT'])
def update_solver_resource(id: int):
    """更新求解器资源池"""
    try:
        validated = SolverResourceUpdate(**request.get_json())
        result = config_service.update_solver_resource(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/solver-resources/<int:id>', methods=['DELETE'])
def delete_solver_resource(id: int):
    """删除求解器资源池"""
    try:
        config_service.delete_solver_resource(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 部门 CRUD ============
@config_bp.route('/departments', methods=['GET'])
def list_departments():
    """获取所有部门"""
    data = config_service.get_departments()
    return success(data)


@config_bp.route('/departments/<int:parent_id>/children', methods=['GET'])
def list_sub_departments(parent_id: int):
    """获取子部门列表"""
    data = config_service.get_sub_departments(parent_id)
    return success(data)


@config_bp.route('/departments', methods=['POST'])
def create_department():
    """创建部门"""
    try:
        validated = DepartmentCreate(**request.get_json())
        result = config_service.create_department(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/departments/<int:id>', methods=['PUT'])
def update_department(id: int):
    """更新部门"""
    try:
        validated = DepartmentUpdate(**request.get_json())
        result = config_service.update_department(id, validated.model_dump(exclude_none=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@config_bp.route('/departments/<int:id>', methods=['DELETE'])
def delete_department(id: int):
    """删除部门"""
    try:
        config_service.delete_department(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 工况配置 API ============
@config_bp.route('/working-conditions', methods=['GET'])
def list_working_conditions():
    """获取所有工况配置"""
    data = config_service.get_working_conditions()
    return success(data)


@config_bp.route('/working-conditions/by-fold-type/<int:fold_type_id>', methods=['GET'])
def get_working_conditions_by_fold_type(fold_type_id: int):
    """根据姿态ID获取工况配置"""
    data = config_service.get_working_conditions_by_fold_type(fold_type_id)
    return success(data)


@config_bp.route('/fold-type-sim-type-rels', methods=['GET'])
def list_fold_type_sim_type_rels():
    """获取姿态-仿真类型关联列表"""
    data = config_service.get_fold_type_sim_type_rels()
    return success(data)


@config_bp.route('/fold-type-sim-type-rels/by-fold-type/<int:fold_type_id>', methods=['GET'])
def get_sim_types_by_fold_type(fold_type_id: int):
    """根据姿态ID获取支持的仿真类型列表"""
    data = config_service.get_sim_types_by_fold_type(fold_type_id)
    return success(data)


@config_bp.route('/fold-type-sim-type-rels/fold-type/<int:fold_type_id>/rels', methods=['GET'])
def get_fold_type_sim_type_rels_detail(fold_type_id: int):
    """获取指定姿态的仿真类型关联列表（带详情）"""
    data = config_service.get_fold_type_sim_type_rels_by_fold_type(fold_type_id)
    return success(data)


@config_bp.route('/fold-type-sim-type-rels/fold-type/<int:fold_type_id>', methods=['POST'])
def add_sim_type_to_fold_type(fold_type_id: int):
    """添加姿态-仿真类型关联"""
    data = request.get_json()
    result = config_service.add_sim_type_to_fold_type(fold_type_id, data)
    return success(result, "添加成功")


@config_bp.route('/fold-type-sim-type-rels/fold-type/<int:fold_type_id>/default/<int:sim_type_id>', methods=['PUT'])
def set_default_sim_type_for_fold_type(fold_type_id: int, sim_type_id: int):
    """设置姿态的默认仿真类型"""
    config_service.set_default_sim_type_for_fold_type(fold_type_id, sim_type_id)
    return success(msg="设置成功")


@config_bp.route('/fold-type-sim-type-rels/fold-type/<int:fold_type_id>/sim-type/<int:sim_type_id>', methods=['DELETE'])
def remove_sim_type_from_fold_type(fold_type_id: int, sim_type_id: int):
    """移除姿态-仿真类型关联"""
    config_service.remove_sim_type_from_fold_type(fold_type_id, sim_type_id)
    return success(msg="移除成功")

