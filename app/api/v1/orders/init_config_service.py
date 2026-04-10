"""
提单项目上下文初始化服务。

职责：
- 读取当前项目的阶段列表与默认阶段
- 产出当前项目下的参与人候选列表
- 在需要时补充默认工况展开所需的默认参数链路

注意：
- 项目上下文不再承担资源池查询
- 项目不存在默认仿真类型关联时，仍然必须正常返回项目级数据
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from app.common.errors import BusinessError, NotFoundError
from app.constants.error_codes import ErrorCode
from app.extensions import db
from app.models import (
    CondOutGroupConditionRel,
    CondOutGroupOutputRel,
    ConditionDef,
    ConditionOutputGroup,
    OutputDef,
    ParamDef,
    ParamGroup,
    ParamGroupParamRel,
    Project,
    ProjectSimTypeRel,
    SimType,
    SimTypeCondOutGroupRel,
    SimTypeParamGroupRel,
    SimTypeSolverRel,
    Solver,
    User,
)
from .repository import orders_repository
from app.services.external_data import project_phase_repository


class OrderInitConfigService:
    """提单项目上下文初始化服务。"""

    def get_init_config(
        self,
        project_id: int,
        sim_type_id: Optional[int] = None,
        domain_account: Optional[str] = None,
    ) -> Dict[str, Any]:
        project = db.session.get(Project, project_id)
        if not project:
            raise NotFoundError("项目", project_id)

        sim_type = self._resolve_sim_type(project_id, sim_type_id)

        param_group_options: List[Dict[str, Any]] = []
        default_param_group: Optional[Dict[str, Any]] = None
        cond_out_group_options: List[Dict[str, Any]] = []
        default_cond_out_group: Optional[Dict[str, Any]] = None
        solver_options: List[Dict[str, Any]] = []
        default_solver: Optional[Dict[str, Any]] = None

        if sim_type is not None:
            param_group_options = self._get_param_group_options(sim_type.id, project_id)
            default_param_group = next(
                (opt for opt in param_group_options if opt["isDefault"] == 1),
                None,
            )

            cond_out_group_options = self._get_cond_out_group_options(sim_type.id, project_id)
            default_cond_out_group = next(
                (opt for opt in cond_out_group_options if opt["isDefault"] == 1),
                None,
            )

            solver_options = self._get_solver_options(sim_type.id)
            default_solver = next((opt for opt in solver_options if opt["isDefault"] == 1), None)

        default_phase_id = project_phase_repository.get_default_phase_id(project.id)
        project_phases = project_phase_repository.list_project_phases(project.id)
        if (
            default_phase_id is not None
            and all(item.get("phaseId") != default_phase_id for item in project_phases)
        ):
            project_phases = [
                {"phaseId": default_phase_id, "phaseName": f"阶段-{default_phase_id}"},
                *project_phases,
            ]

        return {
            "projectId": project.id,
            "projectName": project.name,
            "simTypeId": sim_type.id if sim_type else None,
            "simTypeName": sim_type.name if sim_type else None,
            "simTypeCode": sim_type.code if sim_type else None,
            "phases": project_phases,
            "defaultPhaseId": default_phase_id,
            "participantCandidates": self._get_participant_candidates(
                project.id, domain_account or ""
            ),
            "resourcePools": [],
            "defaultResourceId": None,
            "defaultParamGroup": default_param_group,
            "defaultCondOutGroup": default_cond_out_group,
            "defaultSolver": default_solver,
            "paramGroupOptions": param_group_options,
            "condOutGroupOptions": cond_out_group_options,
            "solverOptions": solver_options,
        }

    def _resolve_sim_type(self, project_id: int, sim_type_id: Optional[int]) -> Optional[SimType]:
        if sim_type_id:
            return db.session.get(SimType, sim_type_id)

        default_rel = (
            db.session.query(ProjectSimTypeRel)
            .filter_by(project_id=project_id, is_default=1)
            .first()
        )
        if default_rel:
            return db.session.get(SimType, default_rel.sim_type_id)

        first_rel = (
            db.session.query(ProjectSimTypeRel)
            .filter_by(project_id=project_id)
            .order_by(ProjectSimTypeRel.sort.asc(), ProjectSimTypeRel.id.asc())
            .first()
        )
        if first_rel:
            return db.session.get(SimType, first_rel.sim_type_id)

        return None

    def _get_participant_candidates(
        self, project_id: int, current_domain_account: str
    ) -> List[Dict[str, Any]]:
        frequent_counter = Counter[str]()
        for order in orders_repository.get_recent_orders_by_project(project_id):
            participant_uids = getattr(order, "participant_uids", None) or []
            if not isinstance(participant_uids, list):
                continue
            for raw_value in participant_uids:
                candidate = str(raw_value or "").strip().lower()
                if candidate:
                    frequent_counter[candidate] += 1

        users = (
            User.query.filter(User.valid == 1)
            .order_by(User.real_name.asc(), User.user_name.asc(), User.domain_account.asc())
            .all()
        )

        normalized_current = str(current_domain_account or "").strip().lower()
        serialized: List[Dict[str, Any]] = []
        for user in users:
            payload = user.to_public_dict()
            domain_account = str(payload.get("domainAccount") or payload.get("domain_account") or "").strip().lower()
            frequency = frequent_counter.get(domain_account, 0)
            payload["isProjectFrequent"] = frequency > 0
            payload["projectFrequency"] = frequency
            payload["isCurrentUser"] = domain_account == normalized_current
            serialized.append(payload)

        serialized.sort(
            key=lambda item: (
                -int(item.get("projectFrequency", 0) or 0),
                0 if item.get("isCurrentUser") else 1,
                str(
                    item.get("realName")
                    or item.get("real_name")
                    or item.get("userName")
                    or item.get("user_name")
                    or item.get("displayName")
                    or item.get("display_name")
                    or item.get("domainAccount")
                    or item.get("domain_account")
                    or ""
                ).lower(),
            )
        )
        return serialized

    def _get_param_group_options(self, sim_type_id: int, project_id: int) -> List[Dict[str, Any]]:
        rels = (
            db.session.query(SimTypeParamGroupRel)
            .join(ParamGroup, ParamGroup.id == SimTypeParamGroupRel.param_group_id)
            .filter(
                SimTypeParamGroupRel.sim_type_id == sim_type_id,
                or_(ParamGroup.project_id == project_id, ParamGroup.project_id.is_(None)),
            )
            .order_by(
                ParamGroup.project_id.is_(None).asc(),
                SimTypeParamGroupRel.sort.asc(),
                SimTypeParamGroupRel.id.asc(),
            )
            .all()
        )

        options: List[Dict[str, Any]] = []
        for rel in rels:
            param_group = db.session.get(ParamGroup, rel.param_group_id)
            if not param_group:
                continue

            param_rels = (
                db.session.query(ParamGroupParamRel)
                .filter_by(param_group_id=param_group.id)
                .order_by(ParamGroupParamRel.sort.asc())
                .all()
            )

            params: List[Dict[str, Any]] = []
            for param_rel in param_rels:
                param_def = db.session.get(ParamDef, param_rel.param_def_id)
                if not param_def:
                    continue
                params.append(
                    {
                        "paramDefId": param_def.id,
                        "paramName": param_def.name,
                        "paramKey": param_def.key,
                        "defaultValue": param_rel.default_value or param_def.default_value,
                        "unit": param_def.unit,
                        "valType": param_def.val_type,
                        "required": param_def.required,
                    }
                )

            options.append(
                {
                    "paramGroupId": param_group.id,
                    "paramGroupName": param_group.name,
                    "projectId": param_group.project_id,
                    "algType": param_group.alg_type or 0,
                    "isDefault": rel.is_default,
                    "params": params,
                }
            )

        return options

    def _get_cond_out_group_options(self, sim_type_id: int, project_id: int) -> List[Dict[str, Any]]:
        rels = (
            db.session.query(SimTypeCondOutGroupRel)
            .join(ConditionOutputGroup, ConditionOutputGroup.id == SimTypeCondOutGroupRel.cond_out_group_id)
            .filter(
                SimTypeCondOutGroupRel.sim_type_id == sim_type_id,
                or_(
                    ConditionOutputGroup.project_id == project_id,
                    ConditionOutputGroup.project_id.is_(None),
                ),
            )
            .order_by(
                ConditionOutputGroup.project_id.is_(None).asc(),
                SimTypeCondOutGroupRel.sort.asc(),
                SimTypeCondOutGroupRel.id.asc(),
            )
            .all()
        )

        options: List[Dict[str, Any]] = []
        for rel in rels:
            cond_out_group = db.session.get(ConditionOutputGroup, rel.cond_out_group_id)
            if not cond_out_group:
                continue

            cond_rels = (
                db.session.query(CondOutGroupConditionRel)
                .filter_by(cond_out_group_id=cond_out_group.id)
                .order_by(CondOutGroupConditionRel.sort.asc())
                .all()
            )
            conditions: List[Dict[str, Any]] = []
            for cond_rel in cond_rels:
                cond_def = db.session.get(ConditionDef, cond_rel.condition_def_id)
                if not cond_def:
                    continue
                conditions.append(
                    {
                        "conditionDefId": cond_def.id,
                        "conditionName": cond_def.name,
                        "conditionCode": cond_def.code,
                        "configData": cond_rel.config_data,
                        "conditionSchema": cond_def.condition_schema,
                    }
                )

            output_rels = (
                db.session.query(CondOutGroupOutputRel)
                .filter_by(cond_out_group_id=cond_out_group.id)
                .order_by(CondOutGroupOutputRel.sort.asc())
                .all()
            )
            outputs: List[Dict[str, Any]] = []
            for output_rel in output_rels:
                output_def = db.session.get(OutputDef, output_rel.output_def_id)
                if not output_def:
                    continue
                outputs.append(
                    {
                        "outputDefId": output_def.id,
                        "outputName": output_def.name,
                        "outputCode": output_def.code,
                        "unit": output_def.unit,
                        "valType": output_def.val_type,
                        "setName": output_rel.set_name or "push",
                        "component": output_rel.component or "18",
                        "stepName": output_rel.step_name,
                        "sectionPoint": output_rel.section_point,
                        "specialOutputSet": output_rel.special_output_set,
                        "description": output_rel.description,
                        "weight": output_rel.weight or 1.0,
                        "multiple": output_rel.multiple or 1.0,
                        "lowerLimit": output_rel.lower_limit or 0.0,
                        "upperLimit": output_rel.upper_limit,
                        "targetType": output_rel.target_type or 3,
                        "targetValue": output_rel.target_value,
                    }
                )

            options.append(
                {
                    "condOutGroupId": cond_out_group.id,
                    "condOutGroupName": cond_out_group.name,
                    "projectId": cond_out_group.project_id,
                    "algType": cond_out_group.alg_type or 0,
                    "isDefault": rel.is_default,
                    "conditions": conditions,
                    "outputs": outputs,
                }
            )

        return options

    def _get_solver_options(self, sim_type_id: int) -> List[Dict[str, Any]]:
        rels = (
            db.session.query(SimTypeSolverRel)
            .filter_by(sim_type_id=sim_type_id)
            .order_by(SimTypeSolverRel.sort.asc())
            .all()
        )

        options: List[Dict[str, Any]] = []
        for rel in rels:
            solver = db.session.get(Solver, rel.solver_id)
            if not solver:
                continue
            options.append(
                {
                    "solverId": solver.id,
                    "solverName": solver.name,
                    "solverCode": solver.code,
                    "solverVersion": solver.version,
                    "isDefault": rel.is_default,
                }
            )

        return options
