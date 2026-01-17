"""
订单模块 - 路由层
职责：路由定义 + 参数校验 + 调用Service + 返回Response
禁止：复杂业务逻辑、直接SQL操作
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.common import success, error
from app.constants import ErrorCode
from app.common.errors import NotFoundError, BusinessError
from .schemas import OrderCreate, OrderUpdate, OrderQuery
from .service import orders_service

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    """获取订单列表（分页）"""
    try:
        # 从查询参数构建验证对象
        query_params = {
            'page': request.args.get('page', 1, type=int),
            'pageSize': request.args.get('pageSize', 20, type=int),
            'status': request.args.get('status', type=int),
            'projectId': request.args.get('projectId', type=int)
        }
        validated = OrderQuery(**query_params)
        
        result = orders_service.get_orders(
            page=validated.page,
            page_size=validated.pageSize,
            status=validated.status,
            project_id=validated.projectId
        )
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id: int):
    """获取订单详情"""
    try:
        result = orders_service.get_order(order_id)
        return success(result)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@orders_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """创建订单"""
    try:
        validated = OrderCreate(**request.get_json())
        user_id = get_jwt_identity()
        result = orders_service.create_order(validated.model_dump(), user_id)
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@orders_bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id: int):
    """更新订单"""
    try:
        validated = OrderUpdate(**request.get_json())
        result = orders_service.update_order(
            order_id,
            validated.model_dump(exclude_none=True)
        )
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id: int):
    """删除订单"""
    try:
        orders_service.delete_order(order_id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@orders_bp.route('/<int:order_id>/result', methods=['GET'])
@jwt_required()
def get_order_result(order_id: int):
    """获取订单结果"""
    try:
        result = orders_service.get_order(order_id)
        # 这里可以扩展获取结果的逻辑
        return success(result)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)

