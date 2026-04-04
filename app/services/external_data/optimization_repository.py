from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

from flask import current_app

from .mysql56_client import external_mysql56_client


class OptimizationRepository:
    """union_opt_kernal 外部优化链路只读查询。"""

    @staticmethod
    def _db_name() -> str:
        return current_app.config['EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL']

    def get_opt_issue(self, opt_issue_id: int) -> Dict[str, Any] | None:
        if opt_issue_id <= 0:
            return None
        return external_mysql56_client.fetch_one(
            self._db_name(),
            """
            SELECT id, project_id, base_dir, project_phase_id, remark, domain_account
            FROM opt_issues
            WHERE id = %s
            LIMIT 1
            """,
            (opt_issue_id,),
        )

    def list_jobs(self, job_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = [int(job_id) for job_id in job_ids if int(job_id) > 0]
        if not ids:
            return []
        placeholders = ','.join(['%s'] * len(ids))
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
        ids = [int(job_id) for job_id in job_ids if int(job_id) > 0]
        if not ids:
            return []
        placeholders = ','.join(['%s'] * len(ids))
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
        ids = [int(circle_id) for circle_id in circle_ids if int(circle_id) > 0]
        if not ids:
            return []
        placeholders = ','.join(['%s'] * len(ids))
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, n_opt_circle_id, n_condition_config_id, data_dir, opt_data_signal, running_module, task_id
            FROM opt_data
            WHERE n_opt_circle_id IN ({placeholders})
            ORDER BY n_opt_circle_id ASC, id ASC
            """,
            ids,
        )

    def list_post_data_by_task_ids(self, task_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = [int(task_id) for task_id in task_ids if int(task_id) > 0]
        if not ids:
            return []
        placeholders = ','.join(['%s'] * len(ids))
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, task_id, resp_config_id, origin_value, final_value
            FROM post_data_save
            WHERE task_id IN ({placeholders})
            ORDER BY id ASC
            """,
            ids,
        )

    def list_resp_configs(self, config_ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids = [int(config_id) for config_id in config_ids if int(config_id) > 0]
        if not ids:
            return []
        placeholders = ','.join(['%s'] * len(ids))
        return external_mysql56_client.fetch_all(
            self._db_name(),
            f"""
            SELECT id, n_condition_config_id, `set`, name, output_type, component, section_points, push_node_set
            FROM resp_config
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            ids,
        )

    def build_issue_summary(self, opt_issue_id: int) -> Dict[str, Any] | None:
        row = self.get_opt_issue(opt_issue_id)
        if not row:
            return None
        return {
            'id': int(row['id']),
            'projectId': row.get('project_id'),
            'baseDir': row.get('base_dir'),
            'projectPhaseId': row.get('project_phase_id'),
            'remark': row.get('remark'),
            'domainAccount': row.get('domain_account'),
        }

    def build_job_summaries(self, job_ids: Iterable[int]) -> List[Dict[str, Any]]:
        jobs = self.list_jobs(job_ids)
        if not jobs:
            return []

        job_id_list = [int(job['id']) for job in jobs]
        circles = self.list_job_circles(job_id_list)
        circles_by_job: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for circle in circles:
            circles_by_job[int(circle['n_job_id'])].append(circle)

        circle_ids = [int(circle['id']) for circle in circles]
        opt_data_rows = self.list_opt_data_by_circle_ids(circle_ids)
        opt_data_by_circle: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in opt_data_rows:
            opt_data_by_circle[int(row['n_opt_circle_id'])].append(row)

        task_ids = [int(row['task_id']) for row in opt_data_rows if row.get('task_id') is not None]
        post_data_rows = self.list_post_data_by_task_ids(task_ids)
        post_data_by_task: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in post_data_rows:
            post_data_by_task[int(row['task_id'])].append(row)

        resp_config_ids = [int(row['resp_config_id']) for row in post_data_rows if row.get('resp_config_id') is not None]
        resp_configs = {
            int(row['id']): row
            for row in self.list_resp_configs(resp_config_ids)
        }

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
                    for post_data in post_data_by_task.get(int(task_id), []):
                        resp_config = resp_configs.get(int(post_data['resp_config_id']))
                        output_summaries.append(
                            {
                                'taskId': int(task_id),
                                'respConfigId': int(post_data['resp_config_id']),
                                'respName': resp_config.get('name') if resp_config else None,
                                'outputType': resp_config.get('output_type') if resp_config else None,
                                'component': resp_config.get('component') if resp_config else None,
                                'originValue': post_data.get('origin_value'),
                                'finalValue': post_data.get('final_value'),
                            }
                        )
                round_summaries.append(
                    {
                        'roundIndex': index,
                        'circleId': circle_id,
                        'circleDir': circle.get('circle_dir'),
                        'finalValue': circle.get('final_value'),
                        'status': self._resolve_round_status(circle, circle_opt_data, output_summaries),
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
