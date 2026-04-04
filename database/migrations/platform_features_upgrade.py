"""
平台公告、隐私协议与埋点相关表结构自动升级。
"""
from __future__ import annotations

from sqlalchemy import create_engine, inspect, text


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {item["name"] for item in inspector.get_columns(table_name)}


def _ensure_column(conn, inspector, table_name: str, column_name: str, ddl: str) -> None:
    if not _column_exists(inspector, table_name, column_name):
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {item["name"] for item in inspector.get_indexes(table_name)}


def _ensure_index(conn, inspector, table_name: str, index_name: str, columns: str) -> None:
    if not _index_exists(inspector, table_name, index_name):
        conn.execute(text(f"CREATE INDEX {index_name} ON {table_name} ({columns})"))


def upgrade_platform_features_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)

    if verbose:
        print(f"[platform-features-upgrade] start: {db_url}")

    with engine.connect() as conn:
        inspector = inspect(conn)

        if not _table_exists(inspector, "platform_settings"):
            conn.execute(
                text(
                    """
                    CREATE TABLE platform_settings (
                      `key` VARCHAR(64) NOT NULL PRIMARY KEY COMMENT '配置键',
                      value_json JSON NOT NULL COMMENT '配置值(JSON)',
                      description VARCHAR(255) NULL COMMENT '配置说明',
                      updated_by VARCHAR(32) NULL COMMENT '最后更新人域账号',
                      created_at BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
                      updated_at BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间'
                    ) COMMENT='平台设置'
                    """
                )
            )

        if not _table_exists(inspector, "announcements"):
            conn.execute(
                text(
                    """
                    CREATE TABLE announcements (
                      id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                      title VARCHAR(120) NOT NULL COMMENT '公告标题',
                      content TEXT NOT NULL COMMENT '公告正文',
                      level VARCHAR(16) NOT NULL DEFAULT 'info' COMMENT '公告级别',
                      is_active TINYINT NOT NULL DEFAULT 1 COMMENT '1=启用,0=停用',
                      dismissible TINYINT NOT NULL DEFAULT 1 COMMENT '1=可关闭,0=不可关闭',
                      sort INT NOT NULL DEFAULT 100 COMMENT '排序值',
                      start_at BIGINT NULL COMMENT '生效开始时间戳',
                      end_at BIGINT NULL COMMENT '生效结束时间戳',
                      link_text VARCHAR(60) NULL COMMENT '链接文案',
                      link_url VARCHAR(255) NULL COMMENT '链接地址',
                      created_by VARCHAR(32) NULL COMMENT '创建人域账号',
                      updated_by VARCHAR(32) NULL COMMENT '最后更新人域账号',
                      created_at BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
                      updated_at BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间',
                      KEY idx_announcements_active (is_active, sort, updated_at),
                      KEY idx_announcements_window (start_at, end_at)
                    ) COMMENT='公告表'
                    """
                )
            )

        if not _table_exists(inspector, "privacy_policy_acceptances"):
            conn.execute(
                text(
                    """
                    CREATE TABLE privacy_policy_acceptances (
                      id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                      domain_account VARCHAR(32) NOT NULL COMMENT '用户域账号',
                      policy_version VARCHAR(32) NOT NULL COMMENT '已同意版本',
                      accepted_at BIGINT NOT NULL DEFAULT 0 COMMENT '同意时间',
                      accepted_ip VARCHAR(64) NULL COMMENT '同意时IP',
                      created_at BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
                      updated_at BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间',
                      KEY idx_privacy_acceptance_user (domain_account, policy_version, accepted_at)
                    ) COMMENT='隐私协议同意记录'
                    """
                )
            )

        if not _table_exists(inspector, "tracking_events"):
            conn.execute(
                text(
                    """
                    CREATE TABLE tracking_events (
                      id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                      event_name VARCHAR(64) NOT NULL COMMENT '事件名',
                      event_type VARCHAR(32) NOT NULL COMMENT '事件类型',
                      page_path VARCHAR(255) NULL COMMENT '页面路径',
                      page_key VARCHAR(64) NULL COMMENT '页面唯一标识',
                      feature_key VARCHAR(64) NULL COMMENT '功能唯一标识',
                      module_key VARCHAR(64) NULL COMMENT '模块唯一标识',
                      result VARCHAR(32) NULL COMMENT '结果标识',
                      target VARCHAR(120) NULL COMMENT '事件目标',
                      session_id VARCHAR(64) NULL COMMENT '会话标识',
                      domain_account VARCHAR(32) NULL COMMENT '用户域账号',
                      metadata_json JSON NULL COMMENT '事件元数据',
                      duration_ms INT NULL COMMENT '耗时(毫秒)',
                      created_at BIGINT NOT NULL DEFAULT 0 COMMENT '事件时间',
                      KEY idx_tracking_events_name (event_name, created_at),
                      KEY idx_tracking_events_type (event_type, created_at),
                      KEY idx_tracking_events_page (page_path, created_at),
                      KEY idx_tracking_events_page_key (page_key, created_at),
                      KEY idx_tracking_events_feature_key (feature_key, created_at),
                      KEY idx_tracking_events_module_key (module_key, created_at),
                      KEY idx_tracking_events_result (result, created_at),
                      KEY idx_tracking_events_user (domain_account, created_at)
                    ) COMMENT='前端埋点事件'
                    """
                )
            )
        else:
            _ensure_column(
                conn,
                inspector,
                "tracking_events",
                "page_key",
                "page_key VARCHAR(64) NULL COMMENT '页面唯一标识' AFTER page_path",
            )
            _ensure_column(
                conn,
                inspector,
                "tracking_events",
                "feature_key",
                "feature_key VARCHAR(64) NULL COMMENT '功能唯一标识' AFTER page_key",
            )
            _ensure_column(
                conn,
                inspector,
                "tracking_events",
                "module_key",
                "module_key VARCHAR(64) NULL COMMENT '模块唯一标识' AFTER feature_key",
            )
            _ensure_column(
                conn,
                inspector,
                "tracking_events",
                "result",
                "result VARCHAR(32) NULL COMMENT '结果标识' AFTER module_key",
            )
            _ensure_column(
                conn,
                inspector,
                "tracking_events",
                "duration_ms",
                "duration_ms INT NULL COMMENT '耗时(毫秒)' AFTER metadata_json",
            )
            inspector = inspect(conn)
            _ensure_index(conn, inspector, "tracking_events", "idx_tracking_events_page_key", "page_key, created_at")
            _ensure_index(conn, inspector, "tracking_events", "idx_tracking_events_feature_key", "feature_key, created_at")
            _ensure_index(conn, inspector, "tracking_events", "idx_tracking_events_module_key", "module_key, created_at")
            _ensure_index(conn, inspector, "tracking_events", "idx_tracking_events_result", "`result`, created_at")

        conn.commit()

    if verbose:
        print("[platform-features-upgrade] done")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="升级平台功能相关表结构")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="数据库连接 URL")
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit("错误: 缺少 --db-url 或 DATABASE_URL")

    upgrade_platform_features_schema(args.db_url, verbose=True)
