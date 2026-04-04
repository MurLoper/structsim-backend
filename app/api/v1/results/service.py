"""
Results module service layer.
"""
import json
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from app.common.errors import NotFoundError
from app.services.external_data import optimization_repository
from .repository import results_repository


MOCK_CONDITION_REF_BASE = 7_000_000_000_000_000
MOCK_CONDITION_REF_MULTIPLIER = 100_000


class _MockOrderCondition:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = dict(payload)
        for key, value in self._payload.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._payload)


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
        if conditions:
            return [
                self._enrich_order_condition_payload(
                    self._serialize_order_condition(item, include_mock_summary=True)
                )
                for item in conditions
            ]

        order = self.repository.get_order_by_id(order_id)
        if not order:
            return []
        return [
            self._enrich_order_condition_payload(
                self._serialize_order_condition(item, include_mock_summary=True)
            )
            for item in self._build_mock_order_conditions_from_order(order)
        ]

    def get_order_condition(self, order_condition_id: int) -> Dict[str, Any]:
        condition = self._resolve_order_condition(order_condition_id)
        if not condition:
            raise NotFoundError(f"订单工况 {order_condition_id} 不存在")

        payload = self._enrich_order_condition_payload(
            self._serialize_order_condition(condition, include_mock_summary=True)
        )
        payload["roundSchema"] = self._build_round_schema(condition)
        payload["mockResultEnabled"] = payload.get("resultSource") != "external"
        return payload

    def get_order_condition_rounds(
        self,
        order_condition_id: int,
        page: int = 1,
        page_size: int = 100,
        status: Optional[int] = None,
    ) -> Dict[str, Any]:
        condition = self._resolve_order_condition(order_condition_id)
        if not condition:
            raise NotFoundError(f"订单工况 {order_condition_id} 不存在")

        external_payload = self._build_external_order_condition_rounds_payload(
            condition=condition,
            page=page,
            page_size=page_size,
            status=status,
        )
        if external_payload is not None:
            return external_payload

        return self._build_order_condition_rounds_payload(
            condition=condition,
            page=page,
            page_size=page_size,
            status=status,
        )

    def _enrich_order_condition_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        opt_issue_id = self._to_int(payload.get('optIssueId'), 0)
        opt_job_id = self._to_int(payload.get('optJobId'), 0)

        opt_issue = optimization_repository.build_issue_summary(opt_issue_id) if opt_issue_id > 0 else None
        job_summaries = optimization_repository.build_job_summaries([opt_job_id]) if opt_job_id > 0 else []
        payload['optIssue'] = opt_issue
        payload['conditionJobs'] = job_summaries
        payload['jobSummaries'] = job_summaries
        if job_summaries:
            primary_job = job_summaries[0]
            payload['status'] = int(primary_job.get('status', payload.get('status', 0)) or 0)
            payload['process'] = int(primary_job.get('progress', payload.get('process', 0)) or 0)
            payload['runningModule'] = payload.get('runningModule') or None
            payload['statistics'] = {
                **self._normalize_dict(payload.get('statistics')),
                'totalRounds': len(primary_job.get('rounds') or []),
                'completedRounds': sum(
                    1 for item in (primary_job.get('rounds') or []) if int(item.get('status', 0) or 0) == 2
                ),
                'failedRounds': sum(
                    1 for item in (primary_job.get('rounds') or []) if int(item.get('status', 0) or 0) == 3
                ),
                'runningRounds': sum(
                    1 for item in (primary_job.get('rounds') or []) if int(item.get('status', 0) or 0) == 1
                ),
                'progressPercent': int(primary_job.get('progress', 0) or 0),
            }
            payload['resultSource'] = 'external'
        else:
            payload.setdefault('resultSource', 'mock')
        return payload

    def _build_external_order_condition_rounds_payload(
        self,
        condition,
        page: int,
        page_size: int,
        status: Optional[int],
    ) -> Dict[str, Any] | None:
        opt_job_id = self._to_int(getattr(condition, 'opt_job_id', None), 0)
        if opt_job_id <= 0:
            return None

        job_summaries = optimization_repository.build_job_summaries([opt_job_id])
        if not job_summaries:
            return None

        job_summary = job_summaries[0]
        raw_rounds = job_summary.get('rounds') or []
        items: List[Dict[str, Any]] = []
        for round_item in raw_rounds:
            round_status = int(round_item.get('status', 0) or 0)
            if status is not None and round_status != status:
                continue
            outputs = {}
            for output in round_item.get('outputs') or []:
                resp_name = output.get('respName') or f"resp_{output.get('respConfigId')}"
                value = output.get('finalValue')
                if value in (None, ''):
                    value = output.get('originValue')
                outputs[str(resp_name)] = value
            items.append(
                {
                    'id': f"external-{opt_job_id}-{round_item.get('circleId')}",
                    'orderConditionId': getattr(condition, 'id', None),
                    'optIssueId': getattr(condition, 'opt_issue_id', None),
                    'optJobId': opt_job_id,
                    'roundIndex': int(round_item.get('roundIndex', 0) or 0),
                    'algorithmType': getattr(condition, 'algorithm_type', None),
                    'status': round_status,
                    'params': {},
                    'outputs': outputs,
                    'runningModule': round_item.get('runningModule'),
                    'process': 100 if round_status == 2 else (50 if round_status == 1 else 0),
                    'moduleDetails': [],
                    'finalResult': round_item.get('finalValue'),
                }
            )

        total = len(items)
        page = max(page, 1)
        page_size = max(page_size, 1)
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = items[start:end]

        condition_payload = self._enrich_order_condition_payload(
            self._serialize_order_condition(condition, include_mock_summary=False)
        )
        condition_payload['roundSchema'] = self._build_round_schema(condition)

        return {
            'orderCondition': condition_payload,
            'resultSource': 'external',
            'algorithmType': getattr(condition, 'algorithm_type', None),
            'columns': self._build_round_schema(condition)['columns'],
            'items': paged_items,
            'statistics': self._normalize_dict(condition_payload.get('statistics')),
            'page': page,
            'pageSize': page_size,
            'total': total,
            'totalPages': ceil(total / page_size) if total > 0 else 0,
            'optIssue': condition_payload.get('optIssue'),
            'conditionJobs': condition_payload.get('conditionJobs'),
            'jobSummaries': condition_payload.get('jobSummaries'),
        }

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_list(value: Any) -> List[Any]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
            return parsed if isinstance(parsed, list) else []
        return value if isinstance(value, list) else []

    @staticmethod
    def _condition_to_dict(condition: Any) -> Dict[str, Any]:
        if hasattr(condition, "to_dict"):
            return condition.to_dict()
        return dict(condition) if isinstance(condition, dict) else {}

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

    def _serialize_order_condition(
        self,
        condition,
        include_mock_summary: bool = False,
    ) -> Dict[str, Any]:
        payload = self._condition_to_dict(condition)
        result = {
            "id": payload.get("id"),
            "orderId": payload.get("order_id"),
            "orderNo": payload.get("order_no"),
            "optIssueId": payload.get("opt_issue_id"),
            "optJobId": payload.get("opt_job_id"),
            "conditionId": payload.get("condition_id"),
            "foldTypeId": payload.get("fold_type_id"),
            "foldTypeName": payload.get("fold_type_name"),
            "simTypeId": payload.get("sim_type_id"),
            "simTypeName": payload.get("sim_type_name"),
            "algorithmType": payload.get("algorithm_type"),
            "roundTotal": payload.get("round_total"),
            "outputCount": payload.get("output_count"),
            "solverId": payload.get("solver_id"),
            "careDeviceIds": payload.get("care_device_ids") or [],
            "remark": payload.get("remark"),
            "runningModule": payload.get("running_module"),
            "process": payload.get("process"),
            "status": payload.get("status"),
            "statistics": payload.get("statistics_json"),
            "resultSummary": payload.get("result_summary_json"),
            "conditionSnapshot": payload.get("condition_snapshot"),
            "externalMeta": payload.get("external_meta"),
            "createdAt": payload.get("created_at"),
            "updatedAt": payload.get("updated_at"),
        }
        if include_mock_summary:
            self._apply_mock_condition_summary(condition, result)
        return result

    @staticmethod
    def _extract_algorithm_type_from_condition(condition: Dict[str, Any]) -> Optional[str]:
        params = condition.get("params")
        if not isinstance(params, dict):
            return None
        opt_params = params.get("optParams", params.get("opt_params"))
        if not isinstance(opt_params, dict):
            return None

        raw_alg = opt_params.get("algType", opt_params.get("alg_type"))
        if raw_alg in (1, "1", "bayesian", "BAYESIAN"):
            return "BAYESIAN"
        if raw_alg in (5, "5"):
            return "DOE_FILE"
        if raw_alg in (2, "2", "doe", "DOE"):
            return "DOE"
        return str(raw_alg) if raw_alg is not None else None

    @staticmethod
    def _extract_solver_id_from_condition(condition: Dict[str, Any]) -> Optional[str]:
        solver = condition.get("solver")
        if not isinstance(solver, dict):
            return None

        solver_id = solver.get("solverId", solver.get("solver_id"))
        if solver_id is None:
            return None
        version = solver.get("solverVersion", solver.get("solver_version"))
        return f"{solver_id}_{version}" if version else str(solver_id)

    @staticmethod
    def _extract_output_count_from_condition(condition: Dict[str, Any]) -> int:
        output = condition.get("output")
        if not isinstance(output, dict):
            return 0

        resp_details = output.get("respDetails", output.get("resp_details"))
        if isinstance(resp_details, list):
            return len(resp_details)

        selected_output_ids = output.get("selectedOutputIds", output.get("selected_output_ids"))
        if isinstance(selected_output_ids, list):
            return len(selected_output_ids)
        return 0

    def _estimate_rounds_from_opt_params(self, opt_params: Optional[Dict[str, Any]]) -> int:
        if not isinstance(opt_params, dict):
            return 0

        alg_type = self._to_int(opt_params.get("alg_type", opt_params.get("algType", 2)), 2)
        if alg_type in (2, 5):
            doe_data = opt_params.get("doe_param_data", opt_params.get("doeParamData"))
            return len(doe_data) if isinstance(doe_data, list) else 0

        if alg_type != 1:
            return 0

        batch_size_type = self._to_int(
            opt_params.get("batch_size_type", opt_params.get("batchSizeType", 1)),
            1,
        )
        batch_size = opt_params.get("batch_size", opt_params.get("batchSize")) or []
        max_iter = self._to_int(
            opt_params.get("max_iter", opt_params.get("maxIter", len(batch_size) or 1)),
            1,
        )
        max_iter = max(max_iter, 0)

        if batch_size_type == 2:
            custom = opt_params.get("custom_batch_size", opt_params.get("customBatchSize")) or []
            total = 0
            for idx in range(1, max_iter + 1):
                value = 0
                for item in custom:
                    if not isinstance(item, dict):
                        continue
                    start = self._to_int(item.get("start_index", item.get("startIndex")), 0)
                    end = self._to_int(item.get("end_index", item.get("endIndex")), 0)
                    if start <= idx <= end:
                        value = self._to_int(item.get("value"), 0)
                        break
                total += max(value, 0)
            return total

        values: List[int] = []
        for item in batch_size:
            if isinstance(item, dict):
                values.append(max(self._to_int(item.get("value"), 0), 0))
            else:
                values.append(max(self._to_int(item, 0), 0))

        if max_iter <= 0 or not values:
            return 0
        if len(values) >= max_iter:
            return sum(values[:max_iter])
        if len(values) == 1:
            return values[0] * max_iter
        return sum(values) + values[-1] * (max_iter - len(values))

    @staticmethod
    def _encode_mock_condition_ref(order_id: int, condition_index: int) -> int:
        return (
            MOCK_CONDITION_REF_BASE
            + max(int(order_id), 0) * MOCK_CONDITION_REF_MULTIPLIER
            + max(int(condition_index), 0)
        )

    @staticmethod
    def _decode_mock_condition_ref(ref_id: int) -> Optional[Tuple[int, int]]:
        if ref_id < MOCK_CONDITION_REF_BASE:
            return None
        encoded = ref_id - MOCK_CONDITION_REF_BASE
        order_id = encoded // MOCK_CONDITION_REF_MULTIPLIER
        condition_index = encoded % MOCK_CONDITION_REF_MULTIPLIER
        if order_id <= 0 or condition_index <= 0:
            return None
        return order_id, condition_index

    def _get_order_input_conditions(self, order) -> List[Dict[str, Any]]:
        input_json = self._normalize_dict(getattr(order, "input_json", None))
        return [item for item in self._normalize_list(input_json.get("conditions")) if isinstance(item, dict)]

    def _get_order_fold_type_ids(self, order) -> List[int]:
        fold_type_ids = self._normalize_list(getattr(order, "fold_type_ids", None))
        values = [self._to_int(item, 0) for item in fold_type_ids]
        values = [item for item in values if item >= 0]
        fold_type_id = self._to_int(getattr(order, "fold_type_id", None), 0)
        if fold_type_id > 0 and fold_type_id not in values:
            values.insert(0, fold_type_id)
        return values

    def _get_primary_fold_type(self, order) -> Tuple[int, Optional[str]]:
        fold_type_ids = self._get_order_fold_type_ids(order)
        fold_type_id = fold_type_ids[0] if fold_type_ids else 0
        fold_type_name = self.repository.get_fold_type_name(fold_type_id) if fold_type_id > 0 else None
        return fold_type_id, fold_type_name

    def _build_param_details_from_opt_config(self, opt_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        params = self._normalize_dict(opt_config.get("params"))
        opt_params = self._normalize_dict(params.get("optParams", params.get("opt_params")))
        domain = self._normalize_list(opt_params.get("domain"))
        details: List[Dict[str, Any]] = []
        for item in domain:
            if not isinstance(item, dict):
                continue
            param_name = (
                item.get("param_name")
                or item.get("paramName")
                or item.get("name")
                or item.get("key")
            )
            if param_name is None:
                continue
            details.append({"paramName": str(param_name)})
        return details

    def _build_output_details_from_opt_config(self, opt_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        output = self._normalize_dict(opt_config.get("output"))
        resp_details = self._normalize_list(output.get("respDetails", output.get("resp_details")))
        details: List[Dict[str, Any]] = []
        for item in resp_details:
            if not isinstance(item, dict):
                continue
            resp_name = (
                item.get("respName")
                or item.get("outputName")
                or item.get("description")
                or item.get("output_type")
                or item.get("name")
            )
            if resp_name is None:
                continue
            details.append({"respName": str(resp_name)})
        return details

    def _build_legacy_conditions_from_opt_param(self, order) -> List[Dict[str, Any]]:
        input_json = self._normalize_dict(getattr(order, "input_json", None))
        opt_param = self._normalize_dict(input_json.get("opt_param"))
        if not opt_param:
            opt_param = self._normalize_dict(getattr(order, "opt_param", None))
        if not opt_param:
            return []

        fold_type_id, fold_type_name = self._get_primary_fold_type(order)
        conditions: List[Dict[str, Any]] = []
        for index, (raw_key, raw_value) in enumerate(opt_param.items(), start=1):
            opt_config = self._normalize_dict(raw_value)
            sim_type_id = self._to_int(opt_config.get("sim_type_id", raw_key), self._to_int(raw_key, index))
            sim_type_name = self.repository.get_sim_type_name(sim_type_id) or f"仿真类型-{sim_type_id}"
            params = self._normalize_dict(opt_config.get("params"))
            output = self._normalize_dict(opt_config.get("output"))
            solver = self._normalize_dict(opt_config.get("solver"))
            care_device_ids = opt_config.get("care_device_ids", opt_config.get("careDeviceIds"))
            param_details = self._build_param_details_from_opt_config(opt_config)
            output_details = self._build_output_details_from_opt_config(opt_config)

            if param_details and not params.get("paramDetails"):
                params = {**params, "paramDetails": param_details}
            if output_details and not output.get("respDetails"):
                output = {**output, "respDetails": output_details}

            conditions.append(
                {
                    "conditionId": index,
                    "foldTypeId": fold_type_id,
                    "foldTypeName": fold_type_name,
                    "simTypeId": sim_type_id,
                    "simTypeName": sim_type_name,
                    "params": params,
                    "output": output,
                    "solver": solver,
                    "careDeviceIds": care_device_ids if isinstance(care_device_ids, list) else [],
                }
            )
        return conditions

    def _build_legacy_conditions_from_sim_types(self, order) -> List[Dict[str, Any]]:
        sim_type_ids = [self._to_int(item, 0) for item in self._normalize_list(getattr(order, "sim_type_ids", None))]
        sim_type_ids = [item for item in sim_type_ids if item > 0]
        if not sim_type_ids:
            return []

        fold_type_id, fold_type_name = self._get_primary_fold_type(order)
        return [
            {
                "conditionId": index,
                "foldTypeId": fold_type_id,
                "foldTypeName": fold_type_name,
                "simTypeId": sim_type_id,
                "simTypeName": self.repository.get_sim_type_name(sim_type_id) or f"仿真类型-{sim_type_id}",
                "params": {},
                "output": {},
                "solver": {},
                "careDeviceIds": [],
            }
            for index, sim_type_id in enumerate(sim_type_ids, start=1)
        ]

    def _get_order_input_condition_by_index(
        self,
        order,
        condition_index: int,
    ) -> Optional[Dict[str, Any]]:
        if condition_index <= 0:
            return None
        conditions = self._get_order_input_conditions(order)
        list_index = condition_index - 1
        if list_index >= len(conditions):
            return None
        return conditions[list_index]

    def _build_mock_order_condition_from_order(
        self,
        order,
        condition_dict: Dict[str, Any],
        condition_index: int,
    ) -> _MockOrderCondition:
        params = self._normalize_dict(condition_dict.get("params"))
        output = self._normalize_dict(condition_dict.get("output"))
        solver = self._normalize_dict(condition_dict.get("solver"))
        care_device_ids = condition_dict.get("careDeviceIds", condition_dict.get("care_device_ids"))
        condition_id = self._to_int(
            condition_dict.get("conditionId", condition_dict.get("condition_id")),
            condition_index,
        )
        condition_remark = condition_dict.get(
            "remark",
            condition_dict.get("conditionRemark", condition_dict.get("condition_remark")),
        )

        payload = {
            "id": self._encode_mock_condition_ref(order.id, condition_index),
            "order_id": order.id,
            "order_no": getattr(order, "order_no", None),
            "opt_issue_id": self._to_int(getattr(order, "opt_issue_id", None), 0),
            "opt_job_id": None,
            "condition_id": condition_id,
            "fold_type_id": self._to_int(
                condition_dict.get("foldTypeId", condition_dict.get("fold_type_id")),
                0,
            ),
            "fold_type_name": condition_dict.get("foldTypeName", condition_dict.get("fold_type_name")),
            "sim_type_id": self._to_int(
                condition_dict.get("simTypeId", condition_dict.get("sim_type_id")),
                0,
            ),
            "sim_type_name": condition_dict.get("simTypeName", condition_dict.get("sim_type_name")),
            "algorithm_type": self._extract_algorithm_type_from_condition(condition_dict),
            "round_total": self._estimate_rounds_from_opt_params(
                params.get("optParams", params.get("opt_params"))
            ),
            "output_count": self._extract_output_count_from_condition(condition_dict),
            "solver_id": self._extract_solver_id_from_condition(condition_dict),
            "care_device_ids": care_device_ids if isinstance(care_device_ids, list) else [],
            "remark": condition_remark if isinstance(condition_remark, str) else getattr(order, "remark", None),
            "running_module": None,
            "process": 0,
            "status": 0,
            "statistics_json": None,
            "result_summary_json": None,
            "condition_snapshot": {
                "conditionId": condition_dict.get("conditionId", condition_dict.get("condition_id")),
                "foldTypeId": condition_dict.get("foldTypeId", condition_dict.get("fold_type_id")),
                "foldTypeName": condition_dict.get("foldTypeName", condition_dict.get("fold_type_name")),
                "simTypeId": condition_dict.get("simTypeId", condition_dict.get("sim_type_id")),
                "simTypeName": condition_dict.get("simTypeName", condition_dict.get("sim_type_name")),
                "params": params,
                "output": output,
                "solver": solver,
                "careDeviceIds": care_device_ids if isinstance(care_device_ids, list) else [],
                "witness": {
                    "foldTypeId": condition_dict.get("foldTypeId", condition_dict.get("fold_type_id")),
                    "foldTypeName": condition_dict.get("foldTypeName", condition_dict.get("fold_type_name")),
                    "simTypeId": condition_dict.get("simTypeId", condition_dict.get("sim_type_id")),
                    "simTypeName": condition_dict.get("simTypeName", condition_dict.get("sim_type_name")),
                },
                "rawCondition": condition_dict,
            },
            "external_meta": {
                "resultSource": "mock",
                "mockSource": "order_input_json",
                "conditionIndex": condition_index,
                "totalConditions": len(self._get_order_input_conditions(order)),
                "orderStatus": self._to_int(getattr(order, "status", None), 0),
                "orderProgress": self._to_int(getattr(order, "progress", None), 0),
            },
            "created_at": getattr(order, "created_at", None),
            "updated_at": getattr(order, "updated_at", None),
        }
        return _MockOrderCondition(payload)

    def _build_mock_order_conditions_from_order(self, order) -> List[_MockOrderCondition]:
        conditions = self._get_order_input_conditions(order)
        return [
            self._build_mock_order_condition_from_order(order, condition_dict, condition_index)
            for condition_index, condition_dict in enumerate(conditions, start=1)
        ]

    def _resolve_mock_order_condition(self, order_condition_id: int):
        decoded = self._decode_mock_condition_ref(order_condition_id)
        if not decoded:
            return None

        order_id, condition_index = decoded
        order = self.repository.get_order_by_id(order_id)
        if not order:
            return None

        condition_dict = self._get_order_input_condition_by_index(order, condition_index)
        if not condition_dict:
            return None

        return self._build_mock_order_condition_from_order(order, condition_dict, condition_index)

    def _resolve_order_condition(self, order_condition_id: int):
        condition = self.repository.get_order_condition_by_id(order_condition_id)
        if condition:
            return condition
        return self._resolve_mock_order_condition(order_condition_id)

    def _get_condition_external_meta(self, condition) -> Dict[str, Any]:
        return self._normalize_dict(getattr(condition, "external_meta", None))

    def _get_condition_order(self, condition):
        order_id = self._to_int(getattr(condition, "order_id", 0), 0)
        if order_id <= 0:
            return None
        return self.repository.get_order_by_id(order_id)

    def _get_condition_order_status(self, condition) -> Optional[int]:
        external_meta = self._get_condition_external_meta(condition)
        if "orderStatus" in external_meta:
            return self._to_int(external_meta.get("orderStatus"), 0)

        order = self._get_condition_order(condition)
        if not order:
            return None
        return self._to_int(getattr(order, "status", None), 0)

    def _get_condition_mock_position(self, condition) -> Tuple[int, int]:
        external_meta = self._get_condition_external_meta(condition)
        index = self._to_int(external_meta.get("conditionIndex"), 0)
        total = self._to_int(external_meta.get("totalConditions"), 0)
        if index > 0 and total > 0:
            return index, total

        order = self._get_condition_order(condition)
        if not order:
            return max(index, 1), max(total, 1)

        persisted_conditions = self.repository.get_order_conditions(order.id)
        condition_id = self._to_int(getattr(condition, "condition_id", 0), 0)
        if persisted_conditions:
            total = len(persisted_conditions)
            for current_index, item in enumerate(persisted_conditions, start=1):
                if getattr(item, "id", None) == getattr(condition, "id", None):
                    return current_index, total
                if self._to_int(getattr(item, "condition_id", 0), 0) == condition_id and condition_id > 0:
                    return current_index, total

        input_conditions = self._get_order_input_conditions(order)
        total = len(input_conditions)
        target_fold_type_id = self._to_int(getattr(condition, "fold_type_id", 0), 0)
        target_sim_type_id = self._to_int(getattr(condition, "sim_type_id", 0), 0)
        for current_index, item in enumerate(input_conditions, start=1):
            current_condition_id = self._to_int(item.get("conditionId", item.get("condition_id")), 0)
            current_fold_type_id = self._to_int(item.get("foldTypeId", item.get("fold_type_id")), 0)
            current_sim_type_id = self._to_int(item.get("simTypeId", item.get("sim_type_id")), 0)
            if condition_id > 0 and current_condition_id == condition_id:
                return current_index, max(total, 1)
            if (
                current_fold_type_id == target_fold_type_id
                and current_sim_type_id == target_sim_type_id
                and (target_fold_type_id > 0 or target_sim_type_id > 0)
            ):
                return current_index, max(total, 1)

        return max(index, 1), max(total, 1)

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
            elif index <= max(self._to_int(getattr(condition, "output_count", 0), 0), 1):
                names.append(f"output{index}")

        if names:
            return names

        output_count = self._to_int(getattr(condition, "output_count", 0), 0)
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

    def _resolve_mock_condition_mode(self, condition) -> str:
        order_status = self._get_condition_order_status(condition)
        condition_index, total_conditions = self._get_condition_mock_position(condition)

        if order_status in (0, 4):
            return "pending"
        if order_status == 2:
            return "completed"
        if order_status == 1:
            running_index = 1 if total_conditions <= 1 else min(2, total_conditions)
            if condition_index < running_index:
                return "completed"
            if condition_index == running_index:
                return "running"
            return "pending"
        if order_status == 3:
            failed_index = 1 if total_conditions <= 1 else min(2, total_conditions)
            if condition_index < failed_index:
                return "completed"
            if condition_index == failed_index:
                return "failed"
            return "pending"
        if order_status == 5:
            canceled_index = 1 if total_conditions <= 1 else min(2, total_conditions)
            if condition_index < canceled_index:
                return "completed"
            return "pending"

        raw_status = int(getattr(condition, "status", 0) or 0)
        raw_process = float(getattr(condition, "process", 0) or 0)

        if raw_status == 2:
            return "completed"
        if raw_status == 3:
            return "failed"
        if raw_status == 1 or raw_process > 0:
            return "running"

        seed = int(getattr(condition, "condition_id", 0) or 0) + int(
            getattr(condition, "sim_type_id", 0) or 0
        )
        return ("completed", "running", "failed")[seed % 3]

    def _resolve_mock_total_rounds(self, condition) -> int:
        persisted_total = max(self._to_int(getattr(condition, "round_total", 0), 0), 0)
        if persisted_total > 200:
            return persisted_total

        condition_index, total_conditions = self._get_condition_mock_position(condition)
        order = self._get_condition_order(condition)
        order_id = self._to_int(getattr(order, "id", 0), 0) if order else 0
        condition_id = self._to_int(getattr(condition, "condition_id", 0), 0)
        sim_type_id = self._to_int(getattr(condition, "sim_type_id", 0), 0)

        if total_conditions >= 3 and condition_index == total_conditions:
            return 20_000 if order_id % 2 == 0 else 2_000
        if total_conditions >= 2 and condition_index == total_conditions - 1:
            return 2_000 if order_id % 3 == 0 else 200

        small_round_options = [12, 24, 36, 48, 72, 96, 120, 144, 168, 200]
        seed = (order_id * 31 + condition_id * 17 + sim_type_id * 13 + condition_index * 7) % len(
            small_round_options
        )
        return max(small_round_options[seed], persisted_total or 1)

    def _build_mock_condition_statistics(self, condition) -> Dict[str, Any]:
        total_rounds = max(self._resolve_mock_total_rounds(condition), 1)
        mode = self._resolve_mock_condition_mode(condition)

        if mode == "pending":
            completed_rounds = 0
            failed_rounds = 0
            running_rounds = 0
            progress_percent = 0.0
            status = 0
            running_module = None
        elif mode == "completed":
            completed_rounds = total_rounds
            failed_rounds = 0
            running_rounds = 0
            progress_percent = 100.0
            status = 2
            running_module = None
        elif mode == "failed":
            failed_rounds = min(max(total_rounds // 4, 1), total_rounds)
            completed_rounds = max(total_rounds - failed_rounds, 0)
            running_rounds = 0
            progress_percent = 100.0
            status = 3
            running_module = "SOLVE"
        else:
            failed_rounds = 1 if total_rounds >= 6 else 0
            running_rounds = 1
            completed_rounds = max(total_rounds - failed_rounds - running_rounds, 0)
            progress_percent = (
                round(((completed_rounds + failed_rounds) / total_rounds) * 100, 2)
                if total_rounds > 0
                else 0.0
            )
            status = 1
            running_module = "POST"

        return {
            "mode": mode,
            "status": status,
            "process": progress_percent,
            "runningModule": running_module,
            "totalRounds": total_rounds,
            "completedRounds": completed_rounds,
            "failedRounds": failed_rounds,
            "runningRounds": running_rounds,
            "progressPercent": progress_percent,
        }

    def _apply_mock_condition_summary(self, condition, payload: Dict[str, Any]) -> Dict[str, Any]:
        summary = self._build_mock_condition_statistics(condition)
        payload["status"] = summary["status"]
        payload["process"] = summary["process"]
        payload["runningModule"] = summary["runningModule"]
        payload["statistics"] = {
            **self._normalize_dict(payload.get("statistics")),
            "totalRounds": summary["totalRounds"],
            "completedRounds": summary["completedRounds"],
            "failedRounds": summary["failedRounds"],
            "runningRounds": summary["runningRounds"],
            "progressPercent": summary["progressPercent"],
        }
        payload["resultSource"] = "mock"
        return payload

    def _build_mock_round_item(
        self,
        condition,
        round_index: int,
        summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        algorithm_type = str(getattr(condition, "algorithm_type", "") or "").upper()
        is_bayesian = algorithm_type == "BAYESIAN"
        param_names = self._extract_param_names(condition)
        output_names = self._extract_output_names(condition)
        total_rounds = max(self._resolve_mock_total_rounds(condition), 1)

        param_values: Dict[str, Any] = {}
        for idx, name in enumerate(param_names, start=1):
            param_values[name] = round(10 + round_index * 1.25 + idx * 0.33, 4)

        mode = str(summary.get("mode") or "running")
        if mode == "pending":
            return {
                "id": f"mock-{condition.id}-{round_index}",
                "orderConditionId": condition.id,
                "optIssueId": condition.opt_issue_id,
                "optJobId": condition.opt_job_id,
                "roundIndex": round_index,
                "algorithmType": algorithm_type or None,
                "status": 0,
                "params": param_values,
                "outputs": {},
                "runningModule": None,
                "process": 0,
                "moduleDetails": self._build_module_details(
                    is_running=False,
                    is_failed=False,
                    is_pending=True,
                ),
                "finalResult": None,
            }

        output_values: Dict[str, Any] = {}
        weighted_total = 0.0
        for idx, name in enumerate(output_names, start=1):
            base_value = round(40 + round_index * 2.15 + idx * 1.07, 4)
            output_values[name] = base_value
            if is_bayesian:
                weighted_value = round(base_value * (0.2 + idx * 0.15), 4)
                output_values[f"{name}Weighted"] = weighted_value
                weighted_total += weighted_value

        failed_rounds = self._to_int(summary.get("failedRounds"), 0)
        running_rounds = self._to_int(summary.get("runningRounds"), 0)
        is_running = mode == "running" and running_rounds > 0 and round_index == total_rounds
        failed_start_index = total_rounds - failed_rounds + 1 if failed_rounds > 0 else total_rounds + 1
        is_failed = not is_running and failed_rounds > 0 and round_index >= failed_start_index

        modules = self._build_module_details(
            is_running=is_running,
            is_failed=is_failed,
            is_pending=False,
        )
        progress = 78 if is_running else 100
        running_module = summary.get("runningModule") if is_running else "DONE"
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
        total = max(self._resolve_mock_total_rounds(condition), 1)
        condition_payload = self._serialize_order_condition(condition, include_mock_summary=True)
        summary = self._normalize_dict(condition_payload.get("statistics"))
        page = max(page, 1)
        page_size = max(page_size, 1)

        if status is None:
            filtered_total = total
            start = (page - 1) * page_size + 1
            end = min(start + page_size - 1, filtered_total)
            indices = range(start, end + 1) if start <= filtered_total else []
            items = [
                self._build_mock_round_item(condition, round_index, summary)
                for round_index in indices
            ]
        else:
            filtered_items = [
                self._build_mock_round_item(condition, round_index, summary)
                for round_index in range(1, total + 1)
            ]
            filtered_items = [item for item in filtered_items if item["status"] == status]
            filtered_total = len(filtered_items)
            start = (page - 1) * page_size + 1
            end = min(start + page_size - 1, filtered_total)
            items = filtered_items[start - 1:end] if start <= filtered_total else []

        completed = self._to_int(summary.get("completedRounds"), 0)
        failed = self._to_int(summary.get("failedRounds"), 0)
        running = self._to_int(summary.get("runningRounds"), 0)
        progress_percent = float(summary.get("progressPercent", 0) or 0)

        return {
            "orderCondition": condition_payload,
            "resultSource": "mock",
            "algorithmType": getattr(condition, "algorithm_type", None),
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
    def _build_module_details(
        is_running: bool,
        is_failed: bool,
        is_pending: bool = False,
    ) -> List[Dict[str, Any]]:
        if is_pending:
            stages = [
                ("PREPARE", "未开始", 0, None, "pending"),
                ("SOLVE", "未开始", 0, None, "pending"),
                ("POST", "未开始", 0, None, "pending"),
            ]
        elif is_failed:
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
