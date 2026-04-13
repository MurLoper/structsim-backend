from __future__ import annotations

import json
from typing import Any, Dict, List

import pymysql
from flask import current_app
from pymysql.cursors import DictCursor


class MockUnionWriter:
    """仅用于本地联调的 union_opt_kernal mock 写入器。"""

    def write_case_submission(
        self,
        order,
        case_entity,
        conditions: List[Any],
        issue_id: int,
        job_id: int,
        condition_config_ids: Dict[int, int],
    ) -> None:
        database = current_app.config['EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL']
        with self._connection(database) as conn:
            try:
                with conn.cursor() as cursor:
                    self._ensure_issue(cursor, order, issue_id)
                    self._ensure_job(cursor, order, case_entity, issue_id, job_id)
                    self._ensure_para_configs(cursor, job_id)
                    for condition in conditions:
                        condition_id = self._to_int(getattr(condition, 'id', None), 0)
                        condition_config_id = condition_config_ids.get(condition_id) or self._build_condition_config_id(condition)
                        self._ensure_condition_config(cursor, order, condition, condition_config_id, job_id)
                        self._ensure_subject_config(cursor, condition, condition_config_id)
                        self._ensure_resp_configs(cursor, condition, condition_config_id)
                    self._ensure_round_results(cursor, conditions, condition_config_ids, job_id)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def write_submission(self, order, condition, issue_id: int, job_id: int) -> None:
        condition_config_id = self._build_condition_config_id(condition)
        self.write_case_submission(order, getattr(condition, 'order_case', None), [condition], issue_id, job_id, {condition.id: condition_config_id})

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
    def _exists(cursor, table: str, id_column: str, row_id: int) -> bool:
        cursor.execute(f'SELECT {id_column} FROM {table} WHERE {id_column} = %s LIMIT 1', (row_id,))
        return cursor.fetchone() is not None

    def _ensure_issue(self, cursor, order, issue_id: int) -> None:
        if self._exists(cursor, 'opt_issues', 'id', issue_id):
            return
        cursor.execute(
            """
            INSERT INTO opt_issues (
                id, user_name, user_account, project_id, project_phase_id, sys_phase,
                issue_desc, n_is_auto_opt, can_save_users, care_device_ids
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                issue_id,
                getattr(order, 'real_name', None) or getattr(order, 'created_by', None),
                getattr(order, 'domain_account', None) or getattr(order, 'created_by', None),
                getattr(order, 'project_id', None),
                getattr(order, 'phase_id', None),
                1,
                getattr(order, 'remark', None),
                1,
                json.dumps(getattr(order, 'participant_uids', None) or [], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
            ),
        )

    def _ensure_job(self, cursor, order, case_entity, issue_id: int, job_id: int) -> None:
        if self._exists(cursor, 'jobs', 'id', job_id):
            return
        base_dir = str(getattr(order, 'base_dir', '') or '/mock/structsim').rstrip('/')
        case_index = self._to_int(getattr(case_entity, 'case_index', None), 1)
        job_dir = f'{base_dir}/{getattr(order, "order_no", issue_id)}/case-{case_index}'
        cursor.execute(
            """
            INSERT INTO jobs (
                id, issue_id, s_job_name, n_opt_type, job_signal, base_dir, job_dir,
                batch_size, input_json, case_desc, pre_task_id, n_case_order,
                para_json_file_path, para_inequality
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job_id,
                issue_id,
                getattr(case_entity, 'case_name', None) or f'Case-{case_index}',
                99,
                'running',
                base_dir,
                job_dir,
                12,
                json.dumps(getattr(order, 'input_json', None) or {}, ensure_ascii=False),
                getattr(case_entity, 'case_name', None),
                None,
                case_index,
                f'{job_dir}/para.json',
                None,
            ),
        )

    def _ensure_condition_config(self, cursor, order, condition, condition_config_id: int, job_id: int) -> None:
        if self._exists(cursor, 'job_condition_config', 'n_id', condition_config_id):
            return
        snapshot = self._normalize_dict(getattr(condition, 'condition_snapshot', None))
        fold_name = snapshot.get('foldTypeName') or getattr(condition, 'fold_type_name', None) or '工况'
        sim_name = snapshot.get('simTypeName') or getattr(condition, 'sim_type_name', None) or '仿真'
        cursor.execute(
            """
            INSERT INTO job_condition_config (
                n_id, s_name, s_set_name, n_job_id, user_account, user_name,
                s_condition_dir, s_input_files, n_subject_type, s_param_names
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                condition_config_id,
                f'{getattr(condition, "condition_id", None) or condition_config_id}_{fold_name}_{sim_name}',
                'MOCK_SET',
                job_id,
                getattr(order, 'domain_account', None) or getattr(order, 'created_by', None),
                getattr(order, 'created_by', None),
                f'condition-{condition_config_id}',
                json.dumps(snapshot.get('sourceFiles') or [], ensure_ascii=False),
                0,
                ','.join([item['name'] for item in self._mock_para_configs()]),
            ),
        )

    def _ensure_subject_config(self, cursor, condition, condition_config_id: int) -> None:
        if self._exists(cursor, 'subject_config_struct', 'n_id', condition_config_id):
            return
        cursor.execute(
            """
            INSERT INTO subject_config_struct (
                n_id, n_condition_config_id, n_model_level, n_simulation_type,
                n_solver_type, n_cpu_cores, n_cpu_type, n_double_type,
                n_rotate_drop, n_submit_source_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                condition_config_id,
                condition_config_id,
                1,
                self._to_int(getattr(condition, 'sim_type_id', None), 0),
                self._to_int(getattr(condition, 'solver_id', None), 0),
                16,
                1,
                0,
                1 if self._to_int(getattr(condition, 'rotate_drop_flag', 0), 0) else 0,
                2,
            ),
        )

    def _ensure_para_configs(self, cursor, job_id: int) -> None:
        for index, config in enumerate(self._mock_para_configs(), start=1):
            config_id = job_id * 100 + index
            if self._exists(cursor, 'para_config', 'n_id', config_id):
                continue
            cursor.execute(
                """
                INSERT INTO para_config (
                    n_id, n_job_id, s_name, s_unit, s_type, s_inital_value,
                    s_range, s_comp_name, s_json_file_path
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    config_id,
                    job_id,
                    config['name'],
                    config['unit'],
                    config['type'],
                    config['initial'],
                    config['range'],
                    config['component'],
                    f'/mock/job-{job_id}/params/{config["name"]}.json',
                ),
            )

    def _ensure_resp_configs(self, cursor, condition, condition_config_id: int) -> None:
        for index, output_name in enumerate(self._extract_output_names(condition), start=1):
            resp_config_id = condition_config_id * 100 + index
            if self._exists(cursor, 'resp_config', 'n_id', resp_config_id):
                continue
            cursor.execute(
                """
                INSERT INTO resp_config (
                    n_id, n_condition_config_id, s_name, s_set_name, s_output_type,
                    n_weight, n_multiple, n_target, n_target_value, n_lower_limit,
                    n_upper_limit, s_experssion, s_customize_param1, s_customize_param2,
                    s_customize_param3, s_customize_param4, s_customize_param5, s_step_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    resp_config_id,
                    condition_config_id,
                    output_name,
                    'MOCK_SET',
                    'scalar',
                    1,
                    1,
                    -1,
                    None,
                    None,
                    None,
                    None,
                    '18',
                    None,
                    None,
                    None,
                    'PUSH',
                    'Step-1',
                ),
            )

    def _ensure_round_results(self, cursor, conditions: List[Any], condition_config_ids: Dict[int, int], job_id: int) -> None:
        round_count = max(max(self._to_int(getattr(condition, 'round_total', None), 0), 8) for condition in conditions)
        round_count = min(round_count, 18)
        for round_index in range(1, round_count + 1):
            circle_id = job_id * 100 + round_index
            if not self._exists(cursor, 'opt_circle', 'n_id', circle_id):
                cursor.execute(
                    """
                    INSERT INTO opt_circle (
                        n_id, n_job_id, n_circle, n_run_num, s_circle_path, n_status,
                        n_total_value, d_update
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        circle_id,
                        job_id,
                        round_index,
                        round_index,
                        f'/mock/job-{job_id}/round-{round_index}',
                        2 if round_index % 5 else 1,
                        round(1000 / (round_index + 1), 4),
                    ),
                )
            self._ensure_round_params(cursor, job_id, circle_id, round_index, conditions, condition_config_ids)
            self._ensure_round_outputs(cursor, circle_id, round_index, conditions, condition_config_ids)

    def _ensure_round_params(self, cursor, job_id: int, circle_id: int, round_index: int, conditions: List[Any], condition_config_ids: Dict[int, int]) -> None:
        for condition in conditions:
            condition_config_id = condition_config_ids[self._to_int(getattr(condition, 'id', None), 0)]
            for index, _config in enumerate(self._mock_para_configs(), start=1):
                para_id = circle_id * 1000 + condition_config_id % 1000 * 10 + index
                if self._exists(cursor, 'para', 'n_id', para_id):
                    continue
                cursor.execute(
                    """
                    INSERT INTO para (n_id, n_opt_circle_id, n_para_config_id, s_value, n_condition_config_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        para_id,
                        circle_id,
                        job_id * 100 + index,
                        str(round(1.0 + round_index * 0.1 + index, 4)),
                        condition_config_id,
                    ),
                )

    def _ensure_round_outputs(self, cursor, circle_id: int, round_index: int, conditions: List[Any], condition_config_ids: Dict[int, int]) -> None:
        for condition in conditions:
            condition_id = self._to_int(getattr(condition, 'id', None), 0)
            condition_config_id = condition_config_ids[condition_id]
            opt_data_id = circle_id * 1000 + condition_config_id % 1000
            if not self._exists(cursor, 'opt_data', 'id', opt_data_id):
                cursor.execute(
                    """
                    INSERT INTO opt_data (
                        id, n_opt_circle_id, n_condition_config_id, data_dir, opt_data_signal,
                        s_errors, task_id, total_time, calc_time, process_id, task_record_id,
                        need_down_result, running_module, running_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        opt_data_id,
                        circle_id,
                        condition_config_id,
                        f'/mock/circle-{circle_id}/condition-{condition_config_id}',
                        'done' if round_index % 5 else 'running',
                        None,
                        opt_data_id + 10,
                        120 + round_index,
                        95 + round_index,
                        None,
                        opt_data_id + 20,
                        1,
                        'POST',
                        'done' if round_index % 5 else 'running',
                    ),
                )
            schedule_id = opt_data_id + 30
            if not self._exists(cursor, 'post_schedule_info', 'id', schedule_id):
                cursor.execute(
                    """
                    INSERT INTO post_schedule_info (id, opt_data_id, running, result, odb_path, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (schedule_id, opt_data_id, 0 if round_index % 5 else 1, 'ok' if round_index % 5 else 'running', f'/mock/{opt_data_id}.odb'),
                )
            if round_index % 5:
                self._ensure_post_results(cursor, schedule_id, condition, condition_config_id, round_index)

    def _ensure_post_results(self, cursor, schedule_id: int, condition, condition_config_id: int, round_index: int) -> None:
        for index, _output_name in enumerate(self._extract_output_names(condition), start=1):
            resp_config_id = condition_config_id * 100 + index
            post_data_id = schedule_id * 100 + index
            if self._exists(cursor, 'post_data_save', 'id', post_data_id):
                continue
            origin = self._mock_origin_value(condition, index, round_index)
            final = round(origin * 0.92, 4)
            cursor.execute(
                """
                INSERT INTO post_data_save (
                    id, task_id, resp_config_id, best_time, best_label, origin_value,
                    final_value, curvers_json_path, curvers_png_path, cloud_png_path1,
                    cloud_png_path2, avi_path1, avi_path2, start_time, end_time,
                    s_errors, max_gif_x, max_gif_y
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s)
                """,
                (
                    post_data_id,
                    schedule_id,
                    resp_config_id,
                    round_index,
                    f'round-{round_index}',
                    origin,
                    final,
                    f'/mock/post/{post_data_id}.json',
                    f'/mock/post/{post_data_id}.png',
                    f'/mock/post/{post_data_id}_cloud_1.png',
                    f'/mock/post/{post_data_id}_cloud_2.png',
                    f'/mock/post/{post_data_id}_1.avi',
                    f'/mock/post/{post_data_id}_2.avi',
                    None,
                    None,
                    None,
                ),
            )

    @staticmethod
    def _mock_para_configs() -> List[Dict[str, str]]:
        return [
            {'name': 'thickness', 'unit': 'mm', 'type': 'float', 'initial': '1.2', 'range': '[0.8,2.0]', 'component': 'shell'},
            {'name': 'rib_height', 'unit': 'mm', 'type': 'float', 'initial': '12', 'range': '[8,18]', 'component': 'rib'},
            {'name': 'angle', 'unit': 'deg', 'type': 'float', 'initial': '45', 'range': '[30,60]', 'component': 'corner'},
        ]

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
                    names.append(str(raw_name or f'output_{index}'))
        if names:
            return names[:6]
        output_count = max(self._to_int(getattr(condition, 'output_count', None), 0), 1)
        return [f'output_{index}' for index in range(1, min(output_count, 3) + 1)]

    @staticmethod
    def _build_condition_config_id(condition) -> int:
        return 710_000_000 + max(int(getattr(condition, 'id', 0) or 0), 0) * 10

    @staticmethod
    def _bounded_condition_seed(condition) -> int:
        return max(int(getattr(condition, 'id', 0) or 0), 0) % 10_000

    def _mock_origin_value(self, condition, index: int, round_index: int) -> float:
        seed = self._bounded_condition_seed(condition)
        return round(100.0 + seed % 97 + index * 2.5 + round_index * 0.73, 4)

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


mock_union_writer = MockUnionWriter()
