from __future__ import annotations

from typing import Any, Dict, List

from flask import current_app

from .mysql56_client import external_mysql56_client


class OutputComponentRepository:
    """struct_module.component 字典查询。"""

    @staticmethod
    def _db_name() -> str:
        return current_app.config['EXTERNAL_MYSQL_SCHEMA_STRUCT_MODULE']

    def list_components(self) -> List[Dict[str, Any]]:
        rows = external_mysql56_client.fetch_all(
            self._db_name(),
            """
            SELECT id, component
            FROM component
            ORDER BY component ASC, id ASC
            """,
        )
        return [
            {
                'code': str(row['id']),
                'name': str(row.get('component') or f"Component-{row['id']}"),
                'is_default': 1 if int(row['id']) == 18 else 0,
                'source': 'struct_module.component',
                'remark': None,
            }
            for row in rows
        ]


output_component_repository = OutputComponentRepository()
