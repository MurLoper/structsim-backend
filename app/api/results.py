"""
结果与轮次API接口
支持分页查询，轮次可能达到2万条
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required

from app.api import api_bp
from app.models import Order, SimTypeResult, Round
from app import db


@api_bp.route('/results/sim-type/<int:sim_type_result_id>', methods=['GET'])
@jwt_required()
def get_sim_type_result(sim_type_result_id):
    """Get simulation type result detail."""
    result = SimTypeResult.query.get(sim_type_result_id)
    
    if not result:
        return jsonify({'error': 'SimTypeResult not found'}), 404
    
    return jsonify(result.to_dict())


@api_bp.route('/results/order/<int:order_id>/sim-types', methods=['GET'])
@jwt_required()
def get_order_sim_type_results(order_id):
    """Get all simulation type results for an order."""
    results = SimTypeResult.query.filter_by(order_id=order_id).all()
    return jsonify([r.to_dict() for r in results])


@api_bp.route('/results/sim-type/<int:sim_type_result_id>/rounds', methods=['GET'])
@jwt_required()
def get_rounds(sim_type_result_id):
    """Get rounds with pagination for a simulation type result."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 100, type=int)
    status = request.args.get('status', type=int)
    
    # 限制最大页大小
    page_size = min(page_size, 500)
    
    query = Round.query.filter_by(sim_type_result_id=sim_type_result_id)
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Round.round_index.asc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    return jsonify({
        'items': [r.to_list_dict() for r in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
        'totalPages': pagination.pages
    })


@api_bp.route('/results/rounds/<int:round_id>', methods=['GET'])
@jwt_required()
def get_round_detail(round_id):
    """Get single round detail."""
    round_item = Round.query.get(round_id)
    
    if not round_item:
        return jsonify({'error': 'Round not found'}), 404
    
    return jsonify(round_item.to_dict())


@api_bp.route('/results/analysis', methods=['POST'])
@jwt_required()
def analyze_results():
    """
    数据分析接口 - 根据请求配置返回图表数据
    支持降采样以处理大量数据点
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    order_id = data.get('orderId')
    sim_type_id = data.get('simTypeId')
    chart_type = data.get('chartType', 'SCATTER')
    x_field = data.get('xField')
    y_field = data.get('yField')
    z_field = data.get('zField')
    filters = data.get('filters', {})
    sampling = data.get('sampling', {'enabled': True, 'maxPoints': 2000})
    
    # 查询轮次数据
    query = Round.query.filter_by(order_id=order_id, sim_type_id=sim_type_id)
    
    # 应用过滤器
    if filters.get('roundIndex'):
        min_idx = filters['roundIndex'].get('min')
        max_idx = filters['roundIndex'].get('max')
        if min_idx:
            query = query.filter(Round.round_index >= min_idx)
        if max_idx:
            query = query.filter(Round.round_index <= max_idx)
    
    if filters.get('status'):
        query = query.filter_by(status=filters['status'])
    
    rounds = query.order_by(Round.round_index.asc()).all()
    
    # 降采样
    max_points = sampling.get('maxPoints', 2000) if sampling.get('enabled') else len(rounds)
    if len(rounds) > max_points:
        step = len(rounds) // max_points
        rounds = rounds[::step]
    
    # 构建图表数据
    chart_data = []
    for r in rounds:
        point = {'roundIndex': r.round_index}
        
        # 从params或outputs中提取字段值
        if x_field:
            point['x'] = _extract_field_value(r, x_field)
        if y_field:
            point['y'] = _extract_field_value(r, y_field)
        if z_field:
            point['z'] = _extract_field_value(r, z_field)
        
        chart_data.append(point)
    
    return jsonify({
        'chartType': chart_type,
        'data': chart_data,
        'totalPoints': len(rounds),
        'sampled': len(rounds) < query.count() if hasattr(query, 'count') else False
    })


def _extract_field_value(round_item, field):
    """从轮次数据中提取字段值"""
    if field == 'roundIndex':
        return round_item.round_index
    
    # 尝试从params中获取
    if round_item.params and str(field) in round_item.params:
        return round_item.params[str(field)]
    
    # 尝试从outputs中获取
    if round_item.outputs and str(field) in round_item.outputs:
        return round_item.outputs[str(field)]
    
    return None

