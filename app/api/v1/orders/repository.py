"""
订单模块 - 数据访问层
职责：封装所有数据库操作，提供数据访问接口
禁止：业务逻辑、HTTP 相关代码
"""
from typing import Optional, List, Tuple, Dict
import time

from sqlalchemy import desc, func, inspect
from sqlalchemy.orm import defer

from app.extensions import db
from app.models.order import Order, OrderResult
from app.models.order_condition_opti import OrderConditionOpti


class OrdersRepository:
    """订单相关数据访问"""

    @staticmethod
    def _order_column_names() -> set[str]:
        try:
            return {col.get('name') for col in inspect(db.engine).get_columns('orders')}
        except Exception:
            return set()

    @classmethod
    def _has_order_column(cls, column_name: str) -> bool:
        columns = cls._order_column_names()
        return not columns or column_name in columns

    @staticmethod
    def _has_order_condition_opti_table() -> bool:
        try:
            return 'order_condition_opti' in set(inspect(db.engine).get_table_names())
        except Exception:
            return True

    @classmethod
    def _base_query(cls):
        query = Order.query
        if not cls._has_order_column('condition_summary'):
            query = query.options(defer(Order.condition_summary))
        if not cls._has_order_column('opt_issue_id'):
            query = query.options(defer(Order.opt_issue_id))
        if not cls._has_order_column('domain_account'):
            query = query.options(defer(Order.domain_account))
        if not cls._has_order_column('base_dir'):
            query = query.options(defer(Order.base_dir))
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
        domain_account: Optional[str] = None,
        created_by: Optional[str] = None,
        remark: Optional[str] = None,
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
        if domain_account is not None:
            if cls._has_order_column('domain_account'):
                query = query.filter_by(domain_account=domain_account)
            else:
                query = query.filter_by(created_by=domain_account)
        if created_by is not None:
            query = query.filter_by(created_by=created_by)
        if order_no is not None:
            query = query.filter(Order.order_no.ilike(f'%{order_no}%'))
        if remark is not None:
            query = query.filter(Order.remark.ilike(f'%{remark}%'))
        if sim_type_id is not None:
            query = query.filter(Order.sim_type_ids.contains([sim_type_id]))
        if start_date is not None:
            query = query.filter(Order.created_at >= start_date)
        if end_date is not None:
            query = query.filter(Order.created_at <= end_date)

        total = query.order_by(None).with_entities(func.count(Order.id)).scalar() or 0
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
        """创建订单并 flush，不在仓储层提交事务。"""
        missing_columns = {
            name for name in ('condition_summary', 'opt_issue_id', 'domain_account', 'base_dir')
            if name in order_data and not cls._has_order_column(name)
        }
        if missing_columns:
            order_data = {k: v for k, v in order_data.items() if k not in missing_columns}
        order = Order(**order_data)
        db.session.add(order)
        db.session.flush()
        return order

    @classmethod
    def get_orders_by_creator_between(cls, created_by: str, start_ts: int, end_ts: int) -> List[Order]:
        """获取某用户在时间区间内提交的订单（用于统计轮次）"""
        return cls._base_query().filter(
            Order.created_by == created_by,
            Order.created_at >= start_ts,
            Order.created_at <= end_ts,
        ).all()

    @classmethod
    def update_order(cls, order: Order, update_data: dict) -> Order:
        """更新订单，不在仓储层提交事务。"""
        missing_columns = {
            name for name in ('condition_summary', 'opt_issue_id', 'domain_account', 'base_dir')
            if name in update_data and not cls._has_order_column(name)
        }
        if missing_columns:
            update_data = {k: v for k, v in update_data.items() if k not in missing_columns}
        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        db.session.flush()
        return order

    @staticmethod
    def replace_order_condition_optis(order_id: int, rows: List[dict]) -> List[OrderConditionOpti]:
        """按订单全量替换 condition 运行实体。"""
        if not OrdersRepository._has_order_condition_opti_table():
            return []
        OrderConditionOpti.query.filter_by(order_id=order_id).delete(synchronize_session=False)
        entities = [OrderConditionOpti(**row) for row in rows]
        if entities:
            db.session.add_all(entities)
        db.session.flush()
        return entities

    @staticmethod
    def get_order_condition_optis(order_id: int) -> List[OrderConditionOpti]:
        if not OrdersRepository._has_order_condition_opti_table():
            return []
        return (
            OrderConditionOpti.query.filter_by(order_id=order_id)
            .order_by(OrderConditionOpti.id.asc())
            .all()
        )

    @staticmethod
    def get_order_condition_opti_by_id(order_condition_id: int) -> Optional[OrderConditionOpti]:
        if not OrdersRepository._has_order_condition_opti_table():
            return None
        return OrderConditionOpti.query.filter_by(id=order_condition_id).first()

    @staticmethod
    def commit() -> None:
        db.session.commit()

    @staticmethod
    def rollback() -> None:
        db.session.rollback()

    @staticmethod
    def delete_order(order: Order) -> None:
        """删除订单"""
        if OrdersRepository._has_order_condition_opti_table():
            OrderConditionOpti.query.filter_by(order_id=order.id).delete(synchronize_session=False)
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


orders_repository = OrdersRepository()
