"""
Legacy MySQL 数据库使用示例
展示如何从低版本 MySQL 5.6 数据库查询订单结果
"""
from app.models.legacy_result import LegacyOrderResult


def get_order_results_from_legacy_db(order_id: int):
    """从低版本数据库查询订单结果"""
    results = LegacyOrderResult.query.filter_by(order_id=order_id).all()
    return [result.to_dict() for result in results]


def get_latest_result_from_legacy_db(order_id: int):
    """从低版本数据库获取最新的订单结果"""
    result = (
        LegacyOrderResult.query
        .filter_by(order_id=order_id)
        .order_by(LegacyOrderResult.created_at.desc())
        .first()
    )
    return result.to_dict() if result else None
