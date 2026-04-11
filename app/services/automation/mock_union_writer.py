from __future__ import annotations

from typing import Any, Dict, List

import pymysql
from flask import current_app
from pymysql.cursors import DictCursor


class MockUnionWriter:
    """Optional mock writer for local union_opt_kernal result demos only."""

    def write_submission(self, order, condition, issue_id: int, job_id: int) -> None:
        database = current_app.config['EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL']
        with self._connection(database) as conn:
            try:
                with conn.cursor() as cursor:
                    self._ensure_issue(cursor, order, issue_id)
                    self._ensure_job(cursor, order, condition, issue_id, job_id)
                    self._ensure_round(cursor, condition, job_id)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def _connection(self, database: str):
        return pymysql.connect(
            host=current_app.config['EXTERNAL_MYSQL_HOST'],
            port=int(current_app.config['EXTERNAL_MYSQL_PORT']),
            user=current_app.config['EXTERNAL_MYSQL_USER'],
            password=current_app.config['EXTERNAL_MYSQL_PASSWORD'],
            database=database,
            charset=current_app.config.get('EXTERNAL_MYSQL_CHARSET', 'utf8mb4'),
            cursorclass=DictCursor,
            connect_timeout=float(current_app.config.get('EXTERNAL_MYSQL_CONNECT_TIMEOUT', 10)),
            read_timeout=float(current_app.config.get('EXTERNAL_MYSQL_READ_TIMEOUT', 20)),
            write_timeout=float(current_app.config.get('EXTERNAL_MYSQL_WRITE_TIMEOUT', 20)),
            autocommit=False,
        )

    @staticmethod
    def _exists(cursor, table: str, row_id: int) -> bool:
        cursor.execute(f'SELECT id FROM {table} WHERE id = %s LIMIT 1', (row_id,))
        return cursor.fetchone() is not None

    def _ensure_issue(self, cursor, order, issue_id: int) -> None:
        if self._exists(cursor, 'opt_issues', issue_id):
            return
        cursor.execute(
            """
            INSERT INTO opt_issues (id, project_id, base_dir, project_phase_id, remark, domain_account)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                issue_id,
                getattr(order, 'project_id', None),
                getattr(order, 'base_dir', None),
                getattr(order, 'phase_id', None),
                getattr(order, 'remark', None),
                getattr(order, 'domain_account', None) or getattr(order, 'created_by', None),
            ),
        )

    def _ensure_job(self, cursor, order, condition, issue_id: int, job_id: int) -> None:
        if self._exists(cursor, 'jobs', job_id):
            return
        work_dir = self._build_work_dir(order, condition)
        cursor.execute(
            """
            INSERT INTO jobs (id, issue_id, work_dir, remark, job_signal, batch_size)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                job_id,
                issue_id,
                work_dir,
                getattr(condition, 'remark', None) or getattr(order, 'remark', None),
                'running',
                float(getattr(condition, 'round_total', 0) or 0),
            ),
        )

    def _ensure_round(self, cursor, condition, job_id: int) -> None:
        circle_id = job_id
        if not self._exists(cursor, 'opt_circles', circle_id):
            cursor.execute(
                """
                INSERT INTO opt_circles (id, circle_dir, n_job_id, final_value)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    circle_id,
                    f'mock/job-{job_id}/round-1',
                    job_id,
                    self._mock_final_value(condition, 1),
                ),
            )
        self._ensure_round_outputs(cursor, condition, circle_id)

    def _ensure_round_outputs(self, cursor, condition, circle_id: int) -> None:
        output_names = self._extract_output_names(condition)
        for index, output_name in enumerate(output_names, start=1):
            resp_config_id = self._build_resp_config_id(condition, index)
            task_id = self._build_task_id(condition, index)
            opt_data_id = task_id
            post_data_id = self._build_post_data_id(condition, index)
            self._ensure_resp_config(cursor, resp_config_id, output_name)
            if not self._exists(cursor, 'opt_data', opt_data_id):
                cursor.execute(
                    """
                    INSERT INTO opt_data (
                        id, n_opt_circle_id, n_condition_config_id, data_dir,
                        opt_data_signal, running_module, task_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        opt_data_id,
                        circle_id,
                        None,
                        f'mock/circle-{circle_id}/task-{task_id}',
                        'done',
                        'POST',
                        task_id,
                    ),
                )
            self._ensure_post_schedule(cursor, task_id, opt_data_id)
            if not self._exists(cursor, 'post_data_save', post_data_id):
                cursor.execute(
                    """
                    INSERT INTO post_data_save (
                        id, task_id, resp_config_id, origin_value, final_value,
                        png_path_1, png_path_2, gif_path_1, gif_path_2, gif_path_3
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        post_data_id,
                        task_id,
                        resp_config_id,
                        self._mock_origin_value(condition, index),
                        self._mock_final_value(condition, index),
                        f'/mock/results/{circle_id}/{output_name}_1.png',
                        f'/mock/results/{circle_id}/{output_name}_2.png',
                        f'/mock/results/{circle_id}/{output_name}_1.gif',
                        None,
                        None,
                    ),
                )

    def _ensure_post_schedule(self, cursor, task_id: int, opt_data_id: int) -> None:
        if self._exists(cursor, 'post_schedule', task_id):
            return
        cursor.execute(
            """
            INSERT INTO post_schedule (id, n_opt_data_id, odb_path)
            VALUES (%s, %s, %s)
            """,
            (
                task_id,
                opt_data_id,
                None,
            ),
        )

    def _ensure_resp_config(self, cursor, resp_config_id: int, output_name: str) -> None:
        if self._exists(cursor, 'resp_config', resp_config_id):
            return
        cursor.execute(
            """
            INSERT INTO resp_config (
                id, n_condition_config_id, `set`, name, output_type,
                component, section_points, push_node_set
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                resp_config_id,
                None,
                'MOCK_SET',
                output_name,
                'scalar',
                'mock_component',
                None,
                None,
            ),
        )

    @staticmethod
    def _build_work_dir(order, condition) -> str:
        base_dir = str(getattr(order, 'base_dir', '') or '/mock/structsim').rstrip('/')
        order_no = str(getattr(order, 'order_no', '') or getattr(order, 'id', 'order'))
        condition_ref = getattr(condition, 'condition_id', None) or getattr(condition, 'id', 'condition')
        return f'{base_dir}/{order_no}/condition-{condition_ref}'

    @staticmethod
    def _normalize_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _extract_output_names(self, condition) -> List[str]:
        snapshot = self._normalize_dict(getattr(condition, 'condition_snapshot', None))
        output = self._normalize_dict(snapshot.get('output'))
        resp_details = output.get('respDetails') or output.get('resp_details')
        names: List[str] = []
        if isinstance(resp_details, list):
            for index, item in enumerate(resp_details, start=1):
                if isinstance(item, dict):
                    raw_name = item.get('respName') or item.get('outputName') or item.get('name')
                    names.append(str(raw_name or f'mock_output_{index}'))
        if names:
            return names

        output_count = max(self._to_int(getattr(condition, 'output_count', None), 0), 1)
        return [f'mock_output_{index}' for index in range(1, min(output_count, 3) + 1)]

    @staticmethod
    def _bounded_condition_seed(condition) -> int:
        return max(int(getattr(condition, 'id', 0) or 0), 0) % 10_000_000

    def _build_task_id(self, condition, index: int) -> int:
        return 800_000_000 + self._bounded_condition_seed(condition) * 10 + index

    def _build_resp_config_id(self, condition, index: int) -> int:
        return 900_000_000 + self._bounded_condition_seed(condition) * 10 + index

    def _build_post_data_id(self, condition, index: int) -> int:
        return 1_000_000_000 + self._bounded_condition_seed(condition) * 10 + index

    def _mock_origin_value(self, condition, index: int) -> float:
        seed = self._bounded_condition_seed(condition)
        return round(100.0 + seed % 97 + index * 2.5, 4)

    def _mock_final_value(self, condition, index: int) -> float:
        return round(self._mock_origin_value(condition, index) * 0.92, 4)

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


mock_union_writer = MockUnionWriter()
