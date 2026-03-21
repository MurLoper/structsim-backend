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
from app.common.serializers import get_snake_json
from .schemas import OrderCreate, OrderUpdate, OrderQuery, VerifyFileRequest
from .service import orders_service
from .excel_parser_service import excel_parser_service
from .param_merge_service import param_merge_service

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    """获取订单列表（分页）"""
    try:
        # 从查询参数构建验证对象
        query_params = {
            'page': request.args.get('page', 1, type=int),
            'page_size': int(request.args.get('page_size') or request.args.get('pageSize') or 20),
            'status': request.args.get('status', type=int),
            'project_id': request.args.get('project_id') or request.args.get('projectId'),
            'sim_type_id': request.args.get('sim_type_id') or request.args.get('simTypeId'),
            'order_no': request.args.get('order_no') or request.args.get('orderNo'),
            'created_by': request.args.get('created_by') or request.args.get('createdBy'),
            'start_date': request.args.get('start_date') or request.args.get('startDate'),
            'end_date': request.args.get('end_date') or request.args.get('endDate'),
        }
        # 转换类型
        for key in ['project_id', 'sim_type_id', 'start_date', 'end_date']:
            if query_params[key]:
                query_params[key] = int(query_params[key])
        validated = OrderQuery(**query_params)

        result = orders_service.get_orders(
            page=validated.page,
            page_size=validated.page_size,
            status=validated.status,
            project_id=validated.project_id,
            sim_type_id=validated.sim_type_id,
            order_no=validated.order_no,
            created_by=validated.created_by,
            start_date=validated.start_date,
            end_date=validated.end_date,
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
        validated = OrderCreate(**(get_snake_json() or {}))
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            user_identity = identity.get('domain_account') or identity.get('domainAccount') or identity.get('id')
        else:
            user_identity = identity
        result = orders_service.create_order(validated.model_dump(), str(user_identity))
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@orders_bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id: int):
    """更新订单"""
    try:
        validated = OrderUpdate(**(get_snake_json() or {}))
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
    pass


@orders_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """获取订单统计数据"""
    data = orders_service.get_statistics()
    return success(data)


@orders_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """获取订单趋势数据"""
    days = int(request.args.get('days') or 7)
    data = orders_service.get_trends(days)
    return success(data)


@orders_bp.route('/status-distribution', methods=['GET'])
@jwt_required()
def get_status_distribution():
    """获取订单状态分布"""
    data = orders_service.get_status_distribution()
    return success(data)


@orders_bp.route('/verify-file', methods=['POST'])
@jwt_required()
def verify_file():
    """
    验证源文件是否存在并解析 INP set 集

    请求体:
    {
        "path": "/path/to/file.inp",
        "type": 1    // 1=路径验证, 2=文件ID验证
    }

    返回:
    {
        "success": true,
        "name": "file.inp",
        "path": "/path/to/file.inp",
        "inpSets": [{"type": "component", "name": "CHIP-1"}, ...]
    }
    """
    try:
        validated = VerifyFileRequest(**(get_snake_json() or {}))
        result = orders_service.verify_file(validated.path, validated.type)
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@orders_bp.route('/parse-param-excel', methods=['POST'])
@jwt_required()
def parse_param_excel():
    """
    解析参数Excel文件
    返回解析后的参数列表，供前端预览和编辑
    """
    try:
        if 'file' not in request.files:
            return error(ErrorCode.VALIDATION_ERROR, "请上传Excel文件", http_status=400)

        file = request.files['file']
        if not file.filename:
            return error(ErrorCode.VALIDATION_ERROR, "文件名为空", http_status=400)

        # 检查文件扩展名
        allowed_ext = {'.xlsx', '.xls'}
        ext = '.' + file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_ext:
            return error(ErrorCode.VALIDATION_ERROR, "仅支持xlsx/xls格式", http_status=400)

        sheet_name = request.form.get('sheetName')
        result = excel_parser_service.parse_param_excel(file, sheet_name)

        return success(result)
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)


@orders_bp.route('/merge-params', methods=['POST'])
@jwt_required()
def merge_params():
    """
    合并基础参数和用户自定义参数

    请求体:
    {
        "baseParams": [...],    // 基础配置参数
        "customParams": [...]   // 用户自定义参数（来自Excel或手动输入）
    }

    返回:
    {
        "mergedParams": [...],  // 合并后的参数列表
        "report": {...}         // 合并报告
    }
    """
    try:
        data = get_snake_json() or {}
        base_params = data.get('base_params', [])
        custom_params = data.get('custom_params', [])

        # 获取合并报告
        report = param_merge_service.get_merge_report(base_params, custom_params)
        # 执行合并
        merged_params = param_merge_service.merge_params(base_params, custom_params)

        return success({
            'merged_params': merged_params,
            'report': report
        })
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)


@orders_bp.route('/validate-params', methods=['POST'])
@jwt_required()
def validate_params():
    """
    验证参数列表

    请求体:
    {
        "params": [...],        // 参数列表
        "paramGroupId": 1       // 参数组ID（可选，用于验证必填项）
    }
    """
    try:
        data = get_snake_json() or {}
        params = data.get('params', [])
        param_group_id = data.get('param_group_id')

        result = param_merge_service.validate_params(params, param_group_id)
        return success(result)
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)

