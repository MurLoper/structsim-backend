"""
Results module service layer.
"""
from math import ceil
from typing import Any, Dict, List, Optional

from app.common.errors import NotFoundError
from .repository import results_repository


class ResultsService:
    """Business service for results queries."""

    def __init__(self):
        self.repository = results_repository

    def get_order_sim_type_results(self, order_id: int) -> List[Dict[str, Any]]:
        results = self.repository.get_sim_type_results_by_order(order_id)
        data: List[Dict[str, Any]] = []
        for result in results:
            result_dict = self._serialize_sim_type_result(result)
            sim_type_name = self.repository.get_sim_type_name(result.sim_type_id)
            result_dict["simTypeName"] = sim_type_name or f"SimType-{result.sim_type_id}"
            data.append(result_dict)
        return data

    def get_sim_type_result(self, result_id: int) -> Dict[str, Any]:
        result = self.repository.get_sim_type_result_by_id(result_id)
        if not result:
            raise NotFoundError(f"仿真类型结果 {result_id} 不存在")

        result_dict = self._serialize_sim_type_result(result)
        sim_type_name = self.repository.get_sim_type_name(result.sim_type_id)
        result_dict["simTypeName"] = sim_type_name or f"SimType-{result.sim_type_id}"
        result_dict["statistics"] = self.repository.get_result_statistics(result_id)
        return result_dict

    def get_rounds(
        self,
        sim_type_result_id: int,
        page: int = 1,
        page_size: int = 100,
        status: Optional[int] = None,
    ) -> Dict[str, Any]:
        result = self.repository.get_sim_type_result_by_id(sim_type_result_id)
        if not result:
            raise NotFoundError(f"仿真类型结果 {sim_type_result_id} 不存在")

        rounds, total = self.repository.get_rounds_paginated(
            sim_type_result_id=sim_type_result_id,
            page=page,
            page_size=page_size,
            status=status,
        )

        return {
            "items": [self._serialize_round(item) for item in rounds],
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": ceil(total / page_size) if total > 0 else 0,
        }

    def update_sim_type_result_status(
        self,
        result_id: int,
        status: int,
        progress: Optional[int] = None,
    ) -> Dict[str, Any]:
        success = self.repository.update_sim_type_result_status(result_id, status, progress)
        if not success:
            raise NotFoundError(f"仿真类型结果 {result_id} 不存在")
        return self.get_sim_type_result(result_id)

    def update_round_status(
        self,
        round_id: int,
        status: int,
        progress: Optional[int] = None,
        error_msg: Optional[str] = None,
    ) -> Dict[str, Any]:
        success = self.repository.update_round_status(round_id, status, progress, error_msg)
        if not success:
            raise NotFoundError(f"轮次 {round_id} 不存在")
        round_obj = self.repository.get_round_by_id(round_id)
        return self._serialize_round(round_obj)

    def get_order_conditions(self, order_id: int) -> List[Dict[str, Any]]:
        conditions = self.repository.get_order_conditions(order_id)
        return [self._serialize_order_condition(item) for item in conditions]

    def get_order_condition(self, order_condition_id: int) -> Dict[str, Any]:
        """获取单个工况方案摘要。

        当前开发环境无法接入真实自动化库，因此正式 results 接口先返回后端拼装的 mock
        元数据。后续接入真实执行链路后，直接在这里替换内部实现即可。
        """
        condition = self.repository.get_order_condition_by_id(order_condition_id)
        if not condition:
            raise NotFoundError(f"订单工况 {order_condition_id} 不存在")

        payload = self._serialize_order_condition(condition)
        payload["roundSchema"] = self._build_round_schema(condition)
        payload["mockResultEnabled"] = True
        payload["resultSource"] = "mock"
        return payload

    def get_order_condition_rounds(
        self,
        order_condition_id: int,
        page: int = 1,
        page_size: int = 100,
        status: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取工况方案轮次数据。

        这里保留正式接口路径，当前阶段在接口内部填充 mock 数据，以便前端联调和页面
        展示先打通。未来自动化库接入后，直接替换此方法内部逻辑，不需要再改接口。
        """
        condition = self.repository.get_order_condition_by_id(order_condition_id)
        if not condition:
            raise NotFoundError(f"订单工况 {order_condition_id} 不存在")

        return self._build_order_condition_rounds_payload(
            condition=condition,
            page=page,
            page_size=page_size,
            status=status,
        )

    def _serialize_sim_type_result(self, result) -> Dict[str, Any]:
        return {
            "id": result.id,
            "orderId": result.order_id,
            "simTypeId": result.sim_type_id,
            "status": result.status,
            "progress": result.progress,
            "curNodeId": result.cur_node_id,
            "stuckNodeId": result.stuck_node_id,
            "stuckModuleId": result.stuck_module_id,
            "bestExists": result.best_exists,
            "bestRuleId": result.best_rule_id,
            "bestRoundIndex": result.best_round_index,
            "bestMetrics": result.best_metrics,
            "totalRounds": result.total_rounds,
            "completedRounds": result.completed_rounds,
            "failedRounds": result.failed_rounds,
            "createdAt": result.created_at,
            "updatedAt": result.updated_at,
        }

    def _serialize_round(self, round_obj) -> Dict[str, Any]:
        return {
            "id": round_obj.id,
            "simTypeResultId": round_obj.sim_type_result_id,
            "roundIndex": round_obj.round_index,
            "status": round_obj.status,
            "paramValues": round_obj.params,
            "outputResults": round_obj.outputs,
            "errorMsg": round_obj.error_msg,
            "startedAt": round_obj.started_at,
            "finishedAt": round_obj.finished_at,
            "createdAt": round_obj.created_at,
        }

    def _serialize_order_condition(self, condition) -> Dict[str, Any]:
        payload = condition.to_dict()
        return {
            "id": payload["id"],
            "orderId": payload["order_id"],
            "orderNo": payload["order_no"],
            "optIssueId": payload["opt_issue_id"],
            "optJobId": payload["opt_job_id"],
            "conditionId": payload["condition_id"],
            "foldTypeId": payload["fold_type_id"],
            "foldTypeName": payload["fold_type_name"],
            "simTypeId": payload["sim_type_id"],
            "simTypeName": payload["sim_type_name"],
            "algorithmType": payload["algorithm_type"],
            "roundTotal": payload["round_total"],
            "outputCount": payload["output_count"],
            "solverId": payload["solver_id"],
            "careDeviceIds": payload["care_device_ids"] or [],
            "remark": payload["remark"],
            "runningModule": payload["running_module"],
            "process": payload["process"],
            "status": payload["status"],
            "statistics": payload["statistics_json"],
            "resultSummary": payload["result_summary_json"],
            "conditionSnapshot": payload["condition_snapshot"],
            "externalMeta": payload["external_meta"],
            "createdAt": payload["created_at"],
            "updatedAt": payload["updated_at"],
        }

    @staticmethod
    def _normalize_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_list(value: Any) -> List[Any]:
        return value if isinstance(value, list) else []

    def _extract_param_names(self, condition) -> List[str]:
        snapshot = self._normalize_dict(getattr(condition, "condition_snapshot", None))
        params = self._normalize_dict(snapshot.get("params"))
        param_details = self._normalize_list(
            params.get("paramDetails", params.get("param_details"))
        )

        names: List[str] = []
        for index, item in enumerate(param_details, start=1):
            if not isinstance(item, dict):
                continue
            name = (
                item.get("paramName")
                or item.get("name")
                or item.get("paramKey")
                or item.get("key")
                or item.get("paramId")
            )
            if name is not None:
                names.append(str(name))
            elif index <= 3:
                names.append(f"param{index}")

        if names:
            return names

        selected_ids = self._normalize_list(
            params.get("selectedParamIds", params.get("selected_param_ids"))
        )
        if selected_ids:
            return [f"param{index}" for index, _ in enumerate(selected_ids, start=1)]

        return ["param1", "param2", "param3"]

    def _extract_output_names(self, condition) -> List[str]:
        snapshot = self._normalize_dict(getattr(condition, "condition_snapshot", None))
        output = self._normalize_dict(snapshot.get("output"))
        resp_details = self._normalize_list(
            output.get("respDetails", output.get("resp_details"))
        )

        names: List[str] = []
        for index, item in enumerate(resp_details, start=1):
            if not isinstance(item, dict):
                continue
            name = (
                item.get("respName")
                or item.get("outputName")
                or item.get("name")
                or item.get("respId")
            )
            if name is not None:
                names.append(str(name))
            elif index <= max(int(getattr(condition, "output_count", 0)), 1):
                names.append(f"output{index}")

        if names:
            return names

        output_count = int(getattr(condition, "output_count", 0) or 0)
        if output_count > 0:
            return [f"output{index}" for index in range(1, output_count + 1)]

        return ["output1", "output2", "output3"]

    def _build_round_schema(self, condition) -> Dict[str, Any]:
        algorithm_type = str(getattr(condition, "algorithm_type", "") or "").upper()
        param_names = self._extract_param_names(condition)
        output_names = self._extract_output_names(condition)
        is_bayesian = algorithm_type == "BAYESIAN"

        columns: List[Dict[str, Any]] = [{"key": "roundIndex", "label": "轮次", "type": "base"}]

        for name in param_names:
            columns.append({"key": f"params.{name}", "label": name, "type": "param"})

        for name in output_names:
            columns.append({"key": f"outputs.{name}", "label": name, "type": "output"})
            if is_bayesian:
                columns.append(
                    {
                        "key": f"outputs.{name}Weighted",
                        "label": f"{name}_加权",
                        "type": "output_weighted",
                    }
                )

        columns.extend(
            [
                {"key": "runningModule", "label": "当前模块", "type": "status"},
                {"key": "process", "label": "进度", "type": "progress"},
            ]
        )

        if is_bayesian:
            columns.append({"key": "finalResult", "label": "综合结果", "type": "result"})

        return {
            "algorithmType": algorithm_type or None,
            "columns": columns,
            "paramKeys": param_names,
            "outputKeys": output_names,
        }

    def _build_mock_round_item(self, condition, round_index: int) -> Dict[str, Any]:
        algorithm_type = str(getattr(condition, "algorithm_type", "") or "").upper()
        is_bayesian = algorithm_type == "BAYESIAN"
        param_names = self._extract_param_names(condition)
        output_names = self._extract_output_names(condition)
        total_rounds = max(int(condition.round_total or 0), 1)

        param_values: Dict[str, Any] = {}
        for idx, name in enumerate(param_names, start=1):
            value = round(10 + round_index * 1.25 + idx * 0.33, 4)
            param_values[name] = value

        output_values: Dict[str, Any] = {}
        weighted_total = 0.0
        for idx, name in enumerate(output_names, start=1):
            base_value = round(40 + round_index * 2.15 + idx * 1.07, 4)
            output_values[name] = base_value
            if is_bayesian:
                weighted_value = round(base_value * (0.2 + idx * 0.15), 4)
                output_values[f"{name}Weighted"] = weighted_value
                weighted_total += weighted_value

        failed_round_index = total_rounds - 1 if total_rounds >= 6 else None
        is_failed = failed_round_index is not None and round_index == failed_round_index
        is_running = round_index == total_rounds

        modules = self._build_module_details(is_running=is_running, is_failed=is_failed)
        progress = 100 if not is_running else 78
        running_module = "POST" if is_running else "DONE"
        status = 3 if is_failed else (1 if is_running else 2)

        return {
            "id": f"mock-{condition.id}-{round_index}",
            "orderConditionId": condition.id,
            "optIssueId": condition.opt_issue_id,
            "optJobId": condition.opt_job_id,
            "roundIndex": round_index,
            "algorithmType": algorithm_type or None,
            "status": status,
            "params": param_values,
            "outputs": output_values,
            "runningModule": running_module,
            "process": progress,
            "moduleDetails": modules,
            "finalResult": round(weighted_total, 4) if is_bayesian else None,
        }

    def _build_order_condition_rounds_payload(
        self,
        condition,
        page: int,
        page_size: int,
        status: Optional[int],
    ) -> Dict[str, Any]:
        """正式接口当前阶段统一返回 mock 轮次数据。"""
        total = max(int(condition.round_total or 0), 1)
        all_items = [
            self._build_mock_round_item(condition, round_index)
            for round_index in range(1, total + 1)
        ]
        if status is not None:
            all_items = [item for item in all_items if item["status"] == status]

        page = max(page, 1)
        page_size = max(page_size, 1)
        filtered_total = len(all_items)
        start = (page - 1) * page_size + 1
        end = min(start + page_size - 1, filtered_total)
        items = all_items[start - 1:end] if start <= filtered_total else []

        completed = sum(1 for item in all_items if item["status"] == 2)
        failed = sum(1 for item in all_items if item["status"] == 3)
        running = sum(1 for item in all_items if item["status"] == 1)
        progress_percent = round(((completed + failed) / total) * 100, 2) if total > 0 else 0

        return {
            "orderCondition": self._serialize_order_condition(condition),
            "resultSource": "mock",
            "algorithmType": condition.algorithm_type,
            "columns": self._build_round_schema(condition)["columns"],
            "items": items,
            "statistics": {
                "totalRounds": total,
                "completedRounds": completed,
                "failedRounds": failed,
                "runningRounds": running,
                "progressPercent": progress_percent,
            },
            "page": page,
            "pageSize": page_size,
            "total": filtered_total,
            "totalPages": ceil(filtered_total / page_size) if filtered_total > 0 else 0,
        }

    @staticmethod
    def _build_module_details(is_running: bool, is_failed: bool) -> List[Dict[str, Any]]:
        if is_failed:
            stages = [
                ("PREPARE", "已完成", 100, 12, "success"),
                ("SOLVE", "失败", 64, 133, "error"),
                ("POST", "未开始", 0, None, "pending"),
            ]
        elif is_running:
            stages = [
                ("PREPARE", "已完成", 100, 12, "success"),
                ("SOLVE", "已完成", 100, 156, "success"),
                ("POST", "运行中", 78, 18, "running"),
            ]
        else:
            stages = [
                ("PREPARE", "已完成", 100, 12, "success"),
                ("SOLVE", "已完成", 100, 156, "success"),
                ("POST", "已完成", 100, 24, "success"),
            ]
        return [
            {
                "moduleCode": code,
                "moduleName": code,
                "statusText": status_text,
                "progress": progress,
                "durationSec": duration,
                "statusColor": status_color,
            }
            for code, status_text, progress, duration, status_color in stages
        ]


results_service = ResultsService()
