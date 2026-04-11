from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

from flask import current_app

from .mysql56_client import external_mysql56_client


class OptimizationRepository:
    """Read-only aggregation repository for union_opt_kernal."""

    @staticmethod
    def _db_name() -> str:
        return current_app.config['EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL']

    @staticmethod
    def _positive_ids(values: Iterable[int]) -> List[int]:
        ids: List[int] = []
        seen = set()
        for value in values:
            try:
                item = int(value)
            except (TypeError, ValueError):
                continue
            if item <= 0 or item in seen:
                continue
            seen.add(item)
            ids.append(item)
        return ids

    @staticmethod
    def _placeholders(ids: List[int]) -> str:
        return ','.join(['%s'] * len(ids))

    @staticmethod
    def _fetch_all(cursor, sql: str, params: Iterable[Any]) -> List[Dict[str, Any]]:
        cursor.execute(sql, list(params))
        return list(cursor.fetchall() or [])

    def get_opt_issue(self, opt_issue_id: int) -> Dict[str, Any] | None:
        issue_map = self.build_issue_summaries([opt_issue_id])
        return issue_map.get(int(opt_issue_id))

    def list_jobs(self, job_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = self._positive_ids(job_ids)
        if not ids:
            return []
        placeholders = self._placeholders(ids)
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, issue_id, work_dir, remark, job_signal, batch_size
            FROM jobs
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            ids,
        )

    def list_job_circles(self, job_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = self._positive_ids(job_ids)
        if not ids:
            return []
        placeholders = self._placeholders(ids)
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, circle_dir, n_job_id, final_value
            FROM opt_circles
            WHERE n_job_id IN ({placeholders})
            ORDER BY n_job_id ASC, id ASC
            """,
            ids,
        )

    def list_opt_data_by_circle_ids(self, circle_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = self._positive_ids(circle_ids)
        if not ids:
            return []
        placeholders = self._placeholders(ids)
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, n_opt_circle_id, n_condition_config_id, data_dir, opt_data_signal,
                   running_module, task_id
            FROM opt_data
            WHERE n_opt_circle_id IN ({placeholders})
            ORDER BY n_opt_circle_id ASC, id ASC
            """,
            ids,
        )

    def list_post_data_by_task_ids(self, task_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = self._positive_ids(task_ids)
        if not ids:
            return []
        placeholders = self._placeholders(ids)
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, task_id, resp_config_id, origin_value, final_value,
                   png_path_1, png_path_2, gif_path_1, gif_path_2, gif_path_3
            FROM post_data_save
            WHERE task_id IN ({placeholders})
            ORDER BY id ASC
            """,
            ids,
        )

    def list_resp_configs(self, config_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = self._positive_ids(config_ids)
        if not ids:
            return []
        placeholders = self._placeholders(ids)
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, n_condition_config_id, `set`, name, output_type, component,
                   section_points, push_node_set
            FROM resp_config
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            ids,
        )

    def build_issue_summary(self, opt_issue_id: int) -> Dict[str, Any] | None:
        issue_map = self.build_issue_summaries([opt_issue_id])
        return issue_map.get(int(opt_issue_id))

    def build_issue_summaries(self, opt_issue_ids: Iterable[int]) -> Dict[int, Dict[str, Any]]:
        ids = self._positive_ids(opt_issue_ids)
        if not ids:
            return {}

        with external_mysql56_client.connection(self._db_name()) as conn:
            with conn.cursor() as cursor:
                rows = self._list_issues_with_cursor(cursor, ids)
        return {int(row['id']): self._format_issue_summary(row) for row in rows}

    def build_issue_and_job_summaries(
        self,
        opt_issue_ids: Iterable[int],
        job_ids: Iterable[int],
        include_outputs: bool = True,
    ) -> tuple[Dict[int, Dict[str, Any]], List[Dict[str, Any]]]:
        issue_ids = self._positive_ids(opt_issue_ids)
        requested_job_ids = self._positive_ids(job_ids)
        if not issue_ids and not requested_job_ids:
            return {}, []

        with external_mysql56_client.connection(self._db_name()) as conn:
            with conn.cursor() as cursor:
                issue_rows = self._list_issues_with_cursor(cursor, issue_ids) if issue_ids else []
                job_summaries = self._build_job_summaries_with_cursor(
                    cursor, requested_job_ids, include_outputs=include_outputs
                ) if requested_job_ids else []
        return {int(row['id']): self._format_issue_summary(row) for row in issue_rows}, job_summaries

    @staticmethod
    def _format_issue_summary(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': int(row['id']),
            'projectId': row.get('project_id'),
            'baseDir': row.get('base_dir'),
            'projectPhaseId': row.get('project_phase_id'),
            'remark': row.get('remark'),
            'domainAccount': row.get('domain_account'),
        }

    def build_job_summaries(
        self, job_ids: Iterable[int], include_outputs: bool = True
    ) -> List[Dict[str, Any]]:
        requested_job_ids = self._positive_ids(job_ids)
        if not requested_job_ids:
            return []

        with external_mysql56_client.connection(self._db_name()) as conn:
            with conn.cursor() as cursor:
                return self._build_job_summaries_with_cursor(
                    cursor, requested_job_ids, include_outputs=include_outputs
                )

    def _build_job_summaries_with_cursor(
        self,
        cursor,
        requested_job_ids: List[int],
        include_outputs: bool = True,
    ) -> List[Dict[str, Any]]:
        jobs = self._list_jobs_with_cursor(cursor, requested_job_ids)
        if not jobs:
            return []

        job_id_list = [int(job['id']) for job in jobs]
        circles = self._list_job_circles_with_cursor(cursor, job_id_list)
        if not include_outputs:
            return self._build_job_summary_payloads(
                jobs=jobs,
                circles=circles,
                opt_data_rows=[],
                post_data_rows=[],
                resp_configs={},
            )

        circle_ids = [int(circle['id']) for circle in circles]
        opt_data_rows = self._list_opt_data_with_cursor(cursor, circle_ids) if circle_ids else []
        task_ids = [
            int(row['task_id'])
            for row in opt_data_rows
            if row.get('task_id') is not None
        ]
        post_data_rows = self._list_post_data_with_cursor(cursor, task_ids) if task_ids else []
        resp_config_ids = [
            int(row['resp_config_id'])
            for row in post_data_rows
            if row.get('resp_config_id') is not None
        ]
        condition_config_ids = [
            int(row['n_condition_config_id'])
            for row in opt_data_rows
            if row.get('n_condition_config_id') is not None
        ]
        resp_configs = self._collect_resp_configs_with_cursor(
            cursor,
            resp_config_ids=resp_config_ids,
            condition_config_ids=condition_config_ids,
        )

        return self._build_job_summary_payloads(
            jobs=jobs,
            circles=circles,
            opt_data_rows=opt_data_rows,
            post_data_rows=post_data_rows,
            resp_configs=resp_configs,
        )

    def _list_issues_with_cursor(self, cursor, issue_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(issue_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, project_id, base_dir, project_phase_id, remark, domain_account
            FROM opt_issues
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            issue_ids,
        )

    def _list_jobs_with_cursor(self, cursor, job_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(job_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, issue_id, work_dir, remark, job_signal, batch_size
            FROM jobs
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            job_ids,
        )

    def _list_job_circles_with_cursor(self, cursor, job_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(job_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, circle_dir, n_job_id, final_value
            FROM opt_circles
            WHERE n_job_id IN ({placeholders})
            ORDER BY n_job_id ASC, id ASC
            """,
            job_ids,
        )

    def _list_opt_data_with_cursor(self, cursor, circle_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(circle_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, n_opt_circle_id, n_condition_config_id, data_dir, opt_data_signal,
                   running_module, task_id
            FROM opt_data
            WHERE n_opt_circle_id IN ({placeholders})
            ORDER BY n_opt_circle_id ASC, id ASC
            """,
            circle_ids,
        )

    def _list_post_data_with_cursor(self, cursor, task_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(task_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, task_id, resp_config_id, origin_value, final_value,
                   png_path_1, png_path_2, gif_path_1, gif_path_2, gif_path_3
            FROM post_data_save
            WHERE task_id IN ({placeholders})
            ORDER BY id ASC
            """,
            task_ids,
        )

    def _list_resp_configs_with_cursor(
        self, cursor, config_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        placeholders = self._placeholders(config_ids)
        rows = self._fetch_all(
            cursor,
            f"""
            SELECT id, n_condition_config_id, `set`, name, output_type, component,
                   section_points, push_node_set
            FROM resp_config
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            config_ids,
        )
        return {int(row['id']): row for row in rows}

    def _list_resp_configs_by_condition_config_ids_with_cursor(
        self, cursor, condition_config_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        placeholders = self._placeholders(condition_config_ids)
        rows = self._fetch_all(
            cursor,
            f"""
            SELECT id, n_condition_config_id, `set`, name, output_type, component,
                   section_points, push_node_set
            FROM resp_config
            WHERE n_condition_config_id IN ({placeholders})
            ORDER BY n_condition_config_id ASC, id ASC
            """,
            condition_config_ids,
        )
        return {int(row['id']): row for row in rows}

    def _collect_resp_configs_with_cursor(
        self,
        cursor,
        resp_config_ids: List[int],
        condition_config_ids: List[int],
    ) -> Dict[int, Dict[str, Any]]:
        configs: Dict[int, Dict[str, Any]] = {}
        normalized_resp_config_ids = self._positive_ids(resp_config_ids)
        normalized_condition_config_ids = self._positive_ids(condition_config_ids)
        if normalized_condition_config_ids:
            configs.update(
                self._list_resp_configs_by_condition_config_ids_with_cursor(
                    cursor,
                    normalized_condition_config_ids,
                )
            )
        if normalized_resp_config_ids:
            configs.update(self._list_resp_configs_with_cursor(cursor, normalized_resp_config_ids))
        return configs

    def _build_job_summary_payloads(
        self,
        jobs: List[Dict[str, Any]],
        circles: List[Dict[str, Any]],
        opt_data_rows: List[Dict[str, Any]],
        post_data_rows: List[Dict[str, Any]],
        resp_configs: Dict[int, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        circles_by_job: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for circle in circles:
            circles_by_job[int(circle['n_job_id'])].append(circle)

        opt_data_by_circle: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in opt_data_rows:
            opt_data_by_circle[int(row['n_opt_circle_id'])].append(row)

        post_data_by_task: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in post_data_rows:
            post_data_by_task[int(row['task_id'])].append(row)

        resp_configs_by_condition_config: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in resp_configs.values():
            condition_config_id = row.get('n_condition_config_id')
            if condition_config_id is not None:
                resp_configs_by_condition_config[int(condition_config_id)].append(row)

        summaries: List[Dict[str, Any]] = []
        for job in jobs:
            job_id = int(job['id'])
            job_circles = circles_by_job.get(job_id, [])
            round_summaries: List[Dict[str, Any]] = []
            for index, circle in enumerate(job_circles, start=1):
                circle_id = int(circle['id'])
                circle_opt_data = opt_data_by_circle.get(circle_id, [])
                output_summaries: List[Dict[str, Any]] = []
                running_modules = {
                    str(row.get('running_module')).strip()
                    for row in circle_opt_data
                    if row.get('running_module')
                }
                for opt_data in circle_opt_data:
                    task_id = opt_data.get('task_id')
                    if task_id is None:
                        continue
                    task_post_rows = post_data_by_task.get(int(task_id), [])
                    condition_config_id = opt_data.get('n_condition_config_id')
                    expected_resp_configs = (
                        resp_configs_by_condition_config.get(int(condition_config_id), [])
                        if condition_config_id is not None
                        else []
                    )
                    if not expected_resp_configs:
                        expected_resp_configs = [
                            resp_configs[int(post_data['resp_config_id'])]
                            for post_data in task_post_rows
                            if post_data.get('resp_config_id') is not None
                            and int(post_data['resp_config_id']) in resp_configs
                        ]
                    if not expected_resp_configs:
                        expected_resp_configs = [None]
                    post_rows_by_resp_config: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
                    for post_data in task_post_rows:
                        if post_data.get('resp_config_id') is not None:
                            post_rows_by_resp_config[int(post_data['resp_config_id'])].append(post_data)
                    for resp_config in expected_resp_configs:
                        resp_config_id = int(resp_config['id']) if resp_config else None
                        matched_post_rows = (
                            post_rows_by_resp_config.get(resp_config_id, [])
                            if resp_config_id is not None
                            else []
                        )
                        if not matched_post_rows:
                            output_summaries.append(
                                self._build_output_summary(
                                    task_id=int(task_id),
                                    resp_config_id=resp_config_id,
                                    resp_config=resp_config,
                                    post_data=None,
                                )
                            )
                            continue
                        for post_data in matched_post_rows:
                            output_summaries.append(
                                self._build_output_summary(
                                    task_id=int(task_id),
                                    resp_config_id=resp_config_id,
                                    resp_config=resp_config,
                                    post_data=post_data,
                                )
                            )
                round_summaries.append(
                    {
                        'roundIndex': index,
                        'circleId': circle_id,
                        'circleDir': circle.get('circle_dir'),
                        'finalValue': circle.get('final_value'),
                        'status': self._resolve_round_status(
                            circle, circle_opt_data, output_summaries
                        ),
                        'runningModule': sorted(running_modules)[0] if running_modules else None,
                        'outputs': output_summaries,
                    }
                )

            summaries.append(
                {
                    'id': job_id,
                    'issueId': job.get('issue_id'),
                    'workDir': job.get('work_dir'),
                    'remark': job.get('remark'),
                    'jobSignal': job.get('job_signal'),
                    'batchSize': job.get('batch_size'),
                    'status': self._resolve_job_status(job, round_summaries),
                    'progress': self._resolve_job_progress(round_summaries),
                    'rounds': round_summaries,
                }
            )
        return summaries

    @staticmethod
    def _build_output_summary(
        task_id: int,
        resp_config_id: int | None,
        resp_config: Dict[str, Any] | None,
        post_data: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        return {
            'taskId': task_id,
            'respConfigId': resp_config_id,
            'respName': resp_config.get('name') if resp_config else None,
            'outputType': resp_config.get('output_type') if resp_config else None,
            'component': resp_config.get('component') if resp_config else None,
            'originValue': post_data.get('origin_value') if post_data else None,
            'finalValue': post_data.get('final_value') if post_data else None,
            'imagePaths': [
                value
                for value in (
                    post_data.get('png_path_1') if post_data else None,
                    post_data.get('png_path_2') if post_data else None,
                )
                if value
            ],
            'gifPaths': [
                value
                for value in (
                    post_data.get('gif_path_1') if post_data else None,
                    post_data.get('gif_path_2') if post_data else None,
                    post_data.get('gif_path_3') if post_data else None,
                )
                if value
            ],
        }

    @staticmethod
    def _resolve_round_status(
        circle: Dict[str, Any],
        opt_data_rows: List[Dict[str, Any]],
        output_summaries: List[Dict[str, Any]],
    ) -> int:
        final_value = circle.get('final_value')
        if final_value not in (None, ''):
            return 2
        if output_summaries:
            return 1
        if opt_data_rows:
            return 1
        return 0

    @staticmethod
    def _resolve_job_status(job: Dict[str, Any], round_summaries: List[Dict[str, Any]]) -> int:
        signal = str(job.get('job_signal') or '').strip().lower()
        if signal in {'failed', 'error', 'aborted'}:
            return 3
        if round_summaries and all(item['status'] == 2 for item in round_summaries):
            return 2
        if round_summaries and any(item['status'] in (1, 2) for item in round_summaries):
            return 1
        return 0

    @staticmethod
    def _resolve_job_progress(round_summaries: List[Dict[str, Any]]) -> int:
        if not round_summaries:
            return 0
        completed = sum(1 for item in round_summaries if item['status'] == 2)
        total = max(len(round_summaries), 1)
        return int(round((completed / total) * 100))


optimization_repository = OptimizationRepository()
