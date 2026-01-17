"""
工况输出组合管理 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError, ValidationError as AppValidationError
from app.constants.error_codes import ErrorCode
from .schemas import (
    CondOutGroupCreateRequest,
    CondOutGroupUpdateRequest,
    AddConditionToGroupRequest,
    AddOutputToGroupRequest
)
from .service import CondOutGroupService

cond_out_groups_bp = Blueprint('cond_out_groups', __name__, url_prefix='/cond-out-groups')
service = CondOutGroupService()


@cond_out_groups_bp.route('', methods=['GET'])
def get_cond_out_groups():
    """获取工况输出组合列表"""
    try:
        valid = request.args.get('valid', type=int)
        groups = service.get_all_groups(valid)
        return success(data=groups)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>', methods=['GET'])
def get_cond_out_group(group_id: int):
    """获取工况输出组合详情（包含工况和输出列表）"""
    try:
        group = service.get_group_detail(group_id)
        return success(data=group)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('', methods=['POST'])
def create_cond_out_group():
    """创建工况输出组合"""
    try:
        req = CondOutGroupCreateRequest(**request.json)
        group = service.create_group(req.model_dump())
        return success(data=group, msg="创建成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>', methods=['PUT'])
def update_cond_out_group(group_id: int):
    """更新工况输出组合"""
    try:
        req = CondOutGroupUpdateRequest(**request.json)
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


@cond_out_groups_bp.route('/<int:group_id>', methods=['DELETE'])
def delete_cond_out_group(group_id: int):
    """删除工况输出组合"""
    try:
        service.delete_group(group_id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/conditions', methods=['GET'])
def get_group_conditions(group_id: int):
    """获取组合包含的工况"""
    try:
        conditions = service.get_group_conditions(group_id)
        return success(data=conditions)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/conditions', methods=['POST'])
def add_condition_to_group(group_id: int):
    """添加工况到组合"""
    try:
        req = AddConditionToGroupRequest(**request.json)
        condition = service.add_condition_to_group(group_id, req.model_dump())
        return success(data=condition, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/conditions/<int:condition_def_id>', methods=['DELETE'])
def remove_condition_from_group(group_id: int, condition_def_id: int):
    """从组合移除工况"""
    try:
        service.remove_condition_from_group(group_id, condition_def_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/outputs', methods=['GET'])
def get_group_outputs(group_id: int):
    """获取组合包含的输出"""
    try:
        outputs = service.get_group_outputs(group_id)
        return success(data=outputs)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/outputs', methods=['POST'])
def add_output_to_group(group_id: int):
    """添加输出到组合"""
    try:
        req = AddOutputToGroupRequest(**request.json)
        output = service.add_output_to_group(group_id, req.model_dump())
        return success(data=output, msg="添加成功")
    except ValidationError as e:
        return error(code=ErrorCode.VALIDATION_ERROR, msg=str(e))
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/outputs/<int:output_def_id>', methods=['DELETE'])
def remove_output_from_group(group_id: int, output_def_id: int):
    """从组合移除输出"""
    try:
        service.remove_output_from_group(group_id, output_def_id)
        return success(msg="移除成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))

