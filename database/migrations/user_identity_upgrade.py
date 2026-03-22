"""
用户身份标识升级：
1. 以 domain_account 作为业务唯一标识
2. 保留自增 id 作为内部代理键
3. 清理 users.username / users.name 历史字段
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


def _build_domain_account_expr(user_cols: set[str]) -> str:
    candidates = ["domain_account"]
    if "username" in user_cols:
        candidates.append("username")
    candidates.append("''")
    return f"LOWER(TRIM(COALESCE({', '.join(candidates)})))"


def _build_user_name_expr(user_cols: set[str]) -> str:
    candidates = ["NULLIF(TRIM(user_name), '')"]
    if "name" in user_cols:
        candidates.append("NULLIF(TRIM(name), '')")
    candidates.append("domain_account")
    if "username" in user_cols:
        candidates.append("username")
    return f"COALESCE({', '.join(candidates)})"


def _build_real_name_expr(user_cols: set[str]) -> str:
    candidates = ["NULLIF(TRIM(real_name), '')"]
    if "name" in user_cols:
        candidates.append("NULLIF(TRIM(name), '')")
    candidates.extend(["user_name", "domain_account"])
    if "username" in user_cols:
        candidates.append("username")
    return f"COALESCE({', '.join(candidates)})"


def upgrade_identity_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)

    if verbose:
        print(f"[identity-upgrade] start: {db_url}")

    with engine.connect() as conn:
        inspector = inspect(conn)

        if _table_exists(inspector, "users"):
            user_cols = _column_names(inspector, "users")

            if "domain_account" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN domain_account VARCHAR(32) NULL COMMENT '域账号'")
                )
            if "lc_user_id" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN lc_user_id VARCHAR(64) NULL COMMENT '外部平台用户ID'")
                )
            if "user_name" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN user_name VARCHAR(100) NULL COMMENT '用户展示名'")
                )
            if "real_name" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN real_name VARCHAR(100) NULL COMMENT '真实姓名'")
                )
            if "daily_round_limit" not in user_cols:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN daily_round_limit INT NULL DEFAULT NULL COMMENT '用户日提单轮次上限，覆盖值'"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE users MODIFY COLUMN daily_round_limit INT NULL DEFAULT NULL COMMENT '用户日提单轮次上限，覆盖值'"
                    )
                )

            inspector = inspect(conn)
            user_cols = _column_names(inspector, "users")

            conn.execute(
                text(
                    f"""
                    UPDATE users
                    SET domain_account = {_build_domain_account_expr(user_cols)}
                    WHERE domain_account IS NULL OR TRIM(domain_account) = ''
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    UPDATE users
                    SET user_name = {_build_user_name_expr(user_cols)}
                    WHERE user_name IS NULL OR TRIM(user_name) = ''
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    UPDATE users
                    SET real_name = {_build_real_name_expr(user_cols)}
                    WHERE real_name IS NULL OR TRIM(real_name) = ''
                    """
                )
            )

            conn.execute(
                text("ALTER TABLE users MODIFY COLUMN domain_account VARCHAR(32) NOT NULL COMMENT '域账号'")
            )

            inspector = inspect(conn)
            idx_names = _index_names(inspector, "users")
            if "uq_users_domain_account" not in idx_names:
                conn.execute(text("CREATE UNIQUE INDEX uq_users_domain_account ON users(domain_account)"))
            if "uq_users_lc_user_id" not in idx_names:
                conn.execute(text("CREATE UNIQUE INDEX uq_users_lc_user_id ON users(lc_user_id)"))

            user_cols = _column_names(inspector, "users")
            if "username" in user_cols:
                if "username" in idx_names:
                    conn.execute(text("DROP INDEX `username` ON users"))
                conn.execute(text("ALTER TABLE users DROP COLUMN username"))
            if "name" in user_cols:
                conn.execute(text("ALTER TABLE users DROP COLUMN name"))

        if _table_exists(inspector, "roles"):
            role_cols = _column_names(inspector, "roles")
            if "max_cpu_cores" not in role_cols:
                conn.execute(
                    text("ALTER TABLE roles ADD COLUMN max_cpu_cores INT NOT NULL DEFAULT 192 COMMENT '可用CPU核数上限'")
                )
            if "max_batch_size" not in role_cols:
                conn.execute(
                    text("ALTER TABLE roles ADD COLUMN max_batch_size INT NOT NULL DEFAULT 200 COMMENT '单次提单轮次上限'")
                )
            if "node_list" not in role_cols:
                conn.execute(
                    text("ALTER TABLE roles ADD COLUMN node_list JSON NULL COMMENT '可用计算节点ID列表'")
                )
            if "daily_round_limit_default" not in role_cols:
                conn.execute(
                    text("ALTER TABLE roles ADD COLUMN daily_round_limit_default INT NOT NULL DEFAULT 500 COMMENT '角色默认日提单轮次上限'")
                )

        if _table_exists(inspector, "orders"):
            order_cols = _column_names(inspector, "orders")
            if "created_by" in order_cols:
                conn.execute(
                    text("ALTER TABLE orders MODIFY COLUMN created_by VARCHAR(32) NULL COMMENT '创建人域账号'")
                )

        if _table_exists(inspector, "upload_files"):
            upload_cols = _column_names(inspector, "upload_files")
            if "user_id" in upload_cols:
                fks = inspector.get_foreign_keys("upload_files")
                for fk in fks:
                    constrained = fk.get("constrained_columns") or []
                    fk_name = fk.get("name")
                    if fk_name and "user_id" in constrained:
                        conn.execute(text(f"ALTER TABLE upload_files DROP FOREIGN KEY `{fk_name}`"))

                conn.execute(
                    text("ALTER TABLE upload_files MODIFY COLUMN user_id VARCHAR(32) NOT NULL COMMENT '上传用户标识(域账号)'")
                )
                idx_names = _index_names(inspector, "upload_files")
                if "idx_upload_files_user_id" not in idx_names:
                    conn.execute(text("CREATE INDEX idx_upload_files_user_id ON upload_files(user_id)"))

        conn.commit()

    if verbose:
        print("[identity-upgrade] done")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="升级用户身份字段与关联表结构")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="数据库连接 URL")
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit("错误: 缺少 --db-url 或 DATABASE_URL")

    upgrade_identity_schema(args.db_url, verbose=True)
