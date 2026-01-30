"""
工况配置管理 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError
from app.constants.error_codes import ErrorCode
from .schemas import ConditionConfigCreateRequest, ConditionConfigUpdateRequest
from .service import ConditionConfigService

conditions_bp = Blueprint('conditions', __name__, url_prefix='/conditions')
service = ConditionConfigService()


@conditions_bp.route('', methods=['GET'])
def get_all_conditions():
    """获取所有工况配置"""
    try:
        conditions = service.get_all()
        return success(data=conditions)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@conditions_bp.route('/<int:condition_id>', methods=['GET'])
def get_condition(condition_id: int):
    """获取单个工况配置"""
    try:
        condition = service.get_by_id(condition_id)
        return success(data=condition)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@conditions_bp.route('/by-fold-sim', methods=['GET'])
def get_condition_by_fold_sim():
    """根据姿态+仿真类型查询工况"""
    try:
        fold_type_id = request.args.get('foldTypeId', type=int)
        sim_type_id = request.args.get('simTypeId', type=int)

        if not fold_type_id or not sim_type_id:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="缺少参数")

        condition = service.get_by_fold_sim(fold_type_id, sim_type_id)
        return success(data=condition)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@conditions_bp.route('/by-fold-type/<int:fold_type_id>', methods=['GET'])
def get_conditions_by_fold_type(fold_type_id: int):
    """根据姿态ID获取工况列表"""
    try:
        conditions = service.get_by_fold_type(fold_type_id)
        return success(data=conditions)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@conditions_bp.route('', methods=['POST'])
def create_condition():
    """创建工况配置"""
    try:
        req = ConditionConfigCreateRequest(**request.json)
        condition = service.create(req.model_dump())
        return success(data=condition, msg="创建成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@conditions_bp.route('/<int:condition_id>', methods=['PUT'])
def update_condition(condition_id: int):
    """更新工况配置"""
    try:
        req = ConditionConfigUpdateRequest(**request.json)
        data = {k: v for k, v in req.model_dump().items() if v is not None}
        condition = service.update(condition_id, data)
        return success(data=condition, msg="更新成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@conditions_bp.route('/<int:condition_id>', methods=['DELETE'])
def delete_condition(condition_id: int):
    """删除工况配置"""
    try:
        service.delete(condition_id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))
