"""
订单模块 - 数据访问层
职责：封装所有数据库操作，提供数据访问接口
禁止：业务逻辑、HTTP相关代码
"""
from typing import Optional, List, Tuple, Dict
from sqlalchemy import desc, func, inspect
from sqlalchemy.orm import defer
from app.models.order import Order, OrderResult
from app.extensions import db
import time


class OrdersRepository:
    """订单相关数据访问"""

    @staticmethod
    def _has_condition_summary_column() -> bool:
        """兼容旧数据源：orders 表可能尚未包含 condition_summary 列"""
        try:
            columns = inspect(db.engine).get_columns('orders')
            return any(col.get('name') == 'condition_summary' for col in columns)
        except Exception:
            return True

    @classmethod
    def _base_query(cls):
        query = Order.query
        if not cls._has_condition_summary_column():
            query = query.options(defer(Order.condition_summary))
        return query
    
    @classmethod
    def get_orders_paginated(
        cls,
        page: int,
        page_size: int,
        status: Optional[int] = None,
        project_id: Optional[int] = None,
        sim_type_id: Optional[int] = None,
        order_no: Optional[str] = None,
        created_by: Optional[str] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None
    ) -> Tuple[List[Order], int]:
        """
        分页获取订单列表
        Returns:
            (订单列表, 总数)
        """
        query = cls._base_query()

        if status is not None:
            query = query.filter_by(status=status)
        if project_id is not None:
            query = query.filter_by(project_id=project_id)
        if created_by is not None:
            query = query.filter_by(created_by=created_by)
        if order_no is not None:
            query = query.filter(Order.order_no.ilike(f'%{order_no}%'))
        if sim_type_id is not None:
            query = query.filter(Order.sim_type_ids.contains([sim_type_id]))
        if start_date is not None:
            query = query.filter(Order.created_at >= start_date)
        if end_date is not None:
            query = query.filter(Order.created_at <= end_date)

        # 获取总数（避免 query.count() 触发对全部列的子查询）
        total = query.order_by(None).with_entities(func.count(Order.id)).scalar() or 0

        # 分页查询
        orders = query.order_by(desc(Order.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return orders, total
    
    @classmethod
    def get_order_by_id(cls, order_id: int) -> Optional[Order]:
        """根据ID获取订单"""
        return cls._base_query().filter(Order.id == order_id).first()
    
    @classmethod
    def create_order(cls, order_data: dict) -> Order:
        """创建订单"""
        if not cls._has_condition_summary_column() and 'condition_summary' in order_data:
            order_data = {k: v for k, v in order_data.items() if k != 'condition_summary'}
        order = Order(**order_data)
        db.session.add(order)
        db.session.commit()
        return order
    
    @classmethod
    def update_order(cls, order: Order, update_data: dict) -> Order:
        """更新订单"""
        if not cls._has_condition_summary_column() and 'condition_summary' in update_data:
            update_data = {k: v for k, v in update_data.items() if k != 'condition_summary'}
        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        db.session.commit()
        return order
    
    @staticmethod
    def delete_order(order: Order) -> None:
        """删除订单"""
        db.session.delete(order)
        db.session.commit()
    
    @staticmethod
    def get_order_result(order_id: int) -> Optional[OrderResult]:
        """获取订单结果"""
        return OrderResult.query.filter_by(order_id=order_id).first()

    @staticmethod
    def get_statistics() -> Dict:
        """获取订单统计数据"""
        total = Order.query.count()
        pending = Order.query.filter_by(status=0).count()
        running = Order.query.filter_by(status=1).count()
        completed = Order.query.filter_by(status=2).count()
        failed = Order.query.filter_by(status=3).count()
        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed
        }

    @staticmethod
    def get_trends(days: int) -> List[Dict]:
        """获取订单趋势数据"""
        now = int(time.time())
        start_time = now - days * 86400
        results = db.session.query(
            func.date(func.from_unixtime(Order.created_at)).label('date'),
            func.count(Order.id).label('count')
        ).filter(Order.created_at >= start_time).group_by('date').all()
        return [{'date': str(r.date), 'count': r.count} for r in results]

    @staticmethod
    def get_status_distribution() -> List[Dict]:
        """获取订单状态分布"""
        results = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        return [{'status': r.status, 'count': r.count} for r in results]


# 单例实例
orders_repository = OrdersRepository()

