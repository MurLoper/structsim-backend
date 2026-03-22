"""
订单 condition 运行实体升级：

1) orders 表补充 opt_issue_id、condition_summary
2) 新建或补齐 order_condition_opti 表

用于把订单快照拆分成 condition 级运行实体，兼容旧库平滑升级。
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_names(inspector, table_name: str) -> set[str]:
    return {col.get("name") for col in inspector.get_columns(table_name)}


def _index_names(inspector, table_name: str) -> set[str]:
    try:
        return {idx.get("name") for idx in inspector.get_indexes(table_name) if idx.get("name")}
    except Exception:
        return set()


def _unique_constraint_names(inspector, table_name: str) -> set[str]:
    try:
        return {
            item.get("name")
            for item in inspector.get_unique_constraints(table_name)
            if item.get("name")
        }
    except Exception:
        return set()


ORDER_CONDITION_OPTI_CREATE_SQL = """
CREATE TABLE order_condition_opti (
  id BIGINT NOT NULL AUTO_INCREMENT,
  order_id BIGINT NOT NULL COMMENT '主单ID',
  order_no VARCHAR(50) DEFAULT NULL COMMENT '主单编号冗余',
  opt_issue_id INT NOT NULL COMMENT '自动优化申请单ID',
  opt_job_id INT DEFAULT NULL COMMENT '自动化方案作业ID',
  condition_id BIGINT NOT NULL COMMENT 'condition标识',
  fold_type_id INT NOT NULL COMMENT '姿态ID',
  fold_type_name VARCHAR(100) DEFAULT NULL COMMENT '姿态名称快照',
  sim_type_id INT NOT NULL COMMENT '仿真类型ID',
  sim_type_name VARCHAR(100) DEFAULT NULL COMMENT '仿真类型名称快照',
  algorithm_type VARCHAR(32) DEFAULT NULL COMMENT '算法类型',
  round_total INT DEFAULT 0 COMMENT '轮次数量概览',
  output_count INT DEFAULT 0 COMMENT '输出数量概览',
  solver_id VARCHAR(64) DEFAULT NULL COMMENT '求解器标识，包含类型和版本语义',
  care_device_ids JSON DEFAULT NULL COMMENT '关注器件ID列表',
  remark TEXT COMMENT 'condition级备注',
  running_module VARCHAR(64) DEFAULT NULL COMMENT '当前运行模块',
  process DECIMAL(5,2) DEFAULT 0 COMMENT '进度百分比',
  status SMALLINT DEFAULT 0 COMMENT '状态',
  statistics_json JSON DEFAULT NULL COMMENT '统计摘要',
  result_summary_json JSON DEFAULT NULL COMMENT '结果摘要',
  condition_snapshot JSON NOT NULL COMMENT '完整condition快照',
  external_meta JSON DEFAULT NULL COMMENT '外部扩展信息',
  created_at INT DEFAULT NULL,
  updated_at INT DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_oco_order_condition (order_id, condition_id),
  UNIQUE KEY uk_oco_opt_job_id (opt_job_id),
  KEY idx_oco_opt_issue_id (opt_issue_id),
  KEY idx_oco_order_status (order_id, status),
  KEY idx_oco_order_simtype (order_id, sim_type_id),
  KEY idx_oco_order_foldtype (order_id, fold_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='订单condition优化运行实体表'
"""


def upgrade_order_condition_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)

    if verbose:
        print(f"[order-condition-upgrade] start: {db_url}")

    with engine.connect() as conn:
        inspector = inspect(engine)

        if _table_exists(inspector, "orders"):
            order_cols = _column_names(inspector, "orders")
            if "opt_issue_id" not in order_cols:
                conn.execute(
                    text("ALTER TABLE orders ADD COLUMN opt_issue_id INT NULL COMMENT '自动优化申请单ID'")
                )
            if "condition_summary" not in order_cols:
                conn.execute(
                    text(
                        "ALTER TABLE orders ADD COLUMN condition_summary JSON NULL COMMENT '工况概览 {姿态名: [仿真类型名,...]}'"
                    )
                )

            inspector = inspect(engine)
            order_indexes = _index_names(inspector, "orders")
            if "idx_orders_opt_issue_id" not in order_indexes:
                conn.execute(text("CREATE INDEX idx_orders_opt_issue_id ON orders(opt_issue_id)"))

        inspector = inspect(engine)
        if not _table_exists(inspector, "order_condition_opti"):
            conn.execute(text(ORDER_CONDITION_OPTI_CREATE_SQL))
            conn.commit()
            if verbose:
                print("[order-condition-upgrade] created order_condition_opti")
            inspector = inspect(engine)

        if _table_exists(inspector, "order_condition_opti"):
            columns = _column_names(inspector, "order_condition_opti")

            column_definitions = {
                "order_id": "ALTER TABLE order_condition_opti ADD COLUMN order_id BIGINT NOT NULL DEFAULT 0 COMMENT '主单ID'",
                "order_no": "ALTER TABLE order_condition_opti ADD COLUMN order_no VARCHAR(50) DEFAULT NULL COMMENT '主单编号冗余'",
                "opt_issue_id": "ALTER TABLE order_condition_opti ADD COLUMN opt_issue_id INT NOT NULL DEFAULT 0 COMMENT '自动优化申请单ID'",
                "opt_job_id": "ALTER TABLE order_condition_opti ADD COLUMN opt_job_id INT DEFAULT NULL COMMENT '自动化方案作业ID'",
                "condition_id": "ALTER TABLE order_condition_opti ADD COLUMN condition_id BIGINT NOT NULL DEFAULT 0 COMMENT 'condition标识'",
                "fold_type_id": "ALTER TABLE order_condition_opti ADD COLUMN fold_type_id INT NOT NULL DEFAULT 0 COMMENT '姿态ID'",
                "fold_type_name": "ALTER TABLE order_condition_opti ADD COLUMN fold_type_name VARCHAR(100) DEFAULT NULL COMMENT '姿态名称快照'",
                "sim_type_id": "ALTER TABLE order_condition_opti ADD COLUMN sim_type_id INT NOT NULL DEFAULT 0 COMMENT '仿真类型ID'",
                "sim_type_name": "ALTER TABLE order_condition_opti ADD COLUMN sim_type_name VARCHAR(100) DEFAULT NULL COMMENT '仿真类型名称快照'",
                "algorithm_type": "ALTER TABLE order_condition_opti ADD COLUMN algorithm_type VARCHAR(32) DEFAULT NULL COMMENT '算法类型'",
                "round_total": "ALTER TABLE order_condition_opti ADD COLUMN round_total INT DEFAULT 0 COMMENT '轮次数量概览'",
                "output_count": "ALTER TABLE order_condition_opti ADD COLUMN output_count INT DEFAULT 0 COMMENT '输出数量概览'",
                "solver_id": "ALTER TABLE order_condition_opti ADD COLUMN solver_id VARCHAR(64) DEFAULT NULL COMMENT '求解器标识，包含类型和版本语义'",
                "care_device_ids": "ALTER TABLE order_condition_opti ADD COLUMN care_device_ids JSON DEFAULT NULL COMMENT '关注器件ID列表'",
                "remark": "ALTER TABLE order_condition_opti ADD COLUMN remark TEXT COMMENT 'condition级备注'",
                "running_module": "ALTER TABLE order_condition_opti ADD COLUMN running_module VARCHAR(64) DEFAULT NULL COMMENT '当前运行模块'",
                "process": "ALTER TABLE order_condition_opti ADD COLUMN process DECIMAL(5,2) DEFAULT 0 COMMENT '进度百分比'",
                "status": "ALTER TABLE order_condition_opti ADD COLUMN status SMALLINT DEFAULT 0 COMMENT '状态'",
                "statistics_json": "ALTER TABLE order_condition_opti ADD COLUMN statistics_json JSON DEFAULT NULL COMMENT '统计摘要'",
                "result_summary_json": "ALTER TABLE order_condition_opti ADD COLUMN result_summary_json JSON DEFAULT NULL COMMENT '结果摘要'",
                "condition_snapshot": "ALTER TABLE order_condition_opti ADD COLUMN condition_snapshot JSON NULL COMMENT '完整condition快照'",
                "external_meta": "ALTER TABLE order_condition_opti ADD COLUMN external_meta JSON DEFAULT NULL COMMENT '外部扩展信息'",
                "created_at": "ALTER TABLE order_condition_opti ADD COLUMN created_at INT DEFAULT NULL",
                "updated_at": "ALTER TABLE order_condition_opti ADD COLUMN updated_at INT DEFAULT NULL",
            }

            for column_name, ddl in column_definitions.items():
                if column_name not in columns:
                    conn.execute(text(ddl))

            inspector = inspect(engine)
            if "condition_snapshot" in _column_names(inspector, "order_condition_opti"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE order_condition_opti MODIFY COLUMN condition_snapshot JSON NOT NULL COMMENT '完整condition快照'"
                        )
                    )
                except Exception:
                    pass

            inspector = inspect(engine)
            index_names = _index_names(inspector, "order_condition_opti")
            unique_names = _unique_constraint_names(inspector, "order_condition_opti")
            if "uk_oco_order_condition" not in index_names and "uk_oco_order_condition" not in unique_names:
                conn.execute(
                    text(
                        "ALTER TABLE order_condition_opti ADD CONSTRAINT uk_oco_order_condition UNIQUE (order_id, condition_id)"
                    )
                )
            if "uk_oco_opt_job_id" not in index_names and "uk_oco_opt_job_id" not in unique_names:
                conn.execute(
                    text(
                        "ALTER TABLE order_condition_opti ADD CONSTRAINT uk_oco_opt_job_id UNIQUE (opt_job_id)"
                    )
                )
            if "idx_oco_opt_issue_id" not in index_names:
                conn.execute(text("CREATE INDEX idx_oco_opt_issue_id ON order_condition_opti(opt_issue_id)"))
            if "idx_oco_order_status" not in index_names:
                conn.execute(text("CREATE INDEX idx_oco_order_status ON order_condition_opti(order_id, status)"))
            if "idx_oco_order_simtype" not in index_names:
                conn.execute(text("CREATE INDEX idx_oco_order_simtype ON order_condition_opti(order_id, sim_type_id)"))
            if "idx_oco_order_foldtype" not in index_names:
                conn.execute(text("CREATE INDEX idx_oco_order_foldtype ON order_condition_opti(order_id, fold_type_id)"))

        conn.commit()

    if verbose:
        print("[order-condition-upgrade] done")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="升级订单 condition 运行实体相关表结构")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="数据库连接 URL")
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit("错误: 缺少 --db-url 或 DATABASE_URL")

    upgrade_order_condition_schema(args.db_url, verbose=True)
