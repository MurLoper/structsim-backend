import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pymysql
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def parse_json(value: Any, default: Any):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return default
    return default


def ensure_dict(value: Any) -> Dict[str, Any]:
    parsed = parse_json(value, value)
    return parsed if isinstance(parsed, dict) else {}


def ensure_list(value: Any) -> List[Any]:
    parsed = parse_json(value, value)
    return parsed if isinstance(parsed, list) else []


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def dedupe_ints(values: List[int]) -> List[int]:
    seen = set()
    result: List[int] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def snake_to_camel_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    mapping = {
        "template_set_id": "templateSetId",
        "template_item_id": "templateItemId",
        "custom_values": "customValues",
        "opt_params": "optParams",
        "output_set_id": "outputSetId",
        "selected_condition_ids": "selectedConditionIds",
        "condition_values": "conditionValues",
        "selected_output_ids": "selectedOutputIds",
        "resp_details": "respDetails",
        "solver_id": "solverId",
        "solver_version": "solverVersion",
        "cpu_type": "cpuType",
        "cpu_cores": "cpuCores",
        "apply_global": "applyGlobal",
        "use_global_config": "useGlobalConfig",
        "resource_id": "resourceId",
        "care_device_ids": "careDeviceIds",
        "condition_remark": "conditionRemark",
        "param_name": "paramName",
        "min_value": "minValue",
        "max_value": "maxValue",
        "init_value": "initValue",
        "range_list": "rangeList",
        "alg_type": "algType",
        "doe_param_csv_path": "doeParamCsvPath",
        "doe_param_json_path": "doeParamJsonPath",
        "doe_param_heads": "doeParamHeads",
        "doe_param_data": "doeParamData",
        "batch_size_type": "batchSizeType",
        "batch_size": "batchSize",
        "custom_batch_size": "customBatchSize",
        "max_iter": "maxIter",
        "start_index": "startIndex",
        "end_index": "endIndex",
        "output_type": "outputType",
        "integration_point": "integrationPoint",
        "step_name": "stepName",
        "special_output_set": "specialOutputSet",
        "lower_limit": "lowerLimit",
        "upper_limit": "upperLimit",
        "target_value": "targetValue",
        "target_type": "targetType",
        "file_id": "fileId",
        "origin_fold_type_id": "originFoldTypeId",
        "participant_ids": "participantIds",
        "project_id": "projectId",
        "project_name": "projectName",
        "project_info": "projectInfo",
        "model_level_id": "modelLevelId",
        "origin_file": "originFile",
        "global_solver": "globalSolver",
        "inp_sets": "inpSets",
        "apply_to_all": "applyToAll",
        "condition_id": "conditionId",
        "fold_type_id": "foldTypeId",
        "fold_type_name": "foldTypeName",
        "sim_type_id": "simTypeId",
        "sim_type_name": "simTypeName",
    }
    for key, value in payload.items():
        camel_key = mapping.get(key, key)
        if isinstance(value, dict):
            result[camel_key] = snake_to_camel_payload(value)
        elif isinstance(value, list):
            result[camel_key] = [
                snake_to_camel_payload(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[camel_key] = value
    return result


def estimate_rounds_from_opt_params(opt_params: Optional[Dict[str, Any]]) -> int:
    if not isinstance(opt_params, dict):
        return 0

    alg_type = to_int(opt_params.get("algType", opt_params.get("alg_type", 2)), 2)
    if alg_type in (2, 5):
        doe_data = opt_params.get("doeParamData", opt_params.get("doe_param_data"))
        return len(doe_data) if isinstance(doe_data, list) else 0

    if alg_type != 1:
        return 0

    batch_size_type = to_int(opt_params.get("batchSizeType", opt_params.get("batch_size_type", 1)), 1)
    batch_size = opt_params.get("batchSize", opt_params.get("batch_size")) or []
    max_iter = to_int(opt_params.get("maxIter", opt_params.get("max_iter", len(batch_size) or 1)), 1)
    max_iter = max(max_iter, 0)

    if batch_size_type == 2:
        custom = opt_params.get("customBatchSize", opt_params.get("custom_batch_size")) or []
        total = 0
        for idx in range(1, max_iter + 1):
            value = 0
            for item in custom:
                if not isinstance(item, dict):
                    continue
                start = to_int(item.get("startIndex", item.get("start_index")), 0)
                end = to_int(item.get("endIndex", item.get("end_index")), 0)
                if start <= idx <= end:
                    value = to_int(item.get("value"), 0)
                    break
            total += max(value, 0)
        return total

    values: List[int] = []
    for item in batch_size:
        if isinstance(item, dict):
            values.append(max(to_int(item.get("value"), 0), 0))
        else:
            values.append(max(to_int(item, 0), 0))

    if max_iter <= 0 or not values:
        return 0
    if len(values) >= max_iter:
        return sum(values[:max_iter])
    if len(values) == 1:
        return values[0] * max_iter
    return sum(values) + values[-1] * (max_iter - len(values))


def extract_algorithm_type(condition: Dict[str, Any]) -> Optional[str]:
    params = ensure_dict(condition.get("params"))
    opt_params = ensure_dict(params.get("optParams", params.get("opt_params")))
    raw_alg = opt_params.get("algType", opt_params.get("alg_type"))
    if raw_alg in (1, "1", "bayesian", "BAYESIAN"):
        return "BAYESIAN"
    if raw_alg in (5, "5"):
        return "DOE_FILE"
    if raw_alg in (2, "2", "doe", "DOE"):
        return "DOE"
    return str(raw_alg) if raw_alg is not None else None


def extract_output_count(condition: Dict[str, Any]) -> int:
    output = ensure_dict(condition.get("output"))
    resp_details = output.get("respDetails", output.get("resp_details"))
    if isinstance(resp_details, list):
        return len(resp_details)
    selected = output.get("selectedOutputIds", output.get("selected_output_ids"))
    if isinstance(selected, list):
        return len(selected)
    return 0


def extract_solver_id(condition: Dict[str, Any]) -> Optional[str]:
    solver = ensure_dict(condition.get("solver"))
    solver_id = solver.get("solverId", solver.get("solver_id"))
    if solver_id is None:
        return None
    version = solver.get("solverVersion", solver.get("solver_version"))
    return f"{solver_id}_{version}" if version else str(solver_id)


def normalize_inp_sets(value: Any) -> List[Any]:
    items = ensure_list(value)
    return [snake_to_camel_payload(item) if isinstance(item, dict) else item for item in items]


def normalize_param_config(raw_value: Any) -> Dict[str, Any]:
    params = snake_to_camel_payload(ensure_dict(raw_value))
    params.setdefault("mode", "template")
    params.setdefault("templateSetId", None)
    params.setdefault("templateItemId", None)
    params.setdefault("algorithm", "doe")
    params.setdefault("customValues", {})
    params["optParams"] = snake_to_camel_payload(ensure_dict(params.get("optParams")))
    params["optParams"].setdefault("algType", 2)
    params["optParams"].setdefault("domain", [])
    params["optParams"].setdefault("batchSizeType", 1)
    params["optParams"].setdefault("batchSize", [{"value": 1}])
    params["optParams"].setdefault("maxIter", 1)
    params["optParams"].setdefault("doeParamHeads", [])
    params["optParams"].setdefault("doeParamData", [])
    return params


def normalize_output_config(raw_value: Any) -> Dict[str, Any]:
    output = snake_to_camel_payload(ensure_dict(raw_value))
    output.setdefault("mode", "template")
    output.setdefault("outputSetId", None)
    output.setdefault("selectedConditionIds", [])
    output.setdefault("conditionValues", {})
    output.setdefault("selectedOutputIds", [])
    output.setdefault("respDetails", [])
    return output


def normalize_solver_config(raw_value: Any, default_solver: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    solver = snake_to_camel_payload(ensure_dict(raw_value))
    if default_solver:
        merged = dict(default_solver)
        merged.update({key: value for key, value in solver.items() if value is not None})
        solver = merged
    solver.setdefault("solverId", 1)
    solver.setdefault("solverVersion", "2024")
    solver.setdefault("cpuType", 1)
    solver.setdefault("cpuCores", 16)
    solver.setdefault("double", 0)
    solver.setdefault("applyGlobal", None)
    solver.setdefault("useGlobalConfig", 0)
    solver.setdefault("resourceId", None)
    return solver


@dataclass
class LookupData:
    sim_type_names: Dict[int, str]
    fold_type_names: Dict[int, str]
    condition_config_map: Dict[Tuple[int, int], int]


def load_lookup_data(cur) -> LookupData:
    cur.execute("SELECT id, name FROM sim_types")
    sim_type_names = {int(row["id"]): row["name"] for row in cur.fetchall()}

    cur.execute("SELECT id, name FROM fold_types")
    fold_type_names = {int(row["id"]): row["name"] for row in cur.fetchall()}
    fold_type_names.setdefault(0, "展开态")

    cur.execute("SELECT id, fold_type_id, sim_type_id FROM condition_configs")
    condition_config_map = {
        (int(row["fold_type_id"]), int(row["sim_type_id"])): int(row["id"])
        for row in cur.fetchall()
    }
    return LookupData(
        sim_type_names=sim_type_names,
        fold_type_names=fold_type_names,
        condition_config_map=condition_config_map,
    )


def build_origin_file(order: Dict[str, Any], current_project_info: Dict[str, Any]) -> Dict[str, Any]:
    origin_file = snake_to_camel_payload(ensure_dict(current_project_info.get("originFile")))
    file_type = to_int(origin_file.get("type", order.get("origin_file_type")), 1)
    file_id = origin_file.get("fileId", order.get("origin_file_id"))
    path = origin_file.get("path", order.get("origin_file_path"))
    name = origin_file.get("name", order.get("origin_file_name"))
    normalized = {
        "type": file_type,
        "path": path or (str(file_id) if file_type == 2 and file_id is not None else ""),
        "name": name or path or (str(file_id) if file_id is not None else ""),
        "verified": bool(origin_file.get("verified", True)),
        "verifiedName": origin_file.get("verifiedName") or name or None,
        "verifiedPath": origin_file.get("verifiedPath") or path or None,
        "fileId": file_id,
    }
    return normalized


def build_project_info(order: Dict[str, Any], current_input_json: Dict[str, Any]) -> Dict[str, Any]:
    current_project_info = snake_to_camel_payload(
        ensure_dict(current_input_json.get("projectInfo", current_input_json.get("project_info")))
    )
    participant_ids = current_project_info.get("participantIds")
    if not isinstance(participant_ids, list):
        participant_ids = [str(item) for item in ensure_list(order.get("participant_uids"))]
    else:
        participant_ids = [str(item) for item in participant_ids]

    return {
        "projectId": to_int(current_project_info.get("projectId", order.get("project_id")), 0),
        "projectName": current_project_info.get("projectName"),
        "modelLevelId": to_int(current_project_info.get("modelLevelId", order.get("model_level_id")), 1),
        "originFile": build_origin_file(order, current_project_info),
        "originFoldTypeId": current_project_info.get("originFoldTypeId", order.get("origin_fold_type_id")),
        "participantIds": participant_ids,
        "issueTitle": current_project_info.get("issueTitle"),
        "remark": current_project_info.get("remark", order.get("remark")),
    }


def pick_primary_fold_type(order: Dict[str, Any], lookup: LookupData) -> Tuple[int, str]:
    fold_type_ids = [to_int(item, 0) for item in ensure_list(order.get("fold_type_ids"))]
    fold_type_ids = [item for item in fold_type_ids if item >= 0]
    fold_type_id = fold_type_ids[0] if fold_type_ids else to_int(order.get("fold_type_id"), 0)
    fold_type_name = lookup.fold_type_names.get(fold_type_id, f"目标姿态-{fold_type_id}")
    return fold_type_id, fold_type_name


def normalize_condition(
    order: Dict[str, Any],
    raw_condition: Dict[str, Any],
    lookup: LookupData,
    index: int,
) -> Optional[Dict[str, Any]]:
    condition = snake_to_camel_payload(ensure_dict(raw_condition))
    fold_type_id = to_int(condition.get("foldTypeId"), to_int(order.get("origin_fold_type_id"), 0))
    sim_type_id = to_int(condition.get("simTypeId"), 0)
    if sim_type_id <= 0:
        return None

    condition_id = to_int(condition.get("conditionId"), 0)
    if condition_id <= 0:
        condition_id = lookup.condition_config_map.get((fold_type_id, sim_type_id), 9_200_000 + to_int(order.get("id"), 0) * 100 + index)

    care_device_ids = ensure_list(condition.get("careDeviceIds"))
    return {
        "conditionId": condition_id,
        "foldTypeId": fold_type_id,
        "foldTypeName": condition.get("foldTypeName") or lookup.fold_type_names.get(fold_type_id, f"目标姿态-{fold_type_id}"),
        "simTypeId": sim_type_id,
        "simTypeName": condition.get("simTypeName") or lookup.sim_type_names.get(sim_type_id, f"仿真类型-{sim_type_id}"),
        "params": normalize_param_config(condition.get("params")),
        "output": normalize_output_config(condition.get("output")),
        "solver": normalize_solver_config(condition.get("solver")),
        "careDeviceIds": [str(item) for item in care_device_ids],
        "remark": condition.get("remark") or condition.get("conditionRemark") or order.get("remark"),
    }


def normalize_existing_conditions(
    order: Dict[str, Any],
    current_input_json: Dict[str, Any],
    lookup: LookupData,
) -> List[Dict[str, Any]]:
    conditions: List[Dict[str, Any]] = []
    for index, raw_condition in enumerate(ensure_list(current_input_json.get("conditions")), start=1):
        if not isinstance(raw_condition, dict):
            continue
        normalized = normalize_condition(order, raw_condition, lookup, index)
        if normalized:
            conditions.append(normalized)
    return conditions


def build_global_solver(current_input_json: Dict[str, Any], first_solver: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    global_solver = snake_to_camel_payload(
        ensure_dict(current_input_json.get("globalSolver", current_input_json.get("global_solver")))
    )
    normalized = normalize_solver_config(global_solver, first_solver)
    normalized["applyToAll"] = bool(global_solver.get("applyToAll", True))
    return normalized


def build_conditions_from_opt_param(
    order: Dict[str, Any],
    current_input_json: Dict[str, Any],
    lookup: LookupData,
) -> List[Dict[str, Any]]:
    opt_param = ensure_dict(current_input_json.get("opt_param"))
    if not opt_param:
        opt_param = ensure_dict(order.get("opt_param"))
    if not opt_param:
        return []

    fold_type_id, fold_type_name = pick_primary_fold_type(order, lookup)
    conditions: List[Dict[str, Any]] = []
    for index, (raw_key, raw_value) in enumerate(opt_param.items(), start=1):
        old_cfg = snake_to_camel_payload(ensure_dict(raw_value))
        sim_type_id = to_int(old_cfg.get("simTypeId", raw_key), to_int(raw_key, index))
        if sim_type_id <= 0:
            continue
        condition_id = lookup.condition_config_map.get((fold_type_id, sim_type_id), 9_000_000 + to_int(order["id"], 0) * 100 + index)
        care_device_ids = ensure_list(old_cfg.get("careDeviceIds"))
        conditions.append(
            {
                "conditionId": condition_id,
                "foldTypeId": fold_type_id,
                "foldTypeName": fold_type_name,
                "simTypeId": sim_type_id,
                "simTypeName": lookup.sim_type_names.get(sim_type_id, f"仿真类型-{sim_type_id}"),
                "params": normalize_param_config(old_cfg.get("params")),
                "output": normalize_output_config(old_cfg.get("output")),
                "solver": normalize_solver_config(old_cfg.get("solver")),
                "careDeviceIds": [str(item) for item in care_device_ids],
                "remark": old_cfg.get("remark") or old_cfg.get("conditionRemark") or order.get("remark"),
            }
        )
    return conditions


def build_conditions_from_sim_types(order: Dict[str, Any], lookup: LookupData) -> List[Dict[str, Any]]:
    sim_type_ids = [to_int(item, 0) for item in ensure_list(order.get("sim_type_ids"))]
    sim_type_ids = [item for item in sim_type_ids if item > 0]
    if not sim_type_ids:
        return []

    fold_type_id, fold_type_name = pick_primary_fold_type(order, lookup)
    conditions: List[Dict[str, Any]] = []
    for index, sim_type_id in enumerate(sim_type_ids, start=1):
        condition_id = lookup.condition_config_map.get((fold_type_id, sim_type_id), 9_100_000 + to_int(order["id"], 0) * 100 + index)
        conditions.append(
            {
                "conditionId": condition_id,
                "foldTypeId": fold_type_id,
                "foldTypeName": fold_type_name,
                "simTypeId": sim_type_id,
                "simTypeName": lookup.sim_type_names.get(sim_type_id, f"仿真类型-{sim_type_id}"),
                "params": normalize_param_config({}),
                "output": normalize_output_config({}),
                "solver": normalize_solver_config({}),
                "careDeviceIds": [],
                "remark": order.get("remark"),
            }
        )
    return conditions


def build_condition_summary(conditions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    summary: Dict[str, List[str]] = {}
    for condition in conditions:
        fold_name = condition.get("foldTypeName") or f"目标姿态-{condition.get('foldTypeId', 0)}"
        sim_name = condition.get("simTypeName") or f"仿真类型-{condition.get('simTypeId', 0)}"
        summary.setdefault(str(fold_name), [])
        if sim_name not in summary[str(fold_name)]:
            summary[str(fold_name)].append(str(sim_name))
    return summary


def build_order_input_json(order: Dict[str, Any], lookup: LookupData) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    current_input_json = snake_to_camel_payload(ensure_dict(order.get("input_json")))
    current_input_json.pop("opt_param", None)

    conditions = normalize_existing_conditions(order, current_input_json, lookup)
    if not conditions:
        conditions = build_conditions_from_opt_param(order, current_input_json, lookup)
    if not conditions:
        conditions = build_conditions_from_sim_types(order, lookup)
    if not conditions:
        return None, []

    first_solver = conditions[0]["solver"] if conditions else None
    input_json = {
        "version": max(to_int(current_input_json.get("version"), 2), 2),
        "projectInfo": build_project_info(order, current_input_json),
        "conditions": conditions,
        "globalSolver": build_global_solver(current_input_json, first_solver),
        "inpSets": normalize_inp_sets(current_input_json.get("inpSets")),
    }
    return input_json, conditions


def build_condition_rows(order: Dict[str, Any], conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now_ts = int(time.time())
    rows: List[Dict[str, Any]] = []
    for condition in conditions:
        params = ensure_dict(condition.get("params"))
        round_total = estimate_rounds_from_opt_params(ensure_dict(params.get("optParams")))
        rows.append(
            {
                "order_id": to_int(order["id"], 0),
                "order_no": order.get("order_no"),
                "opt_issue_id": to_int(order.get("opt_issue_id"), 0),
                "opt_job_id": None,
                "condition_id": to_int(condition.get("conditionId"), 0),
                "fold_type_id": to_int(condition.get("foldTypeId"), 0),
                "fold_type_name": condition.get("foldTypeName"),
                "sim_type_id": to_int(condition.get("simTypeId"), 0),
                "sim_type_name": condition.get("simTypeName"),
                "algorithm_type": extract_algorithm_type(condition),
                "round_total": round_total,
                "output_count": extract_output_count(condition),
                "solver_id": extract_solver_id(condition),
                "care_device_ids": condition.get("careDeviceIds") or [],
                "remark": condition.get("remark") or order.get("remark"),
                "running_module": None,
                "process": 0,
                "status": 0,
                "statistics_json": None,
                "result_summary_json": None,
                "condition_snapshot": condition,
                "external_meta": {"normalizedFromLegacy": True},
                "created_at": now_ts,
                "updated_at": now_ts,
            }
        )
    return rows


def should_refresh_order(order: Dict[str, Any], input_json: Dict[str, Any], conditions: List[Dict[str, Any]], opti_count: int) -> bool:
    current_input_json = snake_to_camel_payload(ensure_dict(order.get("input_json")))
    current_input_json.pop("opt_param", None)
    current_conditions = normalize_inp_sets(current_input_json.get("conditions"))
    stored_opt_param = ensure_dict(order.get("opt_param"))
    stored_sim_type_ids = [to_int(item, 0) for item in ensure_list(order.get("sim_type_ids"))]
    stored_fold_type_ids = [to_int(item, 0) for item in ensure_list(order.get("fold_type_ids"))]
    next_sim_type_ids = dedupe_ints([to_int(item.get("simTypeId"), 0) for item in conditions if to_int(item.get("simTypeId"), 0) > 0])
    next_fold_type_ids = dedupe_ints([to_int(item.get("foldTypeId"), 0) for item in conditions if to_int(item.get("foldTypeId"), 0) >= 0])
    next_summary = build_condition_summary(conditions)

    if stored_opt_param:
        return True
    if ensure_dict(ensure_dict(order.get("input_json")).get("opt_param")):
        return True
    if opti_count != len(conditions):
        return True
    if stored_sim_type_ids != next_sim_type_ids:
        return True
    if stored_fold_type_ids != next_fold_type_ids:
        return True
    if ensure_dict(order.get("condition_summary")) != next_summary:
        return True

    current_json_text = json.dumps(current_input_json, ensure_ascii=False, sort_keys=True)
    next_json_text = json.dumps(input_json, ensure_ascii=False, sort_keys=True)
    current_condition_text = json.dumps(current_conditions, ensure_ascii=False, sort_keys=True)
    next_condition_text = json.dumps(conditions, ensure_ascii=False, sort_keys=True)
    return current_json_text != next_json_text or current_condition_text != next_condition_text


def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not configured")

    parsed = urlparse(db_url)
    conn = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

    updated_orders: List[int] = []
    skipped_orders: List[int] = []

    try:
        with conn.cursor() as cur:
            lookup = load_lookup_data(cur)
            cur.execute(
                """
                SELECT o.*,
                       (SELECT COUNT(*) FROM order_condition_opti oc WHERE oc.order_id = o.id) AS opti_count
                FROM orders o
                ORDER BY o.id ASC
                """
            )
            orders = cur.fetchall()

            for order in orders:
                input_json, conditions = build_order_input_json(order, lookup)
                if not input_json or not conditions:
                    skipped_orders.append(to_int(order["id"], 0))
                    continue

                opti_count = to_int(order.get("opti_count"), 0)
                if not should_refresh_order(order, input_json, conditions, opti_count):
                    skipped_orders.append(to_int(order["id"], 0))
                    continue

                rows = build_condition_rows(order, conditions)
                condition_summary = build_condition_summary(conditions)
                sim_type_ids = dedupe_ints(
                    [condition["simTypeId"] for condition in conditions if to_int(condition.get("simTypeId"), 0) > 0]
                )
                fold_type_ids = dedupe_ints(
                    [condition["foldTypeId"] for condition in conditions if to_int(condition.get("foldTypeId"), 0) >= 0]
                )
                now_ts = int(time.time())

                cur.execute(
                    """
                    UPDATE orders
                    SET input_json=%s,
                        opt_param=%s,
                        sim_type_ids=%s,
                        fold_type_ids=%s,
                        condition_summary=%s,
                        updated_at=%s
                    WHERE id=%s
                    """,
                    (
                        json.dumps(input_json, ensure_ascii=False),
                        None,
                        json.dumps(sim_type_ids, ensure_ascii=False),
                        json.dumps(fold_type_ids, ensure_ascii=False),
                        json.dumps(condition_summary, ensure_ascii=False),
                        now_ts,
                        order["id"],
                    ),
                )

                cur.execute("DELETE FROM order_condition_opti WHERE order_id=%s", (order["id"],))
                if rows:
                    cur.executemany(
                        """
                        INSERT INTO order_condition_opti (
                            order_id, order_no, opt_issue_id, opt_job_id, condition_id,
                            fold_type_id, fold_type_name, sim_type_id, sim_type_name,
                            algorithm_type, round_total, output_count, solver_id,
                            care_device_ids, remark, running_module, process, status,
                            statistics_json, result_summary_json, condition_snapshot,
                            external_meta, created_at, updated_at
                        ) VALUES (
                            %(order_id)s, %(order_no)s, %(opt_issue_id)s, %(opt_job_id)s, %(condition_id)s,
                            %(fold_type_id)s, %(fold_type_name)s, %(sim_type_id)s, %(sim_type_name)s,
                            %(algorithm_type)s, %(round_total)s, %(output_count)s, %(solver_id)s,
                            %(care_device_ids)s, %(remark)s, %(running_module)s, %(process)s, %(status)s,
                            %(statistics_json)s, %(result_summary_json)s, %(condition_snapshot)s,
                            %(external_meta)s, %(created_at)s, %(updated_at)s
                        )
                        """,
                        [
                            {
                                **row,
                                "care_device_ids": json.dumps(row["care_device_ids"], ensure_ascii=False),
                                "condition_snapshot": json.dumps(row["condition_snapshot"], ensure_ascii=False),
                                "external_meta": json.dumps(row["external_meta"], ensure_ascii=False),
                            }
                            for row in rows
                        ],
                    )

                updated_orders.append(to_int(order["id"], 0))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(json.dumps({"updatedOrders": updated_orders, "skippedOrders": skipped_orders}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
