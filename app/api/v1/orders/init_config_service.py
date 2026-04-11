"""
订单项目初始化服务。

职责：
- 返回项目上下文
- 计算默认阶段
- 产出参与人候选列表
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from app.common.errors import NotFoundError
from app.extensions import db
from app.models import Project, User
from app.services.external_data import project_phase_repository

from .repository import orders_repository


class OrderInitConfigService:
    """订单项目初始化服务。"""

    def get_init_config(
        self,
        project_id: int,
        domain_account: str | None = None,
    ) -> Dict[str, Any]:
        project = db.session.get(Project, project_id)
        if not project:
            raise NotFoundError(f"项目不存在: {project_id}")

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
            "phases": project_phases,
            "defaultPhaseId": default_phase_id,
            "participantCandidates": self._get_participant_candidates(
                project.id, domain_account or ""
            ),
        }

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
            account = str(
                payload.get("domainAccount") or payload.get("domain_account") or ""
            ).strip().lower()
            frequency = frequent_counter.get(account, 0)
            payload["isProjectFrequent"] = frequency > 0
            payload["projectFrequency"] = frequency
            payload["isCurrentUser"] = account == normalized_current
            serialized.append(payload)

        serialized.sort(
            key=lambda item: (
                -int(item.get("projectFrequency", 0) or 0),
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
