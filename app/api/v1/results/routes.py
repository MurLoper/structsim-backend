"""
结果分析模块 - Routes层
职责：路由定义 + 参数校验 + 调用Service + 返回Response
禁止：复杂业务逻辑、直接SQL操作
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.common import success, error
from app.constants import ErrorCode
from app.common.errors import NotFoundError, BusinessError
from .schemas import RoundsQueryParams, UpdateStatusRequest
from .service import results_service

results_bp = Blueprint('results', __name__, url_prefix='/results')


@results_bp.route('/order/<int:order_id>/sim-types', methods=['GET'])
@jwt_required()
def get_order_sim_type_results(order_id: int):
    """获取订单的所有仿真类型结果"""
    try:
        data = results_service.get_order_sim_type_results(order_id)
        return success(data)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(e), http_status=404)


@results_bp.route('/sim-type/<int:result_id>', methods=['GET'])
@jwt_required()
def get_sim_type_result(result_id: int):
    """获取单个仿真类型结果详情"""
    try:
        data = results_service.get_sim_type_result(result_id)
        return success(data)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(e), http_status=404)


@results_bp.route('/sim-type/<int:sim_type_result_id>/rounds', methods=['GET'])
@jwt_required()
def get_rounds(sim_type_result_id: int):
    """获取轮次列表（分页，支持2万条）"""
    try:
        # 从查询参数构建验证对象
        query_params = {
            'page': request.args.get('page', 1, type=int),
            'pageSize': request.args.get('pageSize', 100, type=int),
            'status': request.args.get('status', type=int)
        }
        validated = RoundsQueryParams(**query_params)

        data = results_service.get_rounds(
            sim_type_result_id=sim_type_result_id,
            page=validated.page,
            page_size=validated.pageSize,
            status=validated.status
        )
        return success(data)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(e), http_status=404)


@results_bp.route('/sim-type/<int:result_id>/status', methods=['PATCH'])
@jwt_required()
def update_sim_type_result_status(result_id: int):
    """更新仿真类型结果状态"""
    try:
        data = request.get_json()
        validated = UpdateStatusRequest(**data)

        result = results_service.update_sim_type_result_status(
            result_id=result_id,
            status=validated.status,
            progress=validated.progress
        )
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(e), http_status=404)


@results_bp.route('/round/<int:round_id>/status', methods=['PATCH'])
@jwt_required()
def update_round_status(round_id: int):
    """更新轮次状态"""
    try:
        data = request.get_json()
        validated = UpdateStatusRequest(**data)

        result = results_service.update_round_status(
            round_id=round_id,
            status=validated.status,
            progress=validated.progress,
            error_msg=validated.errorMsg
        )
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(e), http_status=404)
