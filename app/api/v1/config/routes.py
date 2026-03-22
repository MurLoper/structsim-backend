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
from app.common.serializers import get_snake_json
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
        validated = ProjectCreate(**(get_snake_json() or {}))
        result = config_service.create_project(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e.errors()), http_status=400)


@config_bp.route('/projects/<int:id>', methods=['PUT'])
def update_project(id: int):
    """更新项目"""
    try:
        validated = ProjectUpdate(**(get_snake_json() or {}))
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
        validated = SimTypeCreate(**(get_snake_json() or {}))
        result = config_service.create_sim_type(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/sim-types/<int:id>', methods=['PUT'])
def update_sim_type(id: int):
    """更新仿真类型"""
    try:
        validated = SimTypeUpdate(**(get_snake_json() or {}))
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
    """获取参数定义（支持分页和搜索）"""
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size') or request.args.get('pageSize')
    page_size = int(page_size) if page_size else 20
    keyword = request.args.get('keyword', '').strip()

    # 如果有分页参数，返回分页数据
    if page:
        data = config_service.get_param_defs_paginated(page, page_size, keyword or None)
        return success(data)
    # 否则返回全部数据（兼容旧接口）
    data = config_service.get_param_defs()
    return success(data)


@config_bp.route('/param-defs/batch', methods=['POST'])
def batch_create_param_defs():
    """批量创建参数定义"""
    try:
        data = get_snake_json() or {}
        items = data.get('items', [])
        if not items:
            return error(ErrorCode.VALIDATION_ERROR, "items不能为空", http_status=400)
        result = config_service.batch_create_param_defs(items)
        return success(result, "批量创建完成")
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)


@config_bp.route('/param-defs', methods=['POST'])
def create_param_def():
    """创建参数定义"""
    try:
        validated = ParamDefCreate(**(get_snake_json() or {}))
        result = config_service.create_param_def(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/param-defs/<int:id>', methods=['PUT'])
def update_param_def(id: int):
    """更新参数定义"""
    try:
        request_data = get_snake_json() or {}
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
        validated = SolverCreate(**(get_snake_json() or {}))
        result = config_service.create_solver(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/solvers/<int:id>', methods=['PUT'])
def update_solver(id: int):
    """更新求解器"""
    try:
        validated = SolverUpdate(**(get_snake_json() or {}))
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
        validated = ConditionDefCreate(**(get_snake_json() or {}))
        result = config_service.create_condition_def(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/condition-defs/<int:id>', methods=['PUT'])
def update_condition_def(id: int):
    """更新工况定义"""
    try:
        validated = ConditionDefUpdate(**(get_snake_json() or {}))
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
    """获取输出定义（支持分页和搜索）"""
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size') or request.args.get('pageSize')
    page_size = int(page_size) if page_size else 20
    keyword = request.args.get('keyword', '').strip()

    if page:
        data = config_service.get_output_defs_paginated(page, page_size, keyword or None)
        return success(data)
    data = config_service.get_output_defs()
    return success(data)


@config_bp.route('/post-process-modes', methods=['GET'])
def list_post_process_modes():
    """
    获取后处理方式配置。

    当前先返回后端 mock 数据，后续外部平台联通后保持该接口路径不变，
    直接在 service 内替换数据来源即可。
    """
    data = config_service.get_post_process_modes()
    return success(data)


@config_bp.route('/output-defs/batch', methods=['POST'])
def batch_create_output_defs():
    """批量创建输出定义"""
    try:
        data = get_snake_json() or {}
        items = data.get('items', [])
        if not items:
            return error(ErrorCode.VALIDATION_ERROR, "items不能为空", http_status=400)
        result = config_service.batch_create_output_defs(items)
        return success(result, "批量创建完成")
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)


@config_bp.route('/output-defs', methods=['POST'])
def create_output_def():
    """创建输出定义"""
    try:
        validated = OutputDefCreate(**(get_snake_json() or {}))
        result = config_service.create_output_def(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/output-defs/<int:id>', methods=['PUT'])
def update_output_def(id: int):
    """更新输出定义"""
    try:
        validated = OutputDefUpdate(**(get_snake_json() or {}))
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
        validated = FoldTypeCreate(**(get_snake_json() or {}))
        result = config_service.create_fold_type(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/fold-types/<int:id>', methods=['PUT'])
def update_fold_type(id: int):
    """更新姿态类型"""
    try:
        validated = FoldTypeUpdate(**(get_snake_json() or {}))
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


# ============ 旧接口（已废弃，使用 param-groups 替代） ============
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
        validated = StatusDefUpdate(**(get_snake_json() or {}))
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
        validated = ModelLevelCreate(**(get_snake_json() or {}))
        result = config_service.create_model_level(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/model-levels/<int:id>', methods=['PUT'])
def update_model_level(id: int):
    """更新模型层级"""
    try:
        validated = ModelLevelUpdate(**(get_snake_json() or {}))
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
        validated = CareDeviceCreate(**(get_snake_json() or {}))
        result = config_service.create_care_device(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/care-devices/<int:id>', methods=['PUT'])
def update_care_device(id: int):
    """更新关注器件"""
    try:
        validated = CareDeviceUpdate(**(get_snake_json() or {}))
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
        validated = SolverResourceCreate(**(get_snake_json() or {}))
        result = config_service.create_solver_resource(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/solver-resources/<int:id>', methods=['PUT'])
def update_solver_resource(id: int):
    """更新求解器资源池"""
    try:
        validated = SolverResourceUpdate(**(get_snake_json() or {}))
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
        validated = DepartmentCreate(**(get_snake_json() or {}))
        result = config_service.create_department(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@config_bp.route('/departments/<int:id>', methods=['PUT'])
def update_department(id: int):
    """更新部门"""
    try:
        validated = DepartmentUpdate(**(get_snake_json() or {}))
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
    data = get_snake_json() or {}
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
