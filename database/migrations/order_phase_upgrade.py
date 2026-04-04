"""
orders.phase_id 升级脚本。
只增加字段与索引，不添加外键。
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


def upgrade_order_phase_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)
    if verbose:
        print(f'[order-phase-upgrade] start: {db_url}')

    with engine.connect() as conn:
        inspector = inspect(engine)
        if not _table_exists(inspector, 'orders'):
            if verbose:
                print('[order-phase-upgrade] skip: orders table not found')
            return

        columns = _column_names(inspector, 'orders')
        if 'phase_id' not in columns:
            conn.execute(
                text("ALTER TABLE orders ADD COLUMN phase_id INT NULL COMMENT '项目阶段ID'")
            )

        inspector = inspect(engine)
        indexes = _index_names(inspector, 'orders')
        if 'idx_orders_phase_id' not in indexes:
            conn.execute(text('CREATE INDEX idx_orders_phase_id ON orders(phase_id)'))

        conn.commit()

    if verbose:
        print('[order-phase-upgrade] done')


if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser(description='升级 orders.phase_id 字段')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), help='数据库连接 URL')
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit('错误: 缺少 --db-url 或 DATABASE_URL')

    upgrade_order_phase_schema(args.db_url, verbose=True)
