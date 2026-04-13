from __future__ import annotations

import argparse
import os
from typing import Iterable

from sqlalchemy import create_engine, inspect, text


ORDER_CASE_TABLE_SQL = """
CREATE TABLE order_case_opti (
  id BIGINT NOT NULL AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  order_no VARCHAR(50) DEFAULT NULL,
  case_index INT NOT NULL DEFAULT 1,
  case_name VARCHAR(200) DEFAULT NULL,
  opt_issue_id INT NOT NULL DEFAULT 0,
  opt_job_id INT DEFAULT NULL,
  parameter_scope VARCHAR(32) NOT NULL DEFAULT 'per_condition',
  case_snapshot JSON DEFAULT NULL,
  external_meta JSON DEFAULT NULL,
  status SMALLINT DEFAULT 0,
  process DECIMAL(5,2) DEFAULT 0,
  created_at INT DEFAULT NULL,
  updated_at INT DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_case_index (order_id, case_index),
  UNIQUE KEY uk_order_case_opt_job_id (opt_job_id),
  KEY idx_order_case_order_id (order_id),
  KEY idx_order_case_opt_issue_id (opt_issue_id),
  KEY idx_order_case_status (order_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单自动化case/job映射表'
"""


CASE_CONDITION_TABLE_SQL = """
CREATE TABLE case_condition_opti (
  id BIGINT NOT NULL AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  order_no VARCHAR(50) DEFAULT NULL,
  order_case_id BIGINT NOT NULL,
  case_index INT NOT NULL DEFAULT 1,
  opt_issue_id INT NOT NULL DEFAULT 0,
  opt_job_id INT DEFAULT NULL,
  opt_condition_config_id INT DEFAULT NULL,
  parameter_scope VARCHAR(32) NOT NULL DEFAULT 'per_condition',
  rotate_drop_flag SMALLINT NOT NULL DEFAULT 0,
  condition_id BIGINT NOT NULL,
  fold_type_id INT NOT NULL,
  fold_type_name VARCHAR(100) DEFAULT NULL,
  sim_type_id INT NOT NULL,
  sim_type_name VARCHAR(100) DEFAULT NULL,
  algorithm_type VARCHAR(32) DEFAULT NULL,
  round_total INT DEFAULT 0,
  output_count INT DEFAULT 0,
  solver_id VARCHAR(64) DEFAULT NULL,
  care_device_ids JSON DEFAULT NULL,
  remark TEXT,
  running_module VARCHAR(64) DEFAULT NULL,
  process DECIMAL(5,2) DEFAULT 0,
  status SMALLINT DEFAULT 0,
  statistics_json JSON DEFAULT NULL,
  result_summary_json JSON DEFAULT NULL,
  condition_snapshot JSON NOT NULL,
  subject_config JSON DEFAULT NULL,
  external_meta JSON DEFAULT NULL,
  created_at INT DEFAULT NULL,
  updated_at INT DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cco_order_condition (order_id, condition_id),
  UNIQUE KEY uk_cco_opt_condition_config_id (opt_condition_config_id),
  KEY idx_cco_order_id (order_id),
  KEY idx_cco_order_case_id (order_case_id),
  KEY idx_cco_opt_issue_id (opt_issue_id),
  KEY idx_cco_opt_job_id (opt_job_id),
  KEY idx_cco_order_status (order_id, status),
  KEY idx_cco_order_case (order_id, order_case_id),
  KEY idx_cco_order_simtype (order_id, sim_type_id),
  KEY idx_cco_order_foldtype (order_id, fold_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='case下的平台工况与外部condition_config映射表'
"""


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _columns(inspector, table_name: str) -> set[str]:
    return {item['name'] for item in inspector.get_columns(table_name)}


def _indexes(inspector, table_name: str) -> set[str]:
    return {item['name'] for item in inspector.get_indexes(table_name)}


def _unique_constraints(inspector, table_name: str) -> set[str]:
    return {item['name'] for item in inspector.get_unique_constraints(table_name) if item.get('name')}


def _execute_many(conn, statements: Iterable[str]) -> None:
    for statement in statements:
        conn.execute(text(statement))


def _ensure_columns(conn, inspector, table_name: str, ddl_by_column: dict[str, str]) -> None:
    existing = _columns(inspector, table_name)
    for column_name, ddl in ddl_by_column.items():
        if column_name not in existing:
            conn.execute(text(ddl))


def _ensure_indexes(conn, inspector) -> None:
    case_indexes = _indexes(inspector, 'order_case_opti') | _unique_constraints(inspector, 'order_case_opti')
    condition_indexes = _indexes(inspector, 'case_condition_opti') | _unique_constraints(inspector, 'case_condition_opti')
    if 'uk_order_case_index' not in case_indexes:
        conn.execute(text('ALTER TABLE order_case_opti ADD CONSTRAINT uk_order_case_index UNIQUE (order_id, case_index)'))
    if 'uk_order_case_opt_job_id' not in case_indexes:
        conn.execute(text('ALTER TABLE order_case_opti ADD CONSTRAINT uk_order_case_opt_job_id UNIQUE (opt_job_id)'))
    if 'idx_order_case_status' not in case_indexes:
        conn.execute(text('CREATE INDEX idx_order_case_status ON order_case_opti(order_id, status)'))
    if 'uk_cco_order_condition' not in condition_indexes:
        conn.execute(text('ALTER TABLE case_condition_opti ADD CONSTRAINT uk_cco_order_condition UNIQUE (order_id, condition_id)'))
    if 'uk_cco_opt_condition_config_id' not in condition_indexes:
        conn.execute(text('ALTER TABLE case_condition_opti ADD CONSTRAINT uk_cco_opt_condition_config_id UNIQUE (opt_condition_config_id)'))
    if 'idx_cco_order_case' not in condition_indexes:
        conn.execute(text('CREATE INDEX idx_cco_order_case ON case_condition_opti(order_id, order_case_id)'))


def upgrade_case_opti_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)
    with engine.begin() as conn:
        inspector = inspect(conn)
        if not _table_exists(inspector, 'order_case_opti'):
            conn.execute(text(ORDER_CASE_TABLE_SQL))
            if verbose:
                print('[case-opti-upgrade] created order_case_opti')
        if not _table_exists(inspector, 'case_condition_opti'):
            conn.execute(text(CASE_CONDITION_TABLE_SQL))
            if verbose:
                print('[case-opti-upgrade] created case_condition_opti')

        inspector = inspect(conn)
        _ensure_columns(
            conn,
            inspector,
            'order_case_opti',
            {
                'parameter_scope': "ALTER TABLE order_case_opti ADD COLUMN parameter_scope VARCHAR(32) NOT NULL DEFAULT 'per_condition'",
                'case_snapshot': 'ALTER TABLE order_case_opti ADD COLUMN case_snapshot JSON DEFAULT NULL',
                'external_meta': 'ALTER TABLE order_case_opti ADD COLUMN external_meta JSON DEFAULT NULL',
            },
        )
        inspector = inspect(conn)
        _ensure_columns(
            conn,
            inspector,
            'case_condition_opti',
            {
                'opt_condition_config_id': 'ALTER TABLE case_condition_opti ADD COLUMN opt_condition_config_id INT DEFAULT NULL',
                'parameter_scope': "ALTER TABLE case_condition_opti ADD COLUMN parameter_scope VARCHAR(32) NOT NULL DEFAULT 'per_condition'",
                'rotate_drop_flag': 'ALTER TABLE case_condition_opti ADD COLUMN rotate_drop_flag SMALLINT NOT NULL DEFAULT 0',
                'subject_config': 'ALTER TABLE case_condition_opti ADD COLUMN subject_config JSON DEFAULT NULL',
            },
        )
        inspector = inspect(conn)
        _ensure_indexes(conn, inspector)


def main() -> int:
    parser = argparse.ArgumentParser(description='Upgrade order case/condition opti schema')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), help='Database URL')
    args = parser.parse_args()
    if not args.db_url:
        raise SystemExit('缺少 --db-url 或 DATABASE_URL')
    upgrade_case_opti_schema(args.db_url, verbose=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
