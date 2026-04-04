from __future__ import annotations

from typing import Any, Dict, List

from flask import current_app

from .mysql56_client import external_mysql56_client


class ProjectPhaseRepository:
    """simlation_project 阶段与项目阶段映射查询。"""

    @staticmethod
    def _db_name() -> str:
        return current_app.config['EXTERNAL_MYSQL_SCHEMA_SIMLATION_PROJECT']

    @staticmethod
    def _normalize_phase_name(raw_name: Any, phase_id: int) -> str:
        name = str(raw_name or '').strip()
        if not name or '\ufffd' in name or '?' in name:
            return f'阶段-{phase_id}'
        return name

    def list_phases(self) -> List[Dict[str, Any]]:
        rows = external_mysql56_client.fetch_all(
            self._db_name(),
            """
            SELECT phase_id, phase_desc
            FROM phase
            ORDER BY phase_id ASC
            """,
        )
        return [
            {
                'phaseId': int(row['phase_id']),
                'phaseName': self._normalize_phase_name(row.get('phase_desc'), int(row['phase_id'])),
            }
            for row in rows
        ]

    def get_default_phase_id(self, project_id: int) -> int | None:
        row = external_mysql56_client.fetch_one(
            self._db_name(),
            """
            SELECT phase_id
            FROM pp_phase
            WHERE pp_record_id = %s
            ORDER BY pp_phase_id DESC
            LIMIT 1
            """,
            (project_id,),
        )
        if not row or row.get('phase_id') is None:
            return None
        return int(row['phase_id'])


project_phase_repository = ProjectPhaseRepository()
