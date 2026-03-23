"""
Results module repository layer.
Responsible for pure data access only.
"""
from typing import List, Optional, Tuple

from sqlalchemy import func, inspect

from app.extensions import db
from app.models.config import FoldType, SimType
from app.models.order import Order
from app.models.order_condition_opti import OrderConditionOpti
from app.models.result import Round, SimTypeResult


class ResultsRepository:
    """Repository for results related queries."""

    def __init__(self):
        self.session = db.session

    @staticmethod
    def _has_order_condition_opti_table() -> bool:
        try:
            return 'order_condition_opti' in set(inspect(db.engine).get_table_names())
        except Exception:
            return True

    def get_sim_type_result_by_id(self, result_id: int) -> Optional[SimTypeResult]:
        return self.session.get(SimTypeResult, result_id)

    def get_sim_type_results_by_order(self, order_id: int) -> List[SimTypeResult]:
        return self.session.query(SimTypeResult).filter_by(order_id=order_id).all()

    def get_rounds_paginated(
        self,
        sim_type_result_id: int,
        page: int = 1,
        page_size: int = 100,
        status: Optional[int] = None,
    ) -> Tuple[List[Round], int]:
        query = self.session.query(Round).filter_by(sim_type_result_id=sim_type_result_id)

        if status is not None:
            query = query.filter_by(status=status)

        query = query.order_by(Round.round_index.asc())
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def get_round_by_id(self, round_id: int) -> Optional[Round]:
        return self.session.get(Round, round_id)

    def update_sim_type_result_status(
        self,
        result_id: int,
        status: int,
        progress: Optional[int] = None,
    ) -> bool:
        result = self.get_sim_type_result_by_id(result_id)
        if not result:
            return False

        result.status = status
        if progress is not None:
            result.progress = progress

        self.session.commit()
        return True

    def update_round_status(
        self,
        round_id: int,
        status: int,
        progress: Optional[int] = None,
        error_msg: Optional[str] = None,
    ) -> bool:
        round_obj = self.get_round_by_id(round_id)
        if not round_obj:
            return False

        round_obj.status = status
        if progress is not None and hasattr(round_obj, "progress"):
            setattr(round_obj, "progress", progress)
        if error_msg is not None:
            round_obj.error_msg = error_msg

        self.session.commit()
        return True

    def get_sim_type_name(self, sim_type_id: int) -> Optional[str]:
        sim_type = self.session.get(SimType, sim_type_id)
        return sim_type.name if sim_type else None

    def get_fold_type_name(self, fold_type_id: int) -> Optional[str]:
        fold_type = self.session.get(FoldType, fold_type_id)
        return fold_type.name if fold_type else None

    def get_result_statistics(self, sim_type_result_id: int) -> dict:
        result = self.get_sim_type_result_by_id(sim_type_result_id)
        if not result:
            return {}

        status_counts = (
            self.session.query(Round.status, func.count(Round.id))
            .filter_by(sim_type_result_id=sim_type_result_id)
            .group_by(Round.status)
            .all()
        )

        return {
            "totalRounds": result.total_rounds,
            "completedRounds": result.completed_rounds,
            "failedRounds": result.failed_rounds,
            "statusDistribution": {str(status): count for status, count in status_counts},
        }

    def get_order_conditions(self, order_id: int) -> List[OrderConditionOpti]:
        if not self._has_order_condition_opti_table():
            return []
        return (
            self.session.query(OrderConditionOpti)
            .filter_by(order_id=order_id)
            .order_by(OrderConditionOpti.id.asc())
            .all()
        )

    def get_order_condition_by_id(self, order_condition_id: int) -> Optional[OrderConditionOpti]:
        if not self._has_order_condition_opti_table():
            return None
        return self.session.get(OrderConditionOpti, order_condition_id)

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        return self.session.get(Order, order_id)


results_repository = ResultsRepository()
