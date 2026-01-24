"""
结果分析模块 - Repository层
职责：纯数据访问、CRUD操作封装、查询组合
禁止：业务逻辑、HTTP相关逻辑
"""
from typing import Optional, List, Tuple
from sqlalchemy import func
from app.extensions import db
from app.models.result import SimTypeResult, Round
from app.models.config import SimType


class ResultsRepository:
    """结果分析仓储类"""

    def __init__(self):
        self.session = db.session

    def get_sim_type_result_by_id(self, result_id: int) -> Optional[SimTypeResult]:
        """根据ID查询仿真类型结果"""
        return self.session.get(SimTypeResult, result_id)

    def get_sim_type_results_by_order(self, order_id: int) -> List[SimTypeResult]:
        """根据订单ID查询所有仿真类型结果"""
        return self.session.query(SimTypeResult).filter_by(order_id=order_id).all()

    def get_rounds_paginated(
        self,
        sim_type_result_id: int,
        page: int = 1,
        page_size: int = 100,
        status: Optional[int] = None
    ) -> Tuple[List[Round], int]:
        """
        分页查询轮次列表

        Args:
            sim_type_result_id: 仿真类型结果ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选

        Returns:
            (轮次列表, 总数)
        """
        query = self.session.query(Round).filter_by(sim_type_result_id=sim_type_result_id)

        if status is not None:
            query = query.filter_by(status=status)

        # 按轮次索引排序
        query = query.order_by(Round.round_index.asc())

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_round_by_id(self, round_id: int) -> Optional[Round]:
        """根据ID查询单个轮次"""
        return self.session.get(Round, round_id)

    def update_sim_type_result_status(
        self,
        result_id: int,
        status: int,
        progress: Optional[int] = None
    ) -> bool:
        """
        更新仿真类型结果状态

        Args:
            result_id: 结果ID
            status: 状态
            progress: 进度

        Returns:
            是否成功
        """
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
        error_msg: Optional[str] = None
    ) -> bool:
        """
        更新轮次状态

        Args:
            round_id: 轮次ID
            status: 状态
            progress: 进度
            error_msg: 错误信息

        Returns:
            是否成功
        """
        round_obj = self.get_round_by_id(round_id)
        if not round_obj:
            return False

        round_obj.status = status
        if progress is not None:
            round_obj.progress = progress
        if error_msg is not None:
            round_obj.error_msg = error_msg

        self.session.commit()
        return True

    def get_sim_type_name(self, sim_type_id: int) -> Optional[str]:
        """获取仿真类型名称"""
        sim_type = self.session.get(SimType, sim_type_id)
        return sim_type.name if sim_type else None

    def get_result_statistics(self, sim_type_result_id: int) -> dict:
        """
        获取结果统计信息

        Returns:
            统计字典
        """
        result = self.get_sim_type_result_by_id(sim_type_result_id)
        if not result:
            return {}

        # 查询各状态轮次数量
        status_counts = self.session.query(
            Round.status,
            func.count(Round.id)
        ).filter_by(
            sim_type_result_id=sim_type_result_id
        ).group_by(Round.status).all()

        stats = {
            "totalRounds": result.total_rounds,
            "completedRounds": result.completed_rounds,
            "failedRounds": result.failed_rounds,
            "statusDistribution": {str(status): count for status, count in status_counts}
        }

        return stats


# 单例
results_repository = ResultsRepository()
