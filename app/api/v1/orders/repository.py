from typing import Dict, List, Optional, Tuple
import time

from sqlalchemy import desc, func, inspect
from sqlalchemy.orm import defer
from sqlalchemy.orm.attributes import set_committed_value

from app.extensions import db
from app.models.case_opti import CaseConditionOpti, OrderCaseOpti
from app.models.order import Order, OrderResult


class OrdersRepository:
    """订单模块数据访问层。"""

    @staticmethod
    def _is_memory_sqlite() -> bool:
        try:
            return str(db.engine.url) == 'sqlite:///:memory:'
        except Exception:
            return False

    @staticmethod
    def _order_column_names() -> set[str]:
        if OrdersRepository._is_memory_sqlite():
            return {column.name for column in Order.__table__.columns}
        try:
            return {col.get('name') for col in inspect(db.engine).get_columns('orders')}
        except Exception:
            return set()

    @classmethod
    def _has_order_column(cls, column_name: str) -> bool:
        columns = cls._order_column_names()
        return not columns or column_name in columns

    @staticmethod
    def _has_case_opti_tables() -> bool:
        if OrdersRepository._is_memory_sqlite():
            return True
        try:
            table_names = set(inspect(db.engine).get_table_names())
            return {'order_case_opti', 'case_condition_opti'}.issubset(table_names)
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
        if not cls._has_order_column('phase_id'):
            query = query.options(defer(Order.phase_id))
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
        end_date: Optional[int] = None,
    ) -> Tuple[List[Order], int]:
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
        return cls._base_query().filter(Order.id == order_id).first()

    @classmethod
    def create_order(cls, order_data: dict) -> Order:
        missing_columns = {
            name for name in ('condition_summary', 'opt_issue_id', 'domain_account', 'base_dir', 'phase_id')
            if name in order_data and not cls._has_order_column(name)
        }
        if missing_columns:
            order_data = {key: value for key, value in order_data.items() if key not in missing_columns}
        order = Order(**order_data)
        db.session.add(order)
        db.session.flush()
        return order

    @classmethod
    def get_orders_by_creator_between(cls, created_by: str, start_ts: int, end_ts: int) -> List[Order]:
        return cls._base_query().filter(
            Order.created_by == created_by,
            Order.created_at >= start_ts,
            Order.created_at <= end_ts,
        ).all()

    @classmethod
    def get_recent_orders_by_project(cls, project_id: int, limit: int = 100) -> List[Order]:
        return (
            cls._base_query()
            .filter(Order.project_id == project_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .all()
        )

    @classmethod
    def update_order(cls, order: Order, update_data: dict) -> Order:
        missing_columns = {
            name for name in ('condition_summary', 'opt_issue_id', 'domain_account', 'base_dir', 'phase_id')
            if name in update_data and not cls._has_order_column(name)
        }
        if missing_columns:
            update_data = {key: value for key, value in update_data.items() if key not in missing_columns}
        if update_data and getattr(order, 'id', None):
            db.session.query(Order).filter(Order.id == order.id).update(
                update_data,
                synchronize_session=False,
            )
        for key, value in update_data.items():
            if hasattr(order, key):
                set_committed_value(order, key, value)
        db.session.flush()
        return order

    @staticmethod
    def replace_case_conditions(order_id: int, rows: List[dict]) -> List[CaseConditionOpti]:
        """按订单全量替换 case/condition 自动化关联实体。"""
        if not OrdersRepository._has_case_opti_tables():
            return []

        CaseConditionOpti.query.filter_by(order_id=order_id).delete(synchronize_session=False)
        OrderCaseOpti.query.filter_by(order_id=order_id).delete(synchronize_session=False)

        grouped_rows: Dict[int, List[dict]] = {}
        for row in rows:
            case_index = int(row.get('case_index') or 1)
            grouped_rows.setdefault(case_index, []).append(row)

        case_entities: Dict[int, OrderCaseOpti] = {}
        for case_index, case_rows in sorted(grouped_rows.items()):
            first_row = case_rows[0]
            case_entity = OrderCaseOpti(
                order_id=order_id,
                order_no=first_row.get('order_no'),
                case_index=case_index,
                case_name=first_row.get('case_name') or f'Case-{case_index}',
                opt_issue_id=first_row.get('opt_issue_id') or 0,
                opt_job_id=first_row.get('opt_job_id'),
                parameter_scope=first_row.get('parameter_scope') or 'per_condition',
                case_snapshot=first_row.get('case_snapshot'),
                external_meta=first_row.get('external_meta'),
                status=first_row.get('status') or 0,
                process=first_row.get('process') or 0,
                created_at=first_row.get('created_at'),
                updated_at=first_row.get('updated_at'),
            )
            db.session.add(case_entity)
            db.session.flush()
            case_entities[case_index] = case_entity

        condition_entities: List[CaseConditionOpti] = []
        case_only_keys = {'case_name', 'case_snapshot'}
        for row in rows:
            case_index = int(row.get('case_index') or 1)
            condition_row = {key: value for key, value in row.items() if key not in case_only_keys}
            condition_row['order_case_id'] = case_entities[case_index].id
            if condition_row.get('opt_job_id') is None:
                condition_row['opt_job_id'] = case_entities[case_index].opt_job_id
            condition_entities.append(CaseConditionOpti(**condition_row))

        if condition_entities:
            db.session.add_all(condition_entities)
        db.session.flush()
        return condition_entities

    @staticmethod
    def get_case_conditions(order_id: int) -> List[CaseConditionOpti]:
        if not OrdersRepository._has_case_opti_tables():
            return []
        return (
            CaseConditionOpti.query.filter_by(order_id=order_id)
            .order_by(CaseConditionOpti.case_index.asc(), CaseConditionOpti.id.asc())
            .all()
        )

    @staticmethod
    def get_order_cases(order_id: int) -> List[OrderCaseOpti]:
        if not OrdersRepository._has_case_opti_tables():
            return []
        return (
            OrderCaseOpti.query.filter_by(order_id=order_id)
            .order_by(OrderCaseOpti.case_index.asc(), OrderCaseOpti.id.asc())
            .all()
        )

    @staticmethod
    def get_case_condition_by_id(case_condition_id: int) -> Optional[CaseConditionOpti]:
        if not OrdersRepository._has_case_opti_tables():
            return None
        return CaseConditionOpti.query.filter_by(id=case_condition_id).first()

    @staticmethod
    def update_case_condition(condition: CaseConditionOpti, update_data: dict) -> CaseConditionOpti:
        condition_update_data = {
            key: value
            for key, value in update_data.items()
            if hasattr(condition, key)
        }
        if condition_update_data and getattr(condition, 'id', None):
            db.session.query(CaseConditionOpti).filter(CaseConditionOpti.id == condition.id).update(
                condition_update_data,
                synchronize_session=False,
            )
        for key, value in condition_update_data.items():
            set_committed_value(condition, key, value)

        if condition.order_case_id:
            with db.session.no_autoflush:
                case_entity = OrderCaseOpti.query.filter_by(id=condition.order_case_id).first()
            if case_entity:
                case_update_data = {
                    key: update_data[key]
                    for key in ('opt_issue_id', 'opt_job_id', 'status', 'process', 'external_meta', 'updated_at')
                    if key in update_data and hasattr(case_entity, key)
                }
                if case_update_data:
                    db.session.query(OrderCaseOpti).filter(OrderCaseOpti.id == case_entity.id).update(
                        case_update_data,
                        synchronize_session=False,
                    )
                    for key, value in case_update_data.items():
                        set_committed_value(case_entity, key, value)

        db.session.flush()
        return condition

    @staticmethod
    def commit() -> None:
        db.session.commit()

    @staticmethod
    def rollback() -> None:
        db.session.rollback()

    @staticmethod
    def delete_order(order: Order) -> None:
        if OrdersRepository._has_case_opti_tables():
            CaseConditionOpti.query.filter_by(order_id=order.id).delete(synchronize_session=False)
            OrderCaseOpti.query.filter_by(order_id=order.id).delete(synchronize_session=False)
        db.session.delete(order)
        db.session.commit()

    @staticmethod
    def get_order_result(order_id: int) -> Optional[OrderResult]:
        return OrderResult.query.filter_by(order_id=order_id).first()

    @staticmethod
    def get_statistics() -> Dict:
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
            'failed': failed,
        }

    @staticmethod
    def get_trends(days: int) -> List[Dict]:
        now = int(time.time())
        start_time = now - days * 86400
        results = db.session.query(
            func.date(func.from_unixtime(Order.created_at)).label('date'),
            func.count(Order.id).label('count'),
        ).filter(Order.created_at >= start_time).group_by('date').all()
        return [{'date': str(row.date), 'count': row.count} for row in results]

    @staticmethod
    def get_status_distribution() -> List[Dict]:
        results = db.session.query(
            Order.status,
            func.count(Order.id).label('count'),
        ).group_by(Order.status).all()
        return [{'status': row.status, 'count': row.count} for row in results]


orders_repository = OrdersRepository()
