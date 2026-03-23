"""
用户部门字段升级：
1. users.department_id 作为唯一持久化字段
2. 依据旧 users.department 中文名称 / 编码回填 departments.id
3. 清理旧 users.department 文本列
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


def _foreign_key_names(inspector, table_name: str) -> set[str]:
    try:
        return {fk.get("name") for fk in inspector.get_foreign_keys(table_name) if fk.get("name")}
    except Exception:
        return set()


def upgrade_user_department_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)

    if verbose:
        print(f"[user-department-upgrade] start: {db_url}")

    with engine.connect() as conn:
        inspector = inspect(conn)
        if not _table_exists(inspector, "users") or not _table_exists(inspector, "departments"):
            if verbose:
                print("[user-department-upgrade] skip: missing users/departments table")
            return

        user_cols = _column_names(inspector, "users")
        if "department_id" not in user_cols:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN department_id INT NULL COMMENT '部门ID'"
                )
            )

        inspector = inspect(conn)
        user_cols = _column_names(inspector, "users")

        if "department" in user_cols:
            conn.execute(
                text(
                    """
                    UPDATE users AS u
                    INNER JOIN departments AS d
                        ON TRIM(u.department) <> ''
                       AND (
                            d.name = TRIM(u.department)
                            OR d.code = TRIM(u.department)
                       )
                    SET u.department_id = d.id
                    WHERE u.department_id IS NULL
                    """
                )
            )

        inspector = inspect(conn)
        idx_names = _index_names(inspector, "users")
        if "idx_users_department_id" not in idx_names:
            conn.execute(text("CREATE INDEX idx_users_department_id ON users(department_id)"))

        fk_names = _foreign_key_names(inspector, "users")
        if "fk_users_department_id" not in fk_names:
            conn.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD CONSTRAINT fk_users_department_id
                    FOREIGN KEY (department_id) REFERENCES departments(id)
                    """
                )
            )

        inspector = inspect(conn)
        user_cols = _column_names(inspector, "users")
        if "department" in user_cols:
            conn.execute(text("ALTER TABLE users DROP COLUMN department"))

        conn.commit()

    if verbose:
        print("[user-department-upgrade] done")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="升级 users.department 到 users.department_id")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="数据库连接 URL")
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit("错误: 缺少 --db-url 或 DATABASE_URL")

    upgrade_user_department_schema(args.db_url, verbose=True)
