"""
结果分析模块 - Service层
职责：业务编排、事务管理、调用Repository、组装返回数据
禁止：直接SQL操作、HTTP相关逻辑
"""
from typing import Dict, Any, List
from math import ceil
from app.common.errors import NotFoundError, BusinessError
from app.common.serializers import serialize_model
from .repository import results_repository


class ResultsService:
    """结果分析服务"""

    def __init__(self):
        self.repository = results_repository

    def get_order_sim_type_results(self, order_id: int) -> List[Dict[str, Any]]:
        """
        获取订单的所有仿真类型结果

        Args:
            order_id: 订单ID

        Returns:
            仿真类型结果列表
        """
        results = self.repository.get_sim_type_results_by_order(order_id)

        # 序列化并补充仿真类型名称
        data = []
        for result in results:
            result_dict = self._serialize_sim_type_result(result)
            # 获取仿真类型名称
            sim_type_name = self.repository.get_sim_type_name(result.sim_type_id)
            result_dict['simTypeName'] = sim_type_name or f"SimType-{result.sim_type_id}"
            data.append(result_dict)

        return data

    def get_sim_type_result(self, result_id: int) -> Dict[str, Any]:
        """
        获取单个仿真类型结果详情

        Args:
            result_id: 结果ID

        Returns:
            结果详情字典

        Raises:
            NotFoundError: 结果不存在
        """
        result = self.repository.get_sim_type_result_by_id(result_id)
        if not result:
            raise NotFoundError(f"仿真类型结果 {result_id} 不存在")

        result_dict = self._serialize_sim_type_result(result)

        # 补充仿真类型名称
        sim_type_name = self.repository.get_sim_type_name(result.sim_type_id)
        result_dict['simTypeName'] = sim_type_name or f"SimType-{result.sim_type_id}"

        # 补充统计信息
        stats = self.repository.get_result_statistics(result_id)
        result_dict['statistics'] = stats

        return result_dict

    def get_rounds(
        self,
        sim_type_result_id: int,
        page: int = 1,
        page_size: int = 100,
        status: int = None
    ) -> Dict[str, Any]:
        """
        获取轮次列表（分页）

        Args:
            sim_type_result_id: 仿真类型结果ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选

        Returns:
            包含轮次列表和分页信息的字典

        Raises:
            NotFoundError: 仿真类型结果不存在
        """
        # 验证仿真类型结果是否存在
        result = self.repository.get_sim_type_result_by_id(sim_type_result_id)
        if not result:
            raise NotFoundError(f"仿真类型结果 {sim_type_result_id} 不存在")

        # 分页查询
        rounds, total = self.repository.get_rounds_paginated(
            sim_type_result_id, page, page_size, status
        )

        return {
            'items': [self._serialize_round(r) for r in rounds],
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': ceil(total / page_size) if total > 0 else 0
        }

    def update_sim_type_result_status(
        self,
        result_id: int,
        status: int,
        progress: int = None
    ) -> Dict[str, Any]:
        """
        更新仿真类型结果状态

        Args:
            result_id: 结果ID
            status: 状态
            progress: 进度

        Returns:
            更新后的结果

        Raises:
            NotFoundError: 结果不存在
        """
        success = self.repository.update_sim_type_result_status(result_id, status, progress)
        if not success:
            raise NotFoundError(f"仿真类型结果 {result_id} 不存在")

        # 返回更新后的数据
        return self.get_sim_type_result(result_id)

    def update_round_status(
        self,
        round_id: int,
        status: int,
        progress: int = None,
        error_msg: str = None
    ) -> Dict[str, Any]:
        """
        更新轮次状态

        Args:
            round_id: 轮次ID
            status: 状态
            progress: 进度
            error_msg: 错误信息

        Returns:
            更新后的轮次

        Raises:
            NotFoundError: 轮次不存在
        """
        success = self.repository.update_round_status(round_id, status, progress, error_msg)
        if not success:
            raise NotFoundError(f"轮次 {round_id} 不存在")

        # 返回更新后的数据
        round_obj = self.repository.get_round_by_id(round_id)
        return self._serialize_round(round_obj)

    def _serialize_sim_type_result(self, result) -> Dict[str, Any]:
        """序列化仿真类型结果"""
        return {
            'id': result.id,
            'orderId': result.order_id,
            'simTypeId': result.sim_type_id,
            'status': result.status,
            'progress': result.progress,
            'curNodeId': result.cur_node_id,
            'stuckNodeId': result.stuck_node_id,
            'stuckModuleId': result.stuck_module_id,
            'bestExists': result.best_exists,
            'bestRuleId': result.best_rule_id,
            'bestRoundIndex': result.best_round_index,
            'bestMetrics': result.best_metrics,
            'totalRounds': result.total_rounds,
            'completedRounds': result.completed_rounds,
            'failedRounds': result.failed_rounds,
            'createdAt': result.created_at,
            'updatedAt': result.updated_at
        }

    def _serialize_round(self, round_obj) -> Dict[str, Any]:
        """序列化轮次"""
        return {
            'id': round_obj.id,
            'simTypeResultId': round_obj.sim_type_result_id,
            'roundIndex': round_obj.round_index,
            'status': round_obj.status,
            'paramValues': round_obj.params,
            'outputResults': round_obj.outputs,
            'errorMsg': round_obj.error_msg,
            'startedAt': round_obj.started_at,
            'finishedAt': round_obj.finished_at,
            'createdAt': round_obj.created_at
        }


# 单例
results_service = ResultsService()
