"""
配置中心路由。

这组接口是前端基础配置页和提单页的主数据入口。资源池和项目-仿真类型旧关系已经下线，
但基础配置 CRUD 仍需要继续保留。
"""
from flask import Blueprint, request
from pydantic import ValidationError

from app.common import error, success
from app.common.errors import NotFoundError
from app.common.serializers import get_snake_json
from app.constants import ErrorCode

from .schemas import (
    CareDeviceCreate,
    CareDeviceUpdate,
    ConditionDefCreate,
    ConditionDefUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    FoldTypeCreate,
    FoldTypeUpdate,
    OutputDefCreate,
    OutputDefUpdate,
    ParamDefCreate,
    ParamDefUpdate,
    ProjectCreate,
    ProjectUpdate,
    SimTypeCreate,
    SimTypeUpdate,
    SolverCreate,
    SolverUpdate,
    StatusDefUpdate,
)
from .service import config_service

config_bp = Blueprint("config", __name__, url_prefix="/config")


def _validation_error(exc: ValidationError):
    return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)


def _not_found_error(exc: NotFoundError):
    return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)


def _payload() -> dict:
    return get_snake_json() or {}


@config_bp.route("/projects", methods=["GET"])
def list_projects():
    return success(config_service.get_projects())


@config_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    try:
        return success(config_service.get_project(project_id))
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/projects", methods=["POST"])
def create_project():
    try:
        payload = ProjectCreate(**_payload())
        return success(config_service.create_project(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id: int):
    try:
        payload = ProjectUpdate(**_payload())
        return success(
            config_service.update_project(project_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id: int):
    try:
        config_service.delete_project(project_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/sim-types", methods=["GET"])
def list_sim_types():
    return success(config_service.get_sim_types())


@config_bp.route("/sim-types", methods=["POST"])
def create_sim_type():
    try:
        payload = SimTypeCreate(**_payload())
        return success(config_service.create_sim_type(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/sim-types/<int:sim_type_id>", methods=["PUT"])
def update_sim_type(sim_type_id: int):
    try:
        payload = SimTypeUpdate(**_payload())
        return success(
            config_service.update_sim_type(sim_type_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/sim-types/<int:sim_type_id>", methods=["DELETE"])
def delete_sim_type(sim_type_id: int):
    try:
        config_service.delete_sim_type(sim_type_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/param-defs", methods=["GET"])
def list_param_defs():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int) or request.args.get("page_size", type=int)
    keyword = request.args.get("keyword", type=str)
    return success(config_service.get_param_defs(page, page_size, keyword))


@config_bp.route("/param-defs", methods=["POST"])
def create_param_def():
    try:
        payload = ParamDefCreate(**_payload())
        return success(config_service.create_param_def(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/param-defs/batch", methods=["POST"])
def batch_create_param_defs():
    return success(config_service.batch_create_param_defs(_payload().get("items", [])), "批量创建完成")


@config_bp.route("/param-defs/<int:param_def_id>", methods=["PUT"])
def update_param_def(param_def_id: int):
    try:
        payload = ParamDefUpdate(**_payload())
        return success(
            config_service.update_param_def(param_def_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/param-defs/<int:param_def_id>", methods=["DELETE"])
def delete_param_def(param_def_id: int):
    try:
        config_service.delete_param_def(param_def_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/solvers", methods=["GET"])
def list_solvers():
    return success(config_service.get_solvers())


@config_bp.route("/solvers", methods=["POST"])
def create_solver():
    try:
        payload = SolverCreate(**_payload())
        return success(config_service.create_solver(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/solvers/<int:solver_id>", methods=["PUT"])
def update_solver(solver_id: int):
    try:
        payload = SolverUpdate(**_payload())
        return success(
            config_service.update_solver(solver_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/solvers/<int:solver_id>", methods=["DELETE"])
def delete_solver(solver_id: int):
    try:
        config_service.delete_solver(solver_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/condition-defs", methods=["GET"])
def list_condition_defs():
    return success(config_service.get_condition_defs())


@config_bp.route("/condition-defs", methods=["POST"])
def create_condition_def():
    try:
        payload = ConditionDefCreate(**_payload())
        return success(config_service.create_condition_def(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/condition-defs/<int:condition_def_id>", methods=["PUT"])
def update_condition_def(condition_def_id: int):
    try:
        payload = ConditionDefUpdate(**_payload())
        return success(
            config_service.update_condition_def(
                condition_def_id, payload.model_dump(exclude_none=True)
            ),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/condition-defs/<int:condition_def_id>", methods=["DELETE"])
def delete_condition_def(condition_def_id: int):
    try:
        config_service.delete_condition_def(condition_def_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/output-defs", methods=["GET"])
def list_output_defs():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int) or request.args.get("page_size", type=int)
    keyword = request.args.get("keyword", type=str)
    return success(config_service.get_output_defs(page, page_size, keyword))


@config_bp.route("/output-defs", methods=["POST"])
def create_output_def():
    try:
        payload = OutputDefCreate(**_payload())
        return success(config_service.create_output_def(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/output-defs/batch", methods=["POST"])
def batch_create_output_defs():
    return success(config_service.batch_create_output_defs(_payload().get("items", [])), "批量创建完成")


@config_bp.route("/output-defs/<int:output_def_id>", methods=["PUT"])
def update_output_def(output_def_id: int):
    try:
        payload = OutputDefUpdate(**_payload())
        return success(
            config_service.update_output_def(output_def_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/output-defs/<int:output_def_id>", methods=["DELETE"])
def delete_output_def(output_def_id: int):
    try:
        config_service.delete_output_def(output_def_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/fold-types", methods=["GET"])
def list_fold_types():
    return success(config_service.get_fold_types())


@config_bp.route("/fold-types", methods=["POST"])
def create_fold_type():
    try:
        payload = FoldTypeCreate(**_payload())
        return success(config_service.create_fold_type(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/fold-types/<int:fold_type_id>", methods=["PUT"])
def update_fold_type(fold_type_id: int):
    try:
        payload = FoldTypeUpdate(**_payload())
        return success(
            config_service.update_fold_type(fold_type_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/fold-types/<int:fold_type_id>", methods=["DELETE"])
def delete_fold_type(fold_type_id: int):
    try:
        config_service.delete_fold_type(fold_type_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/care-devices", methods=["GET"])
def list_care_devices():
    return success(config_service.get_care_devices())


@config_bp.route("/care-devices", methods=["POST"])
def create_care_device():
    try:
        payload = CareDeviceCreate(**_payload())
        return success(config_service.create_care_device(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/care-devices/<int:care_device_id>", methods=["PUT"])
def update_care_device(care_device_id: int):
    try:
        payload = CareDeviceUpdate(**_payload())
        return success(
            config_service.update_care_device(care_device_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/care-devices/<int:care_device_id>", methods=["DELETE"])
def delete_care_device(care_device_id: int):
    try:
        config_service.delete_care_device(care_device_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/departments", methods=["GET"])
def list_departments():
    return success(config_service.get_departments())


@config_bp.route("/departments/<int:parent_id>/children", methods=["GET"])
def list_sub_departments(parent_id: int):
    return success(config_service.get_sub_departments(parent_id))


@config_bp.route("/departments", methods=["POST"])
def create_department():
    try:
        payload = DepartmentCreate(**_payload())
        return success(config_service.create_department(payload.model_dump()), "创建成功")
    except ValidationError as exc:
        return _validation_error(exc)


@config_bp.route("/departments/<int:department_id>", methods=["PUT"])
def update_department(department_id: int):
    try:
        payload = DepartmentUpdate(**_payload())
        return success(
            config_service.update_department(department_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/departments/<int:department_id>", methods=["DELETE"])
def delete_department(department_id: int):
    try:
        config_service.delete_department(department_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/status-defs", methods=["GET"])
def list_status_defs():
    return success(config_service.get_status_defs())


@config_bp.route("/status-defs/<int:status_id>", methods=["PUT"])
def update_status_def(status_id: int):
    try:
        payload = StatusDefUpdate(**_payload())
        return success(
            config_service.update_status_def(status_id, payload.model_dump(exclude_none=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return _validation_error(exc)
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route("/automation-modules", methods=["GET"])
def list_automation_modules():
    return success(config_service.get_automation_modules())


@config_bp.route("/workflows", methods=["GET"])
def list_workflows():
    return success(config_service.get_workflows())


@config_bp.route("/post-process-modes", methods=["GET"])
def list_post_process_modes():
    return success(config_service.get_post_process_modes())


@config_bp.route("/base-data", methods=["GET"])
def get_base_data():
    return success(config_service.get_base_data())


@config_bp.route("/working-conditions", methods=["GET"])
def list_working_conditions():
    return success(config_service.get_working_conditions())


@config_bp.route("/working-conditions/by-fold-type/<int:fold_type_id>", methods=["GET"])
def list_working_conditions_by_fold_type(fold_type_id: int):
    return success(config_service.get_working_conditions_by_fold_type(fold_type_id))


@config_bp.route("/fold-type-sim-type-rels", methods=["GET"])
def list_fold_type_sim_type_rels():
    return success(config_service.get_fold_type_sim_type_rels())


@config_bp.route("/fold-type-sim-type-rels/by-fold-type/<int:fold_type_id>", methods=["GET"])
def list_sim_types_by_fold_type(fold_type_id: int):
    return success(config_service.get_sim_types_by_fold_type(fold_type_id))


@config_bp.route("/fold-type-sim-type-rels/fold-type/<int:fold_type_id>/rels", methods=["GET"])
def list_fold_type_sim_type_rels_by_fold_type(fold_type_id: int):
    return success(config_service.get_fold_type_sim_type_rels_by_fold_type(fold_type_id))


@config_bp.route("/fold-type-sim-type-rels/fold-type/<int:fold_type_id>", methods=["POST"])
def add_sim_type_to_fold_type(fold_type_id: int):
    result = config_service.add_sim_type_to_fold_type(fold_type_id, _payload())
    return success(result, "添加成功")


@config_bp.route(
    "/fold-type-sim-type-rels/fold-type/<int:fold_type_id>/default/<int:sim_type_id>",
    methods=["PUT"],
)
def set_default_sim_type_for_fold_type(fold_type_id: int, sim_type_id: int):
    try:
        config_service.set_default_sim_type_for_fold_type(fold_type_id, sim_type_id)
        return success(msg="设置成功")
    except NotFoundError as exc:
        return _not_found_error(exc)


@config_bp.route(
    "/fold-type-sim-type-rels/fold-type/<int:fold_type_id>/sim-type/<int:sim_type_id>",
    methods=["DELETE"],
)
def remove_sim_type_from_fold_type(fold_type_id: int, sim_type_id: int):
    try:
        config_service.remove_sim_type_from_fold_type(fold_type_id, sim_type_id)
        return success(msg="移除成功")
    except NotFoundError as exc:
        return _not_found_error(exc)
