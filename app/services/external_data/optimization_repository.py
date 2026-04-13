from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

from flask import current_app

from .mysql56_client import external_mysql56_client


class OptimizationRepository:
    """union_opt_kernal 只读聚合查询。"""

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
        return self.build_issue_summaries([opt_issue_id]).get(int(opt_issue_id))

    def build_issue_summary(self, opt_issue_id: int) -> Dict[str, Any] | None:
        return self.get_opt_issue(opt_issue_id)

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
                job_summaries = (
                    self._build_job_summaries_with_cursor(cursor, requested_job_ids, include_outputs)
                    if requested_job_ids
                    else []
                )
        return {int(row['id']): self._format_issue_summary(row) for row in issue_rows}, job_summaries

    def build_job_summaries(self, job_ids: Iterable[int], include_outputs: bool = True) -> List[Dict[str, Any]]:
        requested_job_ids = self._positive_ids(job_ids)
        if not requested_job_ids:
            return []
        with external_mysql56_client.connection(self._db_name()) as conn:
            with conn.cursor() as cursor:
                return self._build_job_summaries_with_cursor(cursor, requested_job_ids, include_outputs)

    def _list_issues_with_cursor(self, cursor, issue_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(issue_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, user_name, user_account, project_id, project_phase_id, sys_phase,
                   issue_desc, create_time, update_time, n_is_auto_opt, can_save_users, care_device_ids
            FROM opt_issues
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            issue_ids,
        )

    @staticmethod
    def _format_issue_summary(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': int(row['id']),
            'userName': row.get('user_name'),
            'userAccount': row.get('user_account'),
            'projectId': row.get('project_id'),
            'projectPhaseId': row.get('project_phase_id'),
            'sysPhase': row.get('sys_phase'),
            'issueDesc': row.get('issue_desc'),
            'createdAt': row.get('create_time'),
            'updatedAt': row.get('update_time'),
            'isAutoOpt': row.get('n_is_auto_opt'),
            'canSaveUsers': row.get('can_save_users'),
            'careDeviceIds': row.get('care_device_ids'),
        }

    def _build_job_summaries_with_cursor(
        self,
        cursor,
        requested_job_ids: List[int],
        include_outputs: bool = True,
    ) -> List[Dict[str, Any]]:
        jobs = self._list_jobs_with_cursor(cursor, requested_job_ids)
        if not jobs:
            return []

        job_ids = [int(job['id']) for job in jobs]
        condition_configs = self._list_condition_configs_with_cursor(cursor, job_ids)
        condition_config_ids = [int(row['n_id']) for row in condition_configs]
        subject_configs = self._list_subject_configs_with_cursor(cursor, condition_config_ids) if condition_config_ids else []
        para_configs = self._list_para_configs_with_cursor(cursor, job_ids)
        resp_configs = self._list_resp_configs_with_cursor(cursor, condition_config_ids) if condition_config_ids else []
        circles = self._list_circles_with_cursor(cursor, job_ids)

        if not include_outputs:
            return self._build_job_summary_payloads(
                jobs, condition_configs, subject_configs, para_configs, resp_configs, circles, [], [], [], [], []
            )

        circle_ids = [int(circle['n_id']) for circle in circles]
        opt_data_rows = self._list_opt_data_with_cursor(cursor, circle_ids) if circle_ids else []
        opt_data_ids = [int(row['id']) for row in opt_data_rows]
        schedule_rows = self._list_post_schedule_with_cursor(cursor, opt_data_ids) if opt_data_ids else []
        schedule_ids = [int(row['id']) for row in schedule_rows]
        post_data_rows = self._list_post_data_with_cursor(cursor, schedule_ids) if schedule_ids else []
        para_rows = self._list_para_with_cursor(cursor, circle_ids, condition_config_ids) if circle_ids and condition_config_ids else []
        module_rows = self._list_server_modules_with_cursor(cursor)

        return self._build_job_summary_payloads(
            jobs,
            condition_configs,
            subject_configs,
            para_configs,
            resp_configs,
            circles,
            opt_data_rows,
            schedule_rows,
            post_data_rows,
            para_rows,
            module_rows,
        )

    def _list_jobs_with_cursor(self, cursor, job_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(job_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, issue_id, s_job_name, n_opt_type, job_signal, base_dir, job_dir,
                   batch_size, input_json, case_desc, pre_task_id, n_case_order,
                   start_time, end_time, para_json_file_path, para_inequality
            FROM jobs
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            job_ids,
        )

    def _list_condition_configs_with_cursor(self, cursor, job_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(job_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT n_id, s_name, s_set_name, n_job_id, user_account, user_name,
                   s_condition_dir, s_input_files, n_subject_type, s_param_names
            FROM job_condition_config
            WHERE n_job_id IN ({placeholders})
            ORDER BY n_job_id ASC, n_id ASC
            """,
            job_ids,
        )

    def _list_subject_configs_with_cursor(self, cursor, condition_config_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(condition_config_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT n_id, n_condition_config_id, n_model_level, n_simulation_type,
                   n_solver_type, n_cpu_cores, n_cpu_type, n_double_type,
                   n_rotate_drop, n_submit_source_type
            FROM subject_config_struct
            WHERE n_condition_config_id IN ({placeholders})
            ORDER BY n_condition_config_id ASC
            """,
            condition_config_ids,
        )

    def _list_para_configs_with_cursor(self, cursor, job_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(job_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT n_id, n_job_id, s_name, s_unit, s_type, s_inital_value,
                   s_range, s_comp_name, s_json_file_path
            FROM para_config
            WHERE n_job_id IN ({placeholders})
            ORDER BY n_job_id ASC, n_id ASC
            """,
            job_ids,
        )

    def _list_resp_configs_with_cursor(self, cursor, condition_config_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(condition_config_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT n_id, n_condition_config_id, s_name, s_set_name, s_output_type,
                   n_weight, n_multiple, n_target, n_target_value, n_lower_limit,
                   n_upper_limit, s_experssion, s_customize_param1, s_customize_param2,
                   s_customize_param3, s_customize_param4, s_customize_param5, s_step_name
            FROM resp_config
            WHERE n_condition_config_id IN ({placeholders})
            ORDER BY n_condition_config_id ASC, n_id ASC
            """,
            condition_config_ids,
        )

    def _list_circles_with_cursor(self, cursor, job_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(job_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT n_id, n_job_id, n_circle, n_run_num, s_circle_path, n_status,
                   n_total_value, d_update
            FROM opt_circle
            WHERE n_job_id IN ({placeholders})
            ORDER BY n_job_id ASC, n_circle ASC, n_id ASC
            """,
            job_ids,
        )

    def _list_opt_data_with_cursor(self, cursor, circle_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(circle_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, n_opt_circle_id, n_condition_config_id, data_dir, opt_data_signal,
                   s_errors, task_id, total_time, calc_time, process_id, task_record_id,
                   need_down_result, running_module, running_status
            FROM opt_data
            WHERE n_opt_circle_id IN ({placeholders})
            ORDER BY n_opt_circle_id ASC, n_condition_config_id ASC, id ASC
            """,
            circle_ids,
        )

    def _list_post_schedule_with_cursor(self, cursor, opt_data_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(opt_data_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, opt_data_id, running, result, odb_path, start_time, end_time
            FROM post_schedule_info
            WHERE opt_data_id IN ({placeholders})
            ORDER BY opt_data_id ASC, id ASC
            """,
            opt_data_ids,
        )

    def _list_post_data_with_cursor(self, cursor, schedule_ids: List[int]) -> List[Dict[str, Any]]:
        placeholders = self._placeholders(schedule_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT id, task_id, resp_config_id, best_time, best_label, origin_value,
                   final_value, curvers_json_path, curvers_png_path, cloud_png_path1,
                   cloud_png_path2, avi_path1, avi_path2, start_time, end_time,
                   s_errors, max_gif_x, max_gif_y
            FROM post_data_save
            WHERE task_id IN ({placeholders})
            ORDER BY task_id ASC, resp_config_id ASC, id ASC
            """,
            schedule_ids,
        )

    def _list_para_with_cursor(self, cursor, circle_ids: List[int], condition_config_ids: List[int]) -> List[Dict[str, Any]]:
        circle_placeholders = self._placeholders(circle_ids)
        condition_placeholders = self._placeholders(condition_config_ids)
        return self._fetch_all(
            cursor,
            f"""
            SELECT n_id, n_opt_circle_id, n_para_config_id, s_value, n_condition_config_id
            FROM para
            WHERE n_opt_circle_id IN ({circle_placeholders})
              AND n_condition_config_id IN ({condition_placeholders})
            ORDER BY n_opt_circle_id ASC, n_condition_config_id ASC, n_para_config_id ASC
            """,
            [*circle_ids, *condition_config_ids],
        )

    def _list_server_modules_with_cursor(self, cursor) -> List[Dict[str, Any]]:
        return self._fetch_all(
            cursor,
            """
            SELECT id, resource_name, name, func, func_name, exe, file_path, cwd,
                   script_path, remarks, valid, process_platform, process_env, peocess_user
            FROM server_module_config
            WHERE valid = 1
            ORDER BY id ASC
            """,
            [],
        )

    def _build_job_summary_payloads(
        self,
        jobs: List[Dict[str, Any]],
        condition_configs: List[Dict[str, Any]],
        subject_configs: List[Dict[str, Any]],
        para_configs: List[Dict[str, Any]],
        resp_configs: List[Dict[str, Any]],
        circles: List[Dict[str, Any]],
        opt_data_rows: List[Dict[str, Any]],
        schedule_rows: List[Dict[str, Any]],
        post_data_rows: List[Dict[str, Any]],
        para_rows: List[Dict[str, Any]],
        module_rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        condition_configs_by_job: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in condition_configs:
            condition_configs_by_job[int(row['n_job_id'])].append(row)

        subject_by_condition_config = {
            int(row['n_condition_config_id']): self._format_subject_config(row)
            for row in subject_configs
            if row.get('n_condition_config_id') is not None
        }

        para_configs_by_job: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in para_configs:
            para_configs_by_job[int(row['n_job_id'])].append(self._format_para_config(row))

        resp_configs_by_condition_config: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in resp_configs:
            resp_configs_by_condition_config[int(row['n_condition_config_id'])].append(row)

        circles_by_job: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for circle in circles:
            circles_by_job[int(circle['n_job_id'])].append(circle)

        opt_data_by_circle_condition: Dict[tuple[int, int], Dict[str, Any]] = {}
        for row in opt_data_rows:
            opt_data_by_circle_condition[
                (int(row['n_opt_circle_id']), int(row['n_condition_config_id']))
            ] = row

        schedules_by_opt_data_id: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in schedule_rows:
            schedules_by_opt_data_id[int(row['opt_data_id'])].append(row)

        post_data_by_schedule_resp: Dict[tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
        for row in post_data_rows:
            post_data_by_schedule_resp[(int(row['task_id']), int(row['resp_config_id']))].append(row)

        para_rows_by_circle_condition: Dict[tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
        for row in para_rows:
            para_rows_by_circle_condition[
                (int(row['n_opt_circle_id']), int(row['n_condition_config_id']))
            ].append(row)

        summaries: List[Dict[str, Any]] = []
        for job in jobs:
            job_id = int(job['id'])
            job_condition_configs = condition_configs_by_job.get(job_id, [])
            condition_config_payloads = [
                self._format_condition_config(row, subject_by_condition_config.get(int(row['n_id'])))
                for row in job_condition_configs
            ]
            round_summaries = self._build_round_summaries(
                circles=circles_by_job.get(job_id, []),
                condition_configs=job_condition_configs,
                resp_configs_by_condition_config=resp_configs_by_condition_config,
                opt_data_by_circle_condition=opt_data_by_circle_condition,
                schedules_by_opt_data_id=schedules_by_opt_data_id,
                post_data_by_schedule_resp=post_data_by_schedule_resp,
                para_rows_by_circle_condition=para_rows_by_circle_condition,
            )
            summaries.append(
                {
                    'id': job_id,
                    'issueId': job.get('issue_id'),
                    'jobName': job.get('s_job_name'),
                    'optType': job.get('n_opt_type'),
                    'jobSignal': job.get('job_signal'),
                    'baseDir': job.get('base_dir'),
                    'jobDir': job.get('job_dir'),
                    'batchSize': job.get('batch_size'),
                    'inputJson': job.get('input_json'),
                    'caseDesc': job.get('case_desc'),
                    'caseOrder': job.get('n_case_order'),
                    'paraJsonFilePath': job.get('para_json_file_path'),
                    'paraInequality': job.get('para_inequality'),
                    'conditionConfigs': condition_config_payloads,
                    'subjectConfigs': [item.get('subjectConfig') for item in condition_config_payloads if item.get('subjectConfig')],
                    'paraConfigs': para_configs_by_job.get(job_id, []),
                    'outputConfigs': [
                        self._format_resp_config(row)
                        for config_rows in resp_configs_by_condition_config.values()
                        for row in config_rows
                        if any(int(row['n_condition_config_id']) == int(config['n_id']) for config in job_condition_configs)
                    ],
                    'serverModules': module_rows,
                    'status': self._resolve_job_status(job, round_summaries),
                    'progress': self._resolve_job_progress(round_summaries),
                    'rounds': round_summaries,
                }
            )
        return summaries

    def _build_round_summaries(
        self,
        circles: List[Dict[str, Any]],
        condition_configs: List[Dict[str, Any]],
        resp_configs_by_condition_config: Dict[int, List[Dict[str, Any]]],
        opt_data_by_circle_condition: Dict[tuple[int, int], Dict[str, Any]],
        schedules_by_opt_data_id: Dict[int, List[Dict[str, Any]]],
        post_data_by_schedule_resp: Dict[tuple[int, int], List[Dict[str, Any]]],
        para_rows_by_circle_condition: Dict[tuple[int, int], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        round_summaries: List[Dict[str, Any]] = []
        condition_config_ids = [int(row['n_id']) for row in condition_configs]
        for index, circle in enumerate(circles, start=1):
            circle_id = int(circle['n_id'])
            outputs: List[Dict[str, Any]] = []
            params: List[Dict[str, Any]] = []
            opt_data_rows: List[Dict[str, Any]] = []
            for condition_config_id in condition_config_ids:
                opt_data = opt_data_by_circle_condition.get((circle_id, condition_config_id))
                expected_resp_configs = resp_configs_by_condition_config.get(condition_config_id, [])
                if opt_data:
                    opt_data_rows.append(opt_data)
                    params.extend(para_rows_by_circle_condition.get((circle_id, condition_config_id), []))
                    schedules = schedules_by_opt_data_id.get(int(opt_data['id']), [])
                    for resp_config in expected_resp_configs:
                        resp_config_id = int(resp_config['n_id'])
                        matched_posts = [
                            post
                            for schedule in schedules
                            for post in post_data_by_schedule_resp.get((int(schedule['id']), resp_config_id), [])
                        ]
                        if matched_posts:
                            outputs.extend(
                                self._build_output_summary(resp_config, post, condition_config_id, opt_data, schedules)
                                for post in matched_posts
                            )
                        else:
                            outputs.append(self._build_output_summary(resp_config, None, condition_config_id, opt_data, schedules))
                else:
                    outputs.extend(
                        self._build_output_summary(resp_config, None, condition_config_id, None, [])
                        for resp_config in expected_resp_configs
                    )

            round_summaries.append(
                {
                    'roundIndex': int(circle.get('n_circle') or index),
                    'circleId': circle_id,
                    'circlePath': circle.get('s_circle_path'),
                    'runNum': circle.get('n_run_num'),
                    'finalValue': circle.get('n_total_value'),
                    'status': self._resolve_round_status(circle, opt_data_rows, outputs),
                    'runningModule': self._first_running_module(opt_data_rows),
                    'params': params,
                    'outputs': outputs,
                }
            )
        return round_summaries

    @staticmethod
    def _format_condition_config(row: Dict[str, Any], subject_config: Dict[str, Any] | None) -> Dict[str, Any]:
        return {
            'conditionConfigId': row.get('n_id'),
            'name': row.get('s_name'),
            'setName': row.get('s_set_name'),
            'jobId': row.get('n_job_id'),
            'userAccount': row.get('user_account'),
            'userName': row.get('user_name'),
            'conditionDir': row.get('s_condition_dir'),
            'inputFiles': row.get('s_input_files'),
            'subjectType': row.get('n_subject_type'),
            'paramNames': row.get('s_param_names'),
            'subjectConfig': subject_config,
        }

    @staticmethod
    def _format_subject_config(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': row.get('n_id'),
            'conditionConfigId': row.get('n_condition_config_id'),
            'modelLevel': row.get('n_model_level'),
            'simulationType': row.get('n_simulation_type'),
            'solverType': row.get('n_solver_type'),
            'cpuCores': row.get('n_cpu_cores'),
            'cpuType': row.get('n_cpu_type'),
            'doubleType': row.get('n_double_type'),
            'rotateDrop': row.get('n_rotate_drop'),
            'submitSourceType': row.get('n_submit_source_type'),
        }

    @staticmethod
    def _format_para_config(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': row.get('n_id'),
            'jobId': row.get('n_job_id'),
            'name': row.get('s_name'),
            'unit': row.get('s_unit'),
            'type': row.get('s_type'),
            'initialValue': row.get('s_inital_value'),
            'range': row.get('s_range'),
            'componentName': row.get('s_comp_name'),
            'jsonFilePath': row.get('s_json_file_path'),
        }

    @staticmethod
    def _format_resp_config(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'respConfigId': row.get('n_id'),
            'conditionConfigId': row.get('n_condition_config_id'),
            'respName': row.get('s_name'),
            'setName': row.get('s_set_name'),
            'outputType': row.get('s_output_type'),
            'weight': row.get('n_weight'),
            'multiple': row.get('n_multiple'),
            'target': row.get('n_target'),
            'targetValue': row.get('n_target_value'),
            'lowerLimit': row.get('n_lower_limit'),
            'upperLimit': row.get('n_upper_limit'),
            'expression': row.get('s_experssion'),
            'component': row.get('s_customize_param1'),
            'customizeParam2': row.get('s_customize_param2'),
            'customizeParam3': row.get('s_customize_param3'),
            'integrationPoint': row.get('s_customize_param4'),
            'pushSet': row.get('s_customize_param5'),
            'stepName': row.get('s_step_name'),
        }

    def _build_output_summary(
        self,
        resp_config: Dict[str, Any],
        post_data: Dict[str, Any] | None,
        condition_config_id: int,
        opt_data: Dict[str, Any] | None,
        schedules: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = self._format_resp_config(resp_config)
        payload.update(
            {
                'taskId': post_data.get('task_id') if post_data else (schedules[0].get('id') if schedules else None),
                'conditionConfigId': condition_config_id,
                'optDataId': opt_data.get('id') if opt_data else None,
                'dataDir': opt_data.get('data_dir') if opt_data else None,
                'originValue': post_data.get('origin_value') if post_data else None,
                'finalValue': post_data.get('final_value') if post_data else None,
                'bestTime': post_data.get('best_time') if post_data else None,
                'bestLabel': post_data.get('best_label') if post_data else None,
                'imagePaths': [
                    value
                    for value in (
                        post_data.get('curvers_png_path') if post_data else None,
                        post_data.get('cloud_png_path1') if post_data else None,
                        post_data.get('cloud_png_path2') if post_data else None,
                    )
                    if value
                ],
                'curveJsonPath': post_data.get('curvers_json_path') if post_data else None,
                'aviPaths': [
                    value
                    for value in (
                        post_data.get('avi_path1') if post_data else None,
                        post_data.get('avi_path2') if post_data else None,
                    )
                    if value
                ],
                'errors': post_data.get('s_errors') if post_data else (opt_data.get('s_errors') if opt_data else None),
            }
        )
        return payload

    @staticmethod
    def _first_running_module(opt_data_rows: List[Dict[str, Any]]) -> str | None:
        modules = [str(row.get('running_module')).strip() for row in opt_data_rows if row.get('running_module')]
        return sorted(set(modules))[0] if modules else None

    @staticmethod
    def _resolve_round_status(circle: Dict[str, Any], opt_data_rows: List[Dict[str, Any]], output_summaries: List[Dict[str, Any]]) -> int:
        circle_status = circle.get('n_status')
        if circle_status is not None:
            try:
                return int(circle_status)
            except (TypeError, ValueError):
                pass
        if any(output.get('finalValue') not in (None, '') for output in output_summaries):
            return 2
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
        return int(round((completed / max(len(round_summaries), 1)) * 100))


optimization_repository = OptimizationRepository()
