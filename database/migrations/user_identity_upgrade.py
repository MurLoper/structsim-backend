"""
用户身份标识升级：以 domain_account 作为业务唯一标识，兼容 lc_user_id。

能力：
1) users 表增加/修正字段：domain_account、lc_user_id、user_name、real_name
2) orders.created_by 调整为 VARCHAR(32)
3) upload_files.user_id 调整为 VARCHAR(32)，并移除指向 users.id 的外键
4) 自动回填 users.domain_account/user_name/real_name
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_names(inspector, table_name: str) -> set[str]:
    return {col.get('name') for col in inspector.get_columns(table_name)}


def _index_names(inspector, table_name: str) -> set[str]:
    try:
        return {idx.get('name') for idx in inspector.get_indexes(table_name) if idx.get('name')}
    except Exception:
        return set()


def upgrade_identity_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)
    inspector = inspect(engine)

    if verbose:
        print(f"[identity-upgrade] start: {db_url}")

    with engine.connect() as conn:
        # users
        if _table_exists(inspector, 'users'):
            user_cols = _column_names(inspector, 'users')

            if 'domain_account' not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN domain_account VARCHAR(32) NULL COMMENT '域账号'"))
            if 'lc_user_id' not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN lc_user_id VARCHAR(64) NULL COMMENT '部门平台用户ID'"))
            if 'user_name' not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN user_name VARCHAR(100) NULL COMMENT '用户展示名'"))
            if 'real_name' not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN real_name VARCHAR(100) NULL COMMENT '真实姓名'"))

            # 回填数据
            conn.execute(text("""
                UPDATE users
                SET domain_account = LOWER(TRIM(COALESCE(domain_account, username, '')))
                WHERE domain_account IS NULL OR TRIM(domain_account) = ''
            """))
            conn.execute(text("""
                UPDATE users
                SET user_name = COALESCE(NULLIF(TRIM(user_name), ''), NULLIF(TRIM(name), ''), domain_account, username)
                WHERE user_name IS NULL OR TRIM(user_name) = ''
            """))
            conn.execute(text("""
                UPDATE users
                SET real_name = COALESCE(NULLIF(TRIM(real_name), ''), NULLIF(TRIM(name), ''), user_name, domain_account, username)
                WHERE real_name IS NULL OR TRIM(real_name) = ''
            """))

            conn.execute(text("ALTER TABLE users MODIFY COLUMN domain_account VARCHAR(32) NOT NULL COMMENT '域账号'"))

            # 索引

            idx_names = _index_names(inspector, 'users')
            if 'uq_users_domain_account' not in idx_names:
                conn.execute(text("CREATE UNIQUE INDEX uq_users_domain_account ON users(domain_account)"))
            if 'uq_users_lc_user_id' not in idx_names:
                conn.execute(text("CREATE UNIQUE INDEX uq_users_lc_user_id ON users(lc_user_id)"))

        # orders.created_by -> varchar
        if _table_exists(inspector, 'orders'):
            order_cols = _column_names(inspector, 'orders')
            if 'created_by' in order_cols:
                conn.execute(text("ALTER TABLE orders MODIFY COLUMN created_by VARCHAR(32) NULL COMMENT '创建人域账号'"))

        # upload_files.user_id -> varchar，并移除外键
        if _table_exists(inspector, 'upload_files'):
            upload_cols = _column_names(inspector, 'upload_files')
            if 'user_id' in upload_cols:
                fks = inspector.get_foreign_keys('upload_files')
                for fk in fks:
                    constrained = fk.get('constrained_columns') or []
                    fk_name = fk.get('name')
                    if fk_name and 'user_id' in constrained:
                        conn.execute(text(f"ALTER TABLE upload_files DROP FOREIGN KEY `{fk_name}`"))

                conn.execute(text("ALTER TABLE upload_files MODIFY COLUMN user_id VARCHAR(32) NOT NULL COMMENT '上传用户标识(域账号)'"))
                idx_names = _index_names(inspector, 'upload_files')
                if 'idx_upload_files_user_id' not in idx_names:
                    conn.execute(text("CREATE INDEX idx_upload_files_user_id ON upload_files(user_id)"))

        conn.commit()

    if verbose:
        print("[identity-upgrade] done")


if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser(description='升级用户身份字段与关联表结构')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), help='数据库连接 URL')
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit('错误: 缺少 --db-url 或 DATABASE_URL')

    upgrade_identity_schema(args.db_url, verbose=True)
