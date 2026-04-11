"""
配置中心服务。

保留前端当前仍在使用的基础配置接口：
- projects
- sim-types
- param-defs
- solvers
- condition-defs
- output-defs
- fold-types
- care-devices
- departments
- status-defs
- automation-modules
- workflows
- base-data
- working-conditions
- fold-type-sim-type-rels
"""
from typing import Any, Dict, List, Optional

from app.common.errors import NotFoundError
from app.common.serializers import serialize_model, serialize_models
from app.extensions import db
from app.models.config import SimType
from app.models.config_relations import FoldTypeSimTypeRel, WorkingCondition
from app.services.external_data import output_component_repository

from .repository import (
    AutomationModuleRepository,
    CareDeviceRepository,
    ConditionDefRepository,
    DepartmentRepository,
    FoldTypeRepository,
    ModelLevelRepository,
    OutputDefRepository,
    ParamDefRepository,
    ProjectRepository,
    SimTypeRepository,
    SolverRepository,
    StatusDefRepository,
    WorkflowRepository,
)


class ConfigService:
    def __init__(self) -> None:
        self._repos: Dict[str, Any] = {}

    def _get_repo(self, name: str, repo_class):
        if name not in self._repos:
            self._repos[name] = repo_class()
        return self._repos[name]

    @property
    def project_repo(self) -> ProjectRepository:
        return self._get_repo("project", ProjectRepository)

    @property
    def sim_type_repo(self) -> SimTypeRepository:
        return self._get_repo("sim_type", SimTypeRepository)

    @property
    def param_def_repo(self) -> ParamDefRepository:
        return self._get_repo("param_def", ParamDefRepository)

    @property
    def solver_repo(self) -> SolverRepository:
        return self._get_repo("solver", SolverRepository)

    @property
    def condition_def_repo(self) -> ConditionDefRepository:
        return self._get_repo("condition_def", ConditionDefRepository)

    @property
    def output_def_repo(self) -> OutputDefRepository:
        return self._get_repo("output_def", OutputDefRepository)

    @property
    def fold_type_repo(self) -> FoldTypeRepository:
        return self._get_repo("fold_type", FoldTypeRepository)

    @property
    def model_level_repo(self) -> ModelLevelRepository:
        return self._get_repo("model_level", ModelLevelRepository)

    @property
    def care_device_repo(self) -> CareDeviceRepository:
        return self._get_repo("care_device", CareDeviceRepository)

    @property
    def department_repo(self) -> DepartmentRepository:
        return self._get_repo("department", DepartmentRepository)

    @property
    def status_def_repo(self) -> StatusDefRepository:
        return self._get_repo("status_def", StatusDefRepository)

    @property
    def automation_module_repo(self) -> AutomationModuleRepository:
        return self._get_repo("automation_module", AutomationModuleRepository)

    @property
    def workflow_repo(self) -> WorkflowRepository:
        return self._get_repo("workflow", WorkflowRepository)

    def _get_required(self, repo, record_id: int, label: str):
        record = repo.find_by_id(record_id)
        if not record or getattr(record, "valid", 1) != 1:
            raise NotFoundError(f"{label}不存在: {record_id}")
        return record

    def _list(self, repo) -> List[Dict[str, Any]]:
        return serialize_models(repo.find_all_valid())

    def _get(self, repo, record_id: int, label: str) -> Dict[str, Any]:
        return serialize_model(self._get_required(repo, record_id, label))

    def _create(self, repo, data: Dict[str, Any]) -> Dict[str, Any]:
        return serialize_model(repo.create(data))

    def _update(self, repo, record_id: int, data: Dict[str, Any], label: str) -> Dict[str, Any]:
        self._get_required(repo, record_id, label)
        updated = repo.update(record_id, data)
        return serialize_model(updated)

    def _delete(self, repo, record_id: int, label: str) -> None:
        self._get_required(repo, record_id, label)
        repo.soft_delete(record_id)

    # projects
    def get_projects(self) -> List[Dict[str, Any]]:
        return self._list(self.project_repo)

    def get_project(self, project_id: int) -> Dict[str, Any]:
        return self._get(self.project_repo, project_id, "项目")

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.project_repo, data)

    def update_project(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.project_repo, project_id, data, "项目")

    def delete_project(self, project_id: int) -> None:
        self._delete(self.project_repo, project_id, "项目")

    # sim types
    def get_sim_types(self) -> List[Dict[str, Any]]:
        return self._list(self.sim_type_repo)

    def create_sim_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.sim_type_repo, data)

    def update_sim_type(self, sim_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.sim_type_repo, sim_type_id, data, "仿真类型")

    def delete_sim_type(self, sim_type_id: int) -> None:
        self._delete(self.sim_type_repo, sim_type_id, "仿真类型")

    # param defs
    def get_param_defs(
        self, page: Optional[int] = None, page_size: Optional[int] = None, keyword: Optional[str] = None
    ):
        if page:
            result = self.param_def_repo.find_paginated(page, page_size or 20, keyword)
            return {**result, "items": serialize_models(result.get("items", []))}
        return self._list(self.param_def_repo)

    def create_param_def(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.param_def_repo, data)

    def batch_create_param_defs(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        created = []
        skipped = []
        for item in items:
            key = item.get("key")
            if key and self.param_def_repo.find_by_key(key):
                skipped.append({"key": key, "reason": "已存在"})
                continue
            created.append(item)
        created_models = self.param_def_repo.batch_create(created) if created else []
        return {"created": serialize_models(created_models), "skipped": skipped}

    def update_param_def(self, param_def_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.param_def_repo, param_def_id, data, "参数定义")

    def delete_param_def(self, param_def_id: int) -> None:
        self._delete(self.param_def_repo, param_def_id, "参数定义")

    # solvers
    def get_solvers(self) -> List[Dict[str, Any]]:
        return self._list(self.solver_repo)

    def create_solver(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.solver_repo, data)

    def update_solver(self, solver_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.solver_repo, solver_id, data, "求解器")

    def delete_solver(self, solver_id: int) -> None:
        self._delete(self.solver_repo, solver_id, "求解器")

    # condition defs
    def get_condition_defs(self) -> List[Dict[str, Any]]:
        return self._list(self.condition_def_repo)

    def create_condition_def(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.condition_def_repo, data)

    def update_condition_def(self, condition_def_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.condition_def_repo, condition_def_id, data, "工况定义")

    def delete_condition_def(self, condition_def_id: int) -> None:
        self._delete(self.condition_def_repo, condition_def_id, "工况定义")

    # output defs
    def get_output_defs(
        self, page: Optional[int] = None, page_size: Optional[int] = None, keyword: Optional[str] = None
    ):
        if page:
            result = self.output_def_repo.find_paginated(page, page_size or 20, keyword)
            return {**result, "items": serialize_models(result.get("items", []))}
        return self._list(self.output_def_repo)

    def create_output_def(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.output_def_repo, data)

    def batch_create_output_defs(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        created = []
        skipped = []
        for item in items:
            code = item.get("code")
            if code and self.output_def_repo.find_by_code(code):
                skipped.append({"code": code, "reason": "已存在"})
                continue
            created.append(item)
        created_models = self.output_def_repo.batch_create(created) if created else []
        return {"created": serialize_models(created_models), "skipped": skipped}

    def update_output_def(self, output_def_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.output_def_repo, output_def_id, data, "输出定义")

    def delete_output_def(self, output_def_id: int) -> None:
        self._delete(self.output_def_repo, output_def_id, "输出定义")

    # fold types
    def get_fold_types(self) -> List[Dict[str, Any]]:
        return self._list(self.fold_type_repo)

    def create_fold_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.fold_type_repo, data)

    def update_fold_type(self, fold_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.fold_type_repo, fold_type_id, data, "姿态类型")

    def delete_fold_type(self, fold_type_id: int) -> None:
        self._delete(self.fold_type_repo, fold_type_id, "姿态类型")

    # care devices
    def get_care_devices(self) -> List[Dict[str, Any]]:
        return self._list(self.care_device_repo)

    def create_care_device(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.care_device_repo, data)

    def update_care_device(self, care_device_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.care_device_repo, care_device_id, data, "关注器件")

    def delete_care_device(self, care_device_id: int) -> None:
        self._delete(self.care_device_repo, care_device_id, "关注器件")

    # departments
    def get_departments(self) -> List[Dict[str, Any]]:
        return self._list(self.department_repo)

    def create_department(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create(self.department_repo, data)

    def update_department(self, department_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.department_repo, department_id, data, "部门")

    def delete_department(self, department_id: int) -> None:
        self._delete(self.department_repo, department_id, "部门")

    def get_sub_departments(self, parent_id: int) -> List[Dict[str, Any]]:
        return serialize_models(self.department_repo.find_by_parent_id(parent_id))

    # status / automation / workflows / modes / base-data
    def get_status_defs(self) -> List[Dict[str, Any]]:
        return self._list(self.status_def_repo)

    def update_status_def(self, status_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._update(self.status_def_repo, status_id, data, "状态定义")

    def get_automation_modules(self) -> List[Dict[str, Any]]:
        return self._list(self.automation_module_repo)

    def get_workflows(self) -> List[Dict[str, Any]]:
        return self._list(self.workflow_repo)

    def get_post_process_modes(self) -> List[Dict[str, Any]]:
        return output_component_repository.list_components()

    def get_base_data(self) -> Dict[str, Any]:
        return {
            "projects": self.get_projects(),
            "simTypes": self.get_sim_types(),
            "paramDefs": self.get_param_defs(),
            "solvers": self.get_solvers(),
            "conditionDefs": self.get_condition_defs(),
            "outputDefs": self.get_output_defs(),
            "foldTypes": self.get_fold_types(),
            "careDevices": self.get_care_devices(),
            "statusDefs": self.get_status_defs(),
            "automationModules": self.get_automation_modules(),
            "workflows": self.get_workflows(),
            "postProcessModes": self.get_post_process_modes(),
        }

    # working conditions
    def get_working_conditions(self) -> List[Dict[str, Any]]:
        items = (
            WorkingCondition.query.filter_by(valid=1)
            .order_by(WorkingCondition.sort.asc(), WorkingCondition.id.asc())
            .all()
        )
        return [item.to_dict() for item in items]

    def get_working_conditions_by_fold_type(self, fold_type_id: int) -> List[Dict[str, Any]]:
        items = (
            WorkingCondition.query.filter_by(fold_type_id=fold_type_id, valid=1)
            .order_by(WorkingCondition.sort.asc(), WorkingCondition.id.asc())
            .all()
        )
        return [item.to_dict() for item in items]

    # fold-type / sim-type rels
    def get_fold_type_sim_type_rels(self) -> List[Dict[str, Any]]:
        items = (
            FoldTypeSimTypeRel.query.order_by(
                FoldTypeSimTypeRel.fold_type_id.asc(),
                FoldTypeSimTypeRel.sort.asc(),
                FoldTypeSimTypeRel.id.asc(),
            ).all()
        )
        return [item.to_dict() for item in items]

    def get_sim_types_by_fold_type(self, fold_type_id: int) -> List[Dict[str, Any]]:
        rels = (
            FoldTypeSimTypeRel.query.filter_by(fold_type_id=fold_type_id)
            .order_by(FoldTypeSimTypeRel.sort.asc(), FoldTypeSimTypeRel.id.asc())
            .all()
        )
        result: List[Dict[str, Any]] = []
        for rel in rels:
            sim_type = SimType.query.get(rel.sim_type_id)
            if not sim_type or sim_type.valid != 1:
                continue
            item = sim_type.to_dict()
            item["isDefault"] = rel.is_default == 1
            result.append(item)
        return result

    def get_fold_type_sim_type_rels_by_fold_type(self, fold_type_id: int) -> List[Dict[str, Any]]:
        rels = (
            FoldTypeSimTypeRel.query.filter_by(fold_type_id=fold_type_id)
            .order_by(FoldTypeSimTypeRel.sort.asc(), FoldTypeSimTypeRel.id.asc())
            .all()
        )
        result: List[Dict[str, Any]] = []
        for rel in rels:
            item = rel.to_dict()
            sim_type = SimType.query.get(rel.sim_type_id)
            if sim_type:
                item["simTypeName"] = sim_type.name
                item["simTypeCode"] = sim_type.code
            result.append(item)
        return result

    def add_sim_type_to_fold_type(self, fold_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        rel = FoldTypeSimTypeRel(
            fold_type_id=fold_type_id,
            sim_type_id=data["sim_type_id"],
            is_default=data.get("is_default", 0),
            sort=data.get("sort", 100),
        )
        db.session.add(rel)
        db.session.commit()
        return rel.to_dict()

    def set_default_sim_type_for_fold_type(self, fold_type_id: int, sim_type_id: int) -> None:
        FoldTypeSimTypeRel.query.filter_by(fold_type_id=fold_type_id).update({"is_default": 0})
        rel = FoldTypeSimTypeRel.query.filter_by(
            fold_type_id=fold_type_id, sim_type_id=sim_type_id
        ).first()
        if not rel:
            raise NotFoundError(f"姿态与仿真类型关系不存在: {fold_type_id}-{sim_type_id}")
        rel.is_default = 1
        db.session.commit()

    def remove_sim_type_from_fold_type(self, fold_type_id: int, sim_type_id: int) -> None:
        rel = FoldTypeSimTypeRel.query.filter_by(
            fold_type_id=fold_type_id, sim_type_id=sim_type_id
        ).first()
        if not rel:
            raise NotFoundError(f"姿态与仿真类型关系不存在: {fold_type_id}-{sim_type_id}")
        db.session.delete(rel)
        db.session.commit()


config_service = ConfigService()
