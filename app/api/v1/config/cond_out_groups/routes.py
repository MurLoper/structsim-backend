"""
工况输出组合管理 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError, ValidationError as AppValidationError
from app.common.serializers import get_snake_json
from app.constants.error_codes import ErrorCode
from .schemas import (
    CondOutGroupCreateRequest,
    CondOutGroupUpdateRequest,
    AddConditionToGroupRequest,
    AddOutputToGroupRequest
)
from .service import CondOutGroupService

cond_out_groups_bp = Blueprint('output_groups', __name__, url_prefix='/config/output-groups')
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
        req = CondOutGroupCreateRequest(**(get_snake_json() or {}))
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
        req = CondOutGroupUpdateRequest(**(get_snake_json() or {}))
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
        req = AddConditionToGroupRequest(**(get_snake_json() or {}))
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
        req = AddOutputToGroupRequest(**(get_snake_json() or {}))
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


@cond_out_groups_bp.route('/<int:group_id>/outputs/clear', methods=['DELETE'])
def clear_group_outputs(group_id: int):
    """清空组合的所有输出"""
    try:
        result = service.clear_group_outputs(group_id)
        return success(data=result, msg="清空成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/search-outputs', methods=['GET'])
def search_outputs():
    """搜索输出定义"""
    try:
        keyword = request.args.get('keyword', '').strip()
        group_id = request.args.get('groupId', type=int)
        if not keyword:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="关键词不能为空")
        result = service.search_outputs(keyword, group_id)
        return success(data=result)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@cond_out_groups_bp.route('/<int:group_id>/outputs/create-and-add', methods=['POST'])
def create_and_add_output(group_id: int):
    """快速创建输出定义并添加到组合"""
    try:
        data = get_snake_json() or {}
        result = service.create_and_add_output(group_id, data)
        return success(data=result, msg="操作成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))

