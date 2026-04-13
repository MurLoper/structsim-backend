"""Rebuild external mock schemas for simulation_project and union_opt_kernal.

This script is for local/test integration only. It recreates the mock read-only
external structures, then backfills local order/case/condition rows with stable
mock issue/job/condition_config ids so the result API can resolve the chain.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor
from sqlalchemy import create_engine, text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import Config  # noqa: E402


@dataclass(frozen=True)
class LocalConditionLink:
    order_id: int
    order_no: str
    project_id: int | None
    phase_id: int | None
    domain_account: str | None
    created_by: str | None
    remark: str | None
    case_id: int
    case_index: int
    case_name: str | None
    condition_row_id: int
    condition_id: int
    fold_type_id: int
    fold_type_name: str | None
    sim_type_id: int
    sim_type_name: str | None
    rotate_drop_flag: int
    round_total: int
    output_count: int
    opt_issue_id: int
    opt_job_id: int
    opt_condition_config_id: int


def _external_conn(database: str | None = None):
    return pymysql.connect(
        host=Config.EXTERNAL_MYSQL_HOST,
        port=int(Config.EXTERNAL_MYSQL_PORT),
        user=Config.EXTERNAL_MYSQL_USER,
        password=Config.EXTERNAL_MYSQL_PASSWORD,
        database=database,
        charset=Config.EXTERNAL_MYSQL_CHARSET,
        cursorclass=DictCursor,
        autocommit=False,
    )


def _execute_many(cursor, statements: Iterable[str]) -> None:
    for statement in statements:
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as exc:
                preview = ' '.join(statement.strip().split())[:180]
                raise RuntimeError(f'执行 SQL 失败: {preview}') from exc


def rebuild_simulation_project_schema(cursor) -> None:
    schema = Config.EXTERNAL_MYSQL_SCHEMA_SIMULATION_PROJECT
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{schema}` DEFAULT CHARACTER SET utf8mb4")
    cursor.execute(f"USE `{schema}`")
    _execute_many(
        cursor,
        [
            "DROP TABLE IF EXISTS pp_phase",
            "DROP TABLE IF EXISTS phase",
            """
            CREATE TABLE phase (
                phase_id INT NOT NULL PRIMARY KEY,
                phase_desc VARCHAR(100) NOT NULL,
                sort_order INT DEFAULT 0,
                valid TINYINT DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE pp_phase (
                pp_phase_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
                pp_record_id INT NOT NULL,
                phase_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                KEY idx_pp_phase_project (pp_record_id),
                KEY idx_pp_phase_phase (phase_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ],
    )
    cursor.executemany(
        "INSERT INTO phase (phase_id, phase_desc, sort_order, valid) VALUES (%s, %s, %s, %s)",
        [
            (1, '方案阶段', 1, 1),
            (2, '试验阶段', 2, 1),
            (3, '量产阶段', 3, 1),
        ],
    )
    pp_rows = [(project_id, ((project_id - 1751) % 3) + 1) for project_id in range(1751, 1761)]
    cursor.executemany(
        "INSERT INTO pp_phase (pp_record_id, phase_id) VALUES (%s, %s)",
        pp_rows,
    )


UNION_DROP_ORDER = [
    'post_data_save',
    'post_schedule_info',
    'post_schedule',
    'para',
    'opt_data',
    'opt_circle',
    'opt_circles',
    'resp_config',
    'para_config',
    'subject_config_struct',
    'job_condition_config',
    'server_module_config',
    'jobs',
    'opt_issues',
]


UNION_CREATE_SQL = [
    """
    CREATE TABLE opt_issues (
        id BIGINT NOT NULL PRIMARY KEY,
        user_name VARCHAR(100),
        user_account VARCHAR(100),
        project_id INT,
        project_phase_id INT,
        sys_phase INT,
        issue_desc TEXT,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP NULL DEFAULT NULL,
        n_is_auto_opt TINYINT DEFAULT 1,
        can_save_users TEXT,
        care_device_ids TEXT,
        KEY idx_issue_project (project_id),
        KEY idx_issue_user (user_account)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE jobs (
        id BIGINT NOT NULL PRIMARY KEY,
        issue_id BIGINT NOT NULL,
        s_job_name VARCHAR(200),
        n_opt_type INT DEFAULT 99,
        job_signal VARCHAR(64),
        base_dir VARCHAR(500),
        job_dir VARCHAR(500),
        batch_size INT,
        input_json TEXT,
        case_desc TEXT,
        pre_task_id BIGINT,
        n_case_order INT,
        start_time TIMESTAMP NULL DEFAULT NULL,
        end_time TIMESTAMP NULL DEFAULT NULL,
        para_json_file_path VARCHAR(500),
        para_inequality TEXT,
        KEY idx_jobs_issue (issue_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE job_condition_config (
        n_id BIGINT NOT NULL PRIMARY KEY,
        s_name VARCHAR(200),
        s_set_name VARCHAR(200),
        n_job_id BIGINT NOT NULL,
        user_account VARCHAR(100),
        user_name VARCHAR(100),
        s_condition_dir VARCHAR(500),
        s_input_files TEXT,
        n_subject_type INT DEFAULT 0,
        s_param_names TEXT,
        KEY idx_jcc_job (n_job_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE subject_config_struct (
        n_id BIGINT NOT NULL PRIMARY KEY,
        n_condition_config_id BIGINT NOT NULL,
        n_model_level INT,
        n_simulation_type INT,
        n_solver_type INT,
        n_cpu_cores INT,
        n_cpu_type INT,
        n_double_type INT,
        n_rotate_drop TINYINT DEFAULT 0,
        n_submit_source_type INT,
        KEY idx_subject_condition (n_condition_config_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE para_config (
        n_id BIGINT NOT NULL PRIMARY KEY,
        n_job_id BIGINT NOT NULL,
        s_name VARCHAR(100),
        s_unit VARCHAR(50),
        s_type VARCHAR(50),
        s_inital_value VARCHAR(100),
        s_range VARCHAR(255),
        s_comp_name VARCHAR(100),
        s_json_file_path VARCHAR(500),
        KEY idx_para_config_job (n_job_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE resp_config (
        n_id BIGINT NOT NULL PRIMARY KEY,
        n_condition_config_id BIGINT NOT NULL,
        s_name VARCHAR(100),
        s_set_name VARCHAR(100),
        s_output_type VARCHAR(50),
        n_weight DOUBLE,
        n_multiple DOUBLE,
        n_target INT,
        n_target_value DOUBLE,
        n_lower_limit DOUBLE,
        n_upper_limit DOUBLE,
        s_experssion TEXT,
        s_customize_param1 VARCHAR(255),
        s_customize_param2 VARCHAR(255),
        s_customize_param3 VARCHAR(255),
        s_customize_param4 VARCHAR(255),
        s_customize_param5 VARCHAR(255),
        s_step_name VARCHAR(100),
        KEY idx_resp_condition (n_condition_config_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE opt_circle (
        n_id BIGINT NOT NULL PRIMARY KEY,
        n_job_id BIGINT NOT NULL,
        n_circle INT,
        n_run_num INT,
        s_circle_path VARCHAR(500),
        n_status INT,
        n_total_value DOUBLE,
        d_update TIMESTAMP NULL DEFAULT NULL,
        KEY idx_circle_job (n_job_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE opt_data (
        id BIGINT NOT NULL PRIMARY KEY,
        n_opt_circle_id BIGINT NOT NULL,
        n_condition_config_id BIGINT NOT NULL,
        data_dir VARCHAR(500),
        opt_data_signal VARCHAR(64),
        s_errors TEXT,
        task_id BIGINT,
        total_time DOUBLE,
        calc_time DOUBLE,
        process_id BIGINT,
        task_record_id BIGINT,
        need_down_result TINYINT,
        running_module VARCHAR(100),
        running_status VARCHAR(100),
        KEY idx_opt_data_circle (n_opt_circle_id),
        KEY idx_opt_data_condition (n_condition_config_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE post_schedule_info (
        id BIGINT NOT NULL PRIMARY KEY,
        opt_data_id BIGINT NOT NULL,
        running TINYINT,
        result VARCHAR(100),
        odb_path VARCHAR(500),
        start_time TIMESTAMP NULL DEFAULT NULL,
        end_time TIMESTAMP NULL DEFAULT NULL,
        KEY idx_post_schedule_opt_data (opt_data_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE post_data_save (
        id BIGINT NOT NULL PRIMARY KEY,
        task_id BIGINT NOT NULL,
        resp_config_id BIGINT NOT NULL,
        best_time DOUBLE,
        best_label VARCHAR(100),
        origin_value DOUBLE,
        final_value DOUBLE,
        curvers_json_path VARCHAR(500),
        curvers_png_path VARCHAR(500),
        cloud_png_path1 VARCHAR(500),
        cloud_png_path2 VARCHAR(500),
        avi_path1 VARCHAR(500),
        avi_path2 VARCHAR(500),
        start_time TIMESTAMP NULL DEFAULT NULL,
        end_time TIMESTAMP NULL DEFAULT NULL,
        s_errors TEXT,
        max_gif_x VARCHAR(500),
        max_gif_y VARCHAR(500),
        KEY idx_post_task (task_id),
        KEY idx_post_resp (resp_config_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE para (
        n_id BIGINT NOT NULL PRIMARY KEY,
        n_opt_circle_id BIGINT NOT NULL,
        n_para_config_id BIGINT NOT NULL,
        s_value VARCHAR(100),
        n_condition_config_id BIGINT NOT NULL,
        KEY idx_para_circle (n_opt_circle_id),
        KEY idx_para_condition (n_condition_config_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE server_module_config (
        id INT NOT NULL PRIMARY KEY,
        resource_name VARCHAR(100),
        name VARCHAR(100),
        func VARCHAR(100),
        func_name VARCHAR(100),
        exe VARCHAR(255),
        file_path VARCHAR(500),
        cwd VARCHAR(500),
        script_path VARCHAR(500),
        remarks TEXT,
        valid TINYINT DEFAULT 1,
        process_platform VARCHAR(100),
        process_env INT,
        peocess_user VARCHAR(100)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def rebuild_union_schema(cursor) -> None:
    schema = Config.EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{schema}` DEFAULT CHARACTER SET utf8mb4")
    cursor.execute(f"USE `{schema}`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("SHOW TABLES")
    existing_tables = [next(iter(row.values())) for row in cursor.fetchall()]
    for table in [*UNION_DROP_ORDER, *existing_tables]:
        cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    _execute_many(cursor, UNION_CREATE_SQL)
    cursor.executemany(
        """
        INSERT INTO server_module_config (
            id, resource_name, name, func, func_name, exe, file_path, cwd,
            script_path, remarks, valid, process_platform, process_env, peocess_user
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            (1, 'PREPARE', '前处理', 'prepare', 'prepare_case', 'python', '/opt/scripts/prepare.py', '/work', '/opt/scripts', 'mock', 1, 'linux', 1, 'structsim'),
            (2, 'SOLVE', '求解', 'solve', 'run_solver', 'python', '/opt/scripts/solve.py', '/work', '/opt/scripts', 'mock', 1, 'linux', 1, 'structsim'),
            (3, 'POST', '后处理', 'post', 'post_process', 'python', '/opt/scripts/post.py', '/work', '/opt/scripts', 'mock', 1, 'linux', 1, 'structsim'),
        ],
    )


def _local_engine():
    db_url = os.getenv('DATABASE_URL') or Config.SQLALCHEMY_DATABASE_URI
    if not db_url or db_url.startswith('sqlite:'):
        return None
    return create_engine(db_url, pool_pre_ping=True)


def load_and_backfill_local_links() -> List[LocalConditionLink]:
    engine = _local_engine()
    if engine is None:
        return []
    with engine.begin() as conn:
        table_names = {row[0] for row in conn.execute(text('SHOW TABLES')).fetchall()}
        if not {'orders', 'order_case_opti', 'case_condition_opti'}.issubset(table_names):
            return []
        rows = conn.execute(
            text(
                """
                SELECT
                    o.id AS order_id, o.order_no, o.project_id, o.phase_id, o.domain_account,
                    o.created_by, o.remark,
                    oc.id AS case_id, oc.case_index, oc.case_name,
                    cc.id AS condition_row_id, cc.condition_id, cc.fold_type_id,
                    cc.fold_type_name, cc.sim_type_id, cc.sim_type_name,
                    cc.rotate_drop_flag, cc.round_total, cc.output_count,
                    COALESCE(NULLIF(o.opt_issue_id, 0), 600000000 + o.id) AS resolved_issue_id,
                    COALESCE(NULLIF(oc.opt_job_id, 0), 700000000 + oc.id * 10) AS resolved_job_id,
                    COALESCE(NULLIF(cc.opt_condition_config_id, 0), 710000000 + cc.id * 10) AS resolved_condition_config_id
                FROM case_condition_opti cc
                JOIN order_case_opti oc ON oc.id = cc.order_case_id
                JOIN orders o ON o.id = cc.order_id
                ORDER BY o.id ASC, oc.case_index ASC, cc.id ASC
                """
            )
        ).mappings().all()
        links = [
            LocalConditionLink(
                order_id=int(row['order_id']),
                order_no=str(row['order_no'] or f'ORD-{row["order_id"]}'),
                project_id=row['project_id'],
                phase_id=row['phase_id'],
                domain_account=row['domain_account'],
                created_by=row['created_by'],
                remark=row['remark'],
                case_id=int(row['case_id']),
                case_index=int(row['case_index'] or 1),
                case_name=row['case_name'],
                condition_row_id=int(row['condition_row_id']),
                condition_id=int(row['condition_id'] or row['condition_row_id']),
                fold_type_id=int(row['fold_type_id'] or 0),
                fold_type_name=row['fold_type_name'],
                sim_type_id=int(row['sim_type_id'] or 0),
                sim_type_name=row['sim_type_name'],
                rotate_drop_flag=int(row['rotate_drop_flag'] or 0),
                round_total=int(row['round_total'] or 8),
                output_count=max(int(row['output_count'] or 3), 1),
                opt_issue_id=int(row['resolved_issue_id']),
                opt_job_id=int(row['resolved_job_id']),
                opt_condition_config_id=int(row['resolved_condition_config_id']),
            )
            for row in rows
        ]
        for link in links:
            conn.execute(text('UPDATE orders SET opt_issue_id = :issue_id WHERE id = :order_id AND COALESCE(opt_issue_id, 0) = 0'), {'issue_id': link.opt_issue_id, 'order_id': link.order_id})
            conn.execute(
                text(
                    """
                    UPDATE order_case_opti
                    SET opt_issue_id = :issue_id, opt_job_id = :job_id, status = 1, process = 60
                    WHERE id = :case_id
                    """
                ),
                {'issue_id': link.opt_issue_id, 'job_id': link.opt_job_id, 'case_id': link.case_id},
            )
            conn.execute(
                text(
                    """
                    UPDATE case_condition_opti
                    SET opt_issue_id = :issue_id, opt_job_id = :job_id,
                        opt_condition_config_id = :condition_config_id, status = 1, process = 60
                    WHERE id = :condition_row_id
                    """
                ),
                {
                    'issue_id': link.opt_issue_id,
                    'job_id': link.opt_job_id,
                    'condition_config_id': link.opt_condition_config_id,
                    'condition_row_id': link.condition_row_id,
                },
            )
        return links


def fallback_links() -> List[LocalConditionLink]:
    links: List[LocalConditionLink] = []
    for order_index in range(1, 4):
        issue_id = 600000000 + order_index
        case_count = order_index
        for case_index in range(1, case_count + 1):
            job_id = 700000000 + order_index * 100 + case_index
            condition_count = ((order_index + case_index) % 3) + 1
            for condition_index in range(1, condition_count + 1):
                links.append(
                    LocalConditionLink(
                        order_id=order_index,
                        order_no=f'MOCK-ORDER-{order_index}',
                        project_id=1750 + order_index,
                        phase_id=((order_index - 1) % 3) + 1,
                        domain_account='a00012346',
                        created_by='a00012346',
                        remark='external mock',
                        case_id=order_index * 100 + case_index,
                        case_index=case_index,
                        case_name=f'方案-{case_index}',
                        condition_row_id=order_index * 1000 + case_index * 10 + condition_index,
                        condition_id=condition_index,
                        fold_type_id=condition_index,
                        fold_type_name=f'工况{condition_index}',
                        sim_type_id=condition_index,
                        sim_type_name=f'仿真{condition_index}',
                        rotate_drop_flag=condition_index % 2,
                        round_total=12 + order_index * 2,
                        output_count=3,
                        opt_issue_id=issue_id,
                        opt_job_id=job_id,
                        opt_condition_config_id=710000000 + order_index * 1000 + case_index * 10 + condition_index,
                    )
                )
    return links


def seed_union_mock_data(cursor, links: List[LocalConditionLink]) -> None:
    links_by_issue: Dict[int, List[LocalConditionLink]] = {}
    links_by_job: Dict[int, List[LocalConditionLink]] = {}
    for link in links:
        links_by_issue.setdefault(link.opt_issue_id, []).append(link)
        links_by_job.setdefault(link.opt_job_id, []).append(link)

    for issue_id, issue_links in links_by_issue.items():
        first = issue_links[0]
        cursor.execute(
            """
            INSERT INTO opt_issues (
                id, user_name, user_account, project_id, project_phase_id, sys_phase,
                issue_desc, n_is_auto_opt, can_save_users, care_device_ids
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                issue_id,
                first.domain_account or first.created_by,
                first.domain_account or first.created_by,
                first.project_id,
                first.phase_id,
                1,
                first.remark,
                1,
                json.dumps([first.created_by or first.domain_account], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
            ),
        )

    for job_id, job_links in links_by_job.items():
        first = job_links[0]
        base_dir = f'/mock/structsim/{first.order_no}'
        cursor.execute(
            """
            INSERT INTO jobs (
                id, issue_id, s_job_name, n_opt_type, job_signal, base_dir, job_dir,
                batch_size, input_json, case_desc, n_case_order, para_json_file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job_id,
                first.opt_issue_id,
                first.case_name or f'Case-{first.case_index}',
                99,
                'running',
                base_dir,
                f'{base_dir}/case-{first.case_index}',
                max(first.round_total, 8),
                json.dumps({'mock': True, 'orderNo': first.order_no}, ensure_ascii=False),
                first.case_name,
                first.case_index,
                f'{base_dir}/case-{first.case_index}/para.json',
            ),
        )
        for index, name in enumerate(('thickness', 'rib_height', 'angle'), start=1):
            cursor.execute(
                """
                INSERT INTO para_config (
                    n_id, n_job_id, s_name, s_unit, s_type, s_inital_value,
                    s_range, s_comp_name, s_json_file_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (job_id * 100 + index, job_id, name, 'mm' if index < 3 else 'deg', 'float', '1.0', '[0,10]', 'mock_component', f'/mock/{job_id}/{name}.json'),
            )

        for link in job_links:
            seed_condition(cursor, link)
        seed_rounds(cursor, job_id, job_links)


def seed_condition(cursor, link: LocalConditionLink) -> None:
    cursor.execute(
        """
        INSERT INTO job_condition_config (
            n_id, s_name, s_set_name, n_job_id, user_account, user_name,
            s_condition_dir, s_input_files, n_subject_type, s_param_names
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            link.opt_condition_config_id,
            f'{link.condition_id}_{link.fold_type_name or "工况"}_{link.sim_type_name or "仿真"}',
            'MOCK_SET',
            link.opt_job_id,
            link.domain_account or link.created_by,
            link.created_by or link.domain_account,
            f'condition-{link.opt_condition_config_id}',
            json.dumps([], ensure_ascii=False),
            0,
            'thickness,rib_height,angle',
        ),
    )
    cursor.execute(
        """
        INSERT INTO subject_config_struct (
            n_id, n_condition_config_id, n_model_level, n_simulation_type,
            n_solver_type, n_cpu_cores, n_cpu_type, n_double_type,
            n_rotate_drop, n_submit_source_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (link.opt_condition_config_id, link.opt_condition_config_id, 1, link.sim_type_id, 1, 16, 1, 0, link.rotate_drop_flag, 2),
    )
    for output_index in range(1, max(link.output_count, 3) + 1):
        cursor.execute(
            """
            INSERT INTO resp_config (
                n_id, n_condition_config_id, s_name, s_set_name, s_output_type,
                n_weight, n_multiple, n_target, n_target_value, s_customize_param1,
                s_customize_param4, s_customize_param5, s_step_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                link.opt_condition_config_id * 100 + output_index,
                link.opt_condition_config_id,
                f'output_name_{output_index}',
                'MOCK_SET',
                'scalar',
                1,
                1,
                -1,
                None,
                '18',
                None,
                'PUSH',
                'Step-1',
            ),
        )


def seed_rounds(cursor, job_id: int, links: List[LocalConditionLink]) -> None:
    round_count = min(max(max(link.round_total for link in links), 6), 8)
    for round_index in range(1, round_count + 1):
        circle_id = job_id * 100 + round_index
        cursor.execute(
            """
            INSERT INTO opt_circle (
                n_id, n_job_id, n_circle, n_run_num, s_circle_path, n_status,
                n_total_value, d_update
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (circle_id, job_id, round_index, round_index, f'/mock/job-{job_id}/round-{round_index}', 2 if round_index % 5 else 1, round(1000 / (round_index + 1), 4)),
        )
        for link in links:
            for para_index in range(1, 4):
                cursor.execute(
                    "INSERT INTO para (n_id, n_opt_circle_id, n_para_config_id, s_value, n_condition_config_id) VALUES (%s, %s, %s, %s, %s)",
                    (circle_id * 1000 + link.opt_condition_config_id % 1000 * 10 + para_index, circle_id, job_id * 100 + para_index, str(round(para_index + round_index * 0.1, 4)), link.opt_condition_config_id),
                )
            opt_data_id = circle_id * 1000 + link.opt_condition_config_id % 1000
            cursor.execute(
                """
                INSERT INTO opt_data (
                    id, n_opt_circle_id, n_condition_config_id, data_dir, opt_data_signal,
                    task_id, total_time, calc_time, need_down_result, running_module, running_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (opt_data_id, circle_id, link.opt_condition_config_id, f'/mock/{circle_id}/{link.opt_condition_config_id}', 'done' if round_index % 5 else 'running', opt_data_id + 10, 120, 90, 1, 'POST', 'done' if round_index % 5 else 'running'),
            )
            schedule_id = opt_data_id + 30
            cursor.execute(
                "INSERT INTO post_schedule_info (id, opt_data_id, running, result, odb_path, start_time, end_time) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
                (schedule_id, opt_data_id, 0 if round_index % 5 else 1, 'ok' if round_index % 5 else 'running', f'/mock/{opt_data_id}.odb'),
            )
            if round_index % 5:
                for output_index in range(1, max(link.output_count, 3) + 1):
                    resp_config_id = link.opt_condition_config_id * 100 + output_index
                    post_id = schedule_id * 100 + output_index
                    origin = round(100 + round_index * 0.8 + output_index * 2.5 + link.condition_id, 4)
                    final = round(origin * 0.92, 4)
                    cursor.execute(
                        """
                        INSERT INTO post_data_save (
                            id, task_id, resp_config_id, best_time, best_label, origin_value,
                            final_value, curvers_json_path, curvers_png_path, cloud_png_path1,
                            cloud_png_path2, avi_path1, avi_path2, start_time, end_time
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                        (post_id, schedule_id, resp_config_id, round_index, f'round-{round_index}', origin, final, f'/mock/post/{post_id}.json', f'/mock/post/{post_id}.png', f'/mock/post/{post_id}_cloud_1.png', f'/mock/post/{post_id}_cloud_2.png', f'/mock/post/{post_id}_1.avi', f'/mock/post/{post_id}_2.avi'),
                    )


def main() -> int:
    parser = argparse.ArgumentParser(description='重建外部 mock 结构并补齐本地 issue/job/config 关联')
    parser.add_argument('--skip-local-backfill', action='store_true', help='只重建外部结构，不回填本地订单关联字段')
    args = parser.parse_args()

    load_dotenv()
    links = [] if args.skip_local_backfill else load_and_backfill_local_links()
    if not links:
        links = fallback_links()

    with _external_conn() as conn:
        try:
            with conn.cursor() as cursor:
                rebuild_simulation_project_schema(cursor)
                rebuild_union_schema(cursor)
                cursor.execute(f"USE `{Config.EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL}`")
                seed_union_mock_data(cursor, links)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    print(f'[external-mock] rebuilt simulation_project and union_opt_kernal, seeded {len(links)} condition links')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
