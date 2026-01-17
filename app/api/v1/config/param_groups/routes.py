"""
参数组合管理 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError, ValidationError as AppValidationError
from app.constants.error_codes import ErrorCode
from .schemas import (
    ParamGroupCreateRequest,
    ParamGroupUpdateRequest,
    AddParamToGroupRequest
)
from .service import ParamGroupService

param_groups_bp = Blueprint('param_groups', __name__, url_prefix='/param-groups')
service = ParamGroupService()


@param_groups_bp.route('', methods=['GET'])
def get_param_groups():
    """获取参数组合列表"""
    try:
        valid = request.args.get('valid', type=int)
        groups = service.get_all_groups(valid)
        return success(data=groups)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>', methods=['GET'])
def get_param_group(group_id: int):
    """获取参数组合详情（包含参数列表）"""
    try:
        group = service.get_group_detail(group_id)
        return success(data=group)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('', methods=['POST'])
def create_param_group():
    """创建参数组合"""
    try:
        req = ParamGroupCreateRequest(**request.json)
        group = service.create_group(req.model_dump())
        return success(data=group, msg="创建成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>', methods=['PUT'])
def update_param_group(group_id: int):
    """更新参数组合"""
    try:
        req = ParamGroupUpdateRequest(**request.json)
        # 只传递非None的字段
        update_data = {k: v for k, v in req.model_dump().items() if v is not None}
        group = service.update_group(group_id, update_data)
        return success(data=group, msg="更新成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>', methods=['DELETE'])
def delete_param_group(group_id: int):
    """删除参数组合"""
    try:
        service.delete_group(group_id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params', methods=['GET'])
def get_group_params(group_id: int):
    """获取组合包含的参数"""
    try:
        params = service.get_group_params(group_id)
        return success(data=params)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params', methods=['POST'])
def add_param_to_group(group_id: int):
    """添加参数到组合"""
    try:
        req = AddParamToGroupRequest(**request.json)
        param = service.add_param_to_group(group_id, req.model_dump())
        return success(data=param, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params/<int:param_def_id>', methods=['DELETE'])
def remove_param_from_group(group_id: int, param_def_id: int):
    """从组合移除参数"""
    try:
        service.remove_param_from_group(group_id, param_def_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))

