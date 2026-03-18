"""
参数组合管理 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError, ValidationError as AppValidationError
from app.common.serializers import get_snake_json
from app.constants.error_codes import ErrorCode
from .schemas import (
    ParamGroupCreateRequest,
    ParamGroupUpdateRequest,
    AddParamToGroupRequest
)
from .service import ParamGroupService

param_groups_bp = Blueprint('param_groups', __name__, url_prefix='/config/param-groups')
service = ParamGroupService()


@param_groups_bp.route('', methods=['GET'])
def get_param_groups():
    """获取参数组合列表，支持 ?valid=1&projectId=1 过滤"""
    try:
        valid = request.args.get('valid', type=int)
        project_id = request.args.get('projectId', type=int)
        groups = service.get_all_groups(valid, project_id)
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
        req = ParamGroupCreateRequest(**(get_snake_json() or {}))
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
        req = ParamGroupUpdateRequest(**(get_snake_json() or {}))
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
        # 调试日志
        from flask import g
        print(f"🔵 [add_param_to_group] request.data: {request.data}")
        print(f"🔵 [add_param_to_group] request.is_json: {request.is_json}")
        print(f"🔵 [add_param_to_group] g.snake_json: {getattr(g, 'snake_json', 'NOT SET')}")
        print(f"🔵 [add_param_to_group] get_snake_json(): {get_snake_json()}")

        req = AddParamToGroupRequest(**(get_snake_json() or {}))
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


@param_groups_bp.route('/<int:group_id>/params/clear', methods=['DELETE'])
def clear_group_params(group_id: int):
    """清空组合的所有参数"""
    try:
        result = service.clear_group_params(group_id)
        return success(data=result, msg="清空成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params/batch', methods=['POST'])
def batch_add_params(group_id: int):
    """
    批量添加参数到组合
    请求体: { "params": [{"paramDefId": 1, "defaultValue": "xxx", "sort": 100}, ...] }
    """
    try:
        data = get_snake_json() or {}
        params = data.get('params', [])
        if not params:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="参数列表不能为空")
        result = service.batch_add_params(group_id, params)
        return success(data=result, msg="批量添加完成")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params/batch', methods=['DELETE'])
def batch_remove_params(group_id: int):
    """
    批量移除参数
    请求体: { "paramDefIds": [1, 2, 3] }
    """
    try:
        data = get_snake_json() or {}
        param_def_ids = data.get('param_def_ids', [])
        if not param_def_ids:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="参数ID列表不能为空")
        result = service.batch_remove_params(group_id, param_def_ids)
        return success(data=result, msg="批量移除完成")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params/replace', methods=['PUT'])
def replace_group_params(group_id: int):
    """
    清空并重新配置组合参数（一键重配）
    请求体: { "params": [{"paramDefId": 1, "defaultValue": "xxx", "sort": 100}, ...] }
    """
    try:
        data = get_snake_json() or {}
        params = data.get('params', [])
        result = service.replace_group_params(group_id, params)
        return success(data=result, msg="重配完成")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/search-params', methods=['GET'])
def search_params():
    """
    搜索参数定义
    查询参数: keyword, groupId(可选，用于标记是否已在组合中)
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        group_id = request.args.get('groupId', type=int)
        if not keyword:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="关键词不能为空")
        result = service.search_params(keyword, group_id)
        return success(data=result)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/check-param', methods=['GET'])
def check_param_exists():
    """
    检查参数是否存在
    查询参数: key, name (至少提供一个)
    """
    try:
        key = request.args.get('key', '').strip()
        name = request.args.get('name', '').strip()
        if not key and not name:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="请提供key或name")
        result = service.check_param_exists(key, name)
        return success(data=result)
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))


@param_groups_bp.route('/<int:group_id>/params/create-and-add', methods=['POST'])
def create_and_add_param(group_id: int):
    """
    快速创建参数定义并添加到组合
    请求体: {
        "key": "param_key",
        "name": "参数名称",
        "unit": "单位",
        "valType": 1,
        "defaultValue": "默认值"
    }
    """
    try:
        data = get_snake_json() or {}
        result = service.create_and_add_param(group_id, data)
        return success(data=result, msg="操作成功")
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))

