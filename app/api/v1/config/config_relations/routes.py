"""
配置关联关系管理 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError
from app.constants.error_codes import ErrorCode
from .schemas import (
    ProjectSimTypeRelCreateRequest,
    SimTypeParamGroupRelCreateRequest,
    SimTypeCondOutGroupRelCreateRequest,
    SimTypeSolverRelCreateRequest,
    SetDefaultRequest
)
from .service import ConfigRelationsService

config_relations_bp = Blueprint('config_relations', __name__)
service = ConfigRelationsService()


# ============ 项目-仿真类型关联 ============

@config_relations_bp.route('/projects/<int:project_id>/sim-types', methods=['GET'])
def get_project_sim_types(project_id: int):
    """获取项目关联的仿真类型"""
    try:
        sim_types = service.get_project_sim_types(project_id)
        return success(data=sim_types)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/projects/<int:project_id>/sim-types', methods=['POST'])
def add_sim_type_to_project(project_id: int):
    """添加仿真类型到项目"""
    try:
        req = ProjectSimTypeRelCreateRequest(**request.json)
        rel = service.add_sim_type_to_project(project_id, req.model_dump())
        return success(data=rel, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/projects/<int:project_id>/sim-types/<int:sim_type_id>/default', methods=['PUT'])
def set_default_sim_type(project_id: int, sim_type_id: int):
    """设置项目的默认仿真类型"""
    try:
        service.set_default_sim_type_for_project(project_id, sim_type_id)
        return success(msg="设置成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/projects/<int:project_id>/sim-types/<int:sim_type_id>', methods=['DELETE'])
def remove_sim_type_from_project(project_id: int, sim_type_id: int):
    """从项目移除仿真类型"""
    try:
        service.remove_sim_type_from_project(project_id, sim_type_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


# ============ 仿真类型-参数组合关联 ============

@config_relations_bp.route('/sim-types/<int:sim_type_id>/param-groups', methods=['GET'])
def get_sim_type_param_groups(sim_type_id: int):
    """获取仿真类型关联的参数组合"""
    try:
        param_groups = service.get_sim_type_param_groups(sim_type_id)
        return success(data=param_groups)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/param-groups', methods=['POST'])
def add_param_group_to_sim_type(sim_type_id: int):
    """添加参数组合到仿真类型"""
    try:
        req = SimTypeParamGroupRelCreateRequest(**request.json)
        rel = service.add_param_group_to_sim_type(sim_type_id, req.model_dump())
        return success(data=rel, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/param-groups/<int:param_group_id>/default', methods=['PUT'])
def set_default_param_group(sim_type_id: int, param_group_id: int):
    """设置仿真类型的默认参数组合"""
    try:
        service.set_default_param_group_for_sim_type(sim_type_id, param_group_id)
        return success(msg="设置成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/param-groups/<int:param_group_id>', methods=['DELETE'])
def remove_param_group_from_sim_type(sim_type_id: int, param_group_id: int):
    """从仿真类型移除参数组合"""
    try:
        service.remove_param_group_from_sim_type(sim_type_id, param_group_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


# ============ 仿真类型-工况输出组合关联 ============

@config_relations_bp.route('/sim-types/<int:sim_type_id>/cond-out-groups', methods=['GET'])
def get_sim_type_cond_out_groups(sim_type_id: int):
    """获取仿真类型关联的工况输出组合"""
    try:
        cond_out_groups = service.get_sim_type_cond_out_groups(sim_type_id)
        return success(data=cond_out_groups)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/cond-out-groups', methods=['POST'])
def add_cond_out_group_to_sim_type(sim_type_id: int):
    """添加工况输出组合到仿真类型"""
    try:
        req = SimTypeCondOutGroupRelCreateRequest(**request.json)
        rel = service.add_cond_out_group_to_sim_type(sim_type_id, req.model_dump())
        return success(data=rel, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/cond-out-groups/<int:cond_out_group_id>/default', methods=['PUT'])
def set_default_cond_out_group(sim_type_id: int, cond_out_group_id: int):
    """设置仿真类型的默认工况输出组合"""
    try:
        service.set_default_cond_out_group_for_sim_type(sim_type_id, cond_out_group_id)
        return success(msg="设置成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/cond-out-groups/<int:cond_out_group_id>', methods=['DELETE'])
def remove_cond_out_group_from_sim_type(sim_type_id: int, cond_out_group_id: int):
    """从仿真类型移除工况输出组合"""
    try:
        service.remove_cond_out_group_from_sim_type(sim_type_id, cond_out_group_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


# ============ 仿真类型-求解器关联 ============

@config_relations_bp.route('/sim-types/<int:sim_type_id>/solvers', methods=['GET'])
def get_sim_type_solvers(sim_type_id: int):
    """获取仿真类型关联的求解器"""
    try:
        solvers = service.get_sim_type_solvers(sim_type_id)
        return success(data=solvers)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/solvers', methods=['POST'])
def add_solver_to_sim_type(sim_type_id: int):
    """添加求解器到仿真类型"""
    try:
        req = SimTypeSolverRelCreateRequest(**request.json)
        rel = service.add_solver_to_sim_type(sim_type_id, req.model_dump())
        return success(data=rel, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/solvers/<int:solver_id>/default', methods=['PUT'])
def set_default_solver(sim_type_id: int, solver_id: int):
    """设置仿真类型的默认求解器"""
    try:
        service.set_default_solver_for_sim_type(sim_type_id, solver_id)
        return success(msg="设置成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/solvers/<int:solver_id>', methods=['DELETE'])
def remove_solver_from_sim_type(sim_type_id: int, solver_id: int):
    """从仿真类型移除求解器"""
    try:
        service.remove_solver_from_sim_type(sim_type_id, solver_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


# ============ 配置级联查询接口（新增）============

@config_relations_bp.route('/projects/<int:project_id>/sim-types/full', methods=['GET'])
def get_project_sim_types_full(project_id: int):
    """
    获取项目支持的仿真类型（带完整配置）
    用于前端级联加载：项目 → 仿真类型 → 参数组/求解器

    返回格式:
    {
        "code": 0,
        "msg": "ok",
        "data": [
            {
                "id": 1,
                "name": "跌落",
                "code": "SIM_1",
                "isDefault": true,
                "paramGroups": [...],
                "solvers": [...]
            }
        ]
    }
    """
    try:
        data = service.get_project_sim_types_with_full_config(project_id)
        return success(data=data)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/sim-types/<int:sim_type_id>/full-config', methods=['GET'])
def get_sim_type_full_config(sim_type_id: int):
    """
    获取仿真类型的完整配置
    用于提单页面初始化，一次性获取所有需要的配置

    Query参数:
        foldType: 折叠态类型 (0=展开态, 1=折叠态)，默认0

    返回格式:
    {
        "code": 0,
        "msg": "ok",
        "data": {
            "simType": {...},
            "foldType": 0,
            "paramGroups": [...],
            "defaultParamGroup": {...},
            "solvers": [...],
            "defaultSolver": {...},
            "solverResources": [...],
            "defaultResource": {...},
            "modelLevels": [...],
            "foldTypes": [...]
        }
    }
    """
    try:
        fold_type = request.args.get('foldType', type=int, default=0)
        data = service.get_sim_type_full_config(sim_type_id, fold_type)
        return success(data=data)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@config_relations_bp.route('/default-config', methods=['GET'])
def get_default_config():
    """
    获取提单默认配置（核心接口）
    前端提单页面初始化时调用此接口，一次性获取所有需要的配置

    Query参数:
        projectId: 项目ID（必填）
        simTypeId: 仿真类型ID（必填）
        foldType: 折叠态类型 (0=展开态, 1=折叠态)，默认0

    返回格式:
    {
        "code": 0,
        "msg": "ok",
        "data": {
            "project": {...},
            "simType": {...},
            "foldType": 0,
            "defaultParamGroup": {...},
            "defaultSolver": {...},
            "defaultResource": {...},
            "modelLevels": [...],
            "foldTypes": [...],
            "paramGroups": [...],
            "solvers": [...],
            "solverResources": [...]
        }
    }

    使用示例:
        GET /api/v1/config-relations/default-config?projectId=1753&simTypeId=1&foldType=0
    """
    try:
        project_id = request.args.get('projectId', type=int)
        sim_type_id = request.args.get('simTypeId', type=int)
        fold_type = request.args.get('foldType', type=int, default=0)

        if not project_id:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="缺少参数: projectId")
        if not sim_type_id:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="缺少参数: simTypeId")

        data = service.get_default_config_for_order(project_id, sim_type_id, fold_type)
        return success(data=data, msg="获取默认配置成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))

