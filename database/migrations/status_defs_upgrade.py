"""
状态定义修正升级：统一状态ID语义，并允许使用 0 作为有效状态ID。

目标：
1) status_defs.id 改为非自增，避免导入脚本写入 0 时被自动转为 1
2) 统一状态编码与ID：
   0=NOT_STARTED, 1=RUNNING, 2=COMPLETED, 3=FAILED,
   4=DRAFT, 5=CANCELLED, 6=STARTING, 7=PARTIAL_COMPLETED
"""

from __future__ import annotations

import time
from sqlalchemy import create_engine, inspect, text


TARGET_STATUS_DEFS = [
    {'id': 0, 'name': '未开始', 'code': 'NOT_STARTED', 'type': 'PROCESS', 'color_tag': '#6b7280', 'icon': 'Clock', 'sort': 0},
    {'id': 1, 'name': '运行中', 'code': 'RUNNING', 'type': 'PROCESS', 'color_tag': '#f59e0b', 'icon': 'Hourglass', 'sort': 10},
    {'id': 2, 'name': '已完成', 'code': 'COMPLETED', 'type': 'FINAL', 'color_tag': '#4ec110', 'icon': 'CheckCircle', 'sort': 20},
    {'id': 3, 'name': '运行失败', 'code': 'FAILED', 'type': 'FINAL', 'color_tag': '#FF0000', 'icon': 'XCircle', 'sort': 30},
    {'id': 4, 'name': '草稿箱', 'code': 'DRAFT', 'type': 'PROCESS', 'color_tag': '#8798b0', 'icon': 'RotateCcw', 'sort': 40},
    {'id': 5, 'name': '手动终止', 'code': 'CANCELLED', 'type': 'FINAL', 'color_tag': '#595040', 'icon': 'Ban', 'sort': 50},
    {'id': 6, 'name': '启动中', 'code': 'STARTING', 'type': 'PROCESS', 'color_tag': '#edaf02', 'icon': 'Timer', 'sort': 60},
    {'id': 7, 'name': '小模块完成', 'code': 'PARTIAL_COMPLETED', 'type': 'PROCESS', 'color_tag': '#84cc16', 'icon': 'CircleCheck', 'sort': 70},
]


def upgrade_status_defs_schema(db_url: str, verbose: bool = True) -> None:
    engine = create_engine(db_url)
    inspector = inspect(engine)

    if 'status_defs' not in set(inspector.get_table_names()):
        if verbose:
            print('[status-defs-upgrade] status_defs 表不存在，跳过')
        return

    if verbose:
        print(f'[status-defs-upgrade] start: {db_url}')

    now_ts = int(time.time())
    target_ids = {item['id'] for item in TARGET_STATUS_DEFS}
    target_codes = {item['code'] for item in TARGET_STATUS_DEFS}

    with engine.connect() as conn:
        # 关键：移除 AUTO_INCREMENT，允许显式写入 id=0
        conn.execute(text("ALTER TABLE status_defs MODIFY COLUMN id INT NOT NULL COMMENT '状态ID'"))
        column_names = {
            str(column.get('name'))
            for column in inspect(engine).get_columns('status_defs')
            if column.get('name')
        }
        if 'color_tag' not in column_names and 'color' in column_names:
            conn.execute(
                text(
                    "ALTER TABLE status_defs CHANGE COLUMN color color_tag VARCHAR(100) NULL COMMENT '颜色样式'"
                )
            )
            column_names = {
                str(column.get('name'))
                for column in inspect(engine).get_columns('status_defs')
                if column.get('name')
            }
        if 'color_tag' not in column_names:
            conn.execute(
                text(
                    "ALTER TABLE status_defs ADD COLUMN color_tag VARCHAR(100) NULL COMMENT '颜色样式'"
                )
            )

        rows = conn.execute(text('SELECT id, code FROM status_defs')).fetchall()
        temp_seed = -1000

        # 先把占用目标ID但不在目标code集合中的记录移走，避免主键冲突
        for row in rows:
            row_id = int(row[0]) if row[0] is not None else None
            row_code = str(row[1]) if row[1] is not None else ''
            if row_id is not None and row_id in target_ids and row_code not in target_codes:
                conn.execute(
                    text('UPDATE status_defs SET id = :temp_id WHERE id = :origin_id'),
                    {'temp_id': temp_seed, 'origin_id': row_id},
                )
                temp_seed -= 1

        # 再把目标code的记录都临时移走，避免改回目标id时冲突
        rows = conn.execute(text('SELECT id, code FROM status_defs')).fetchall()
        for row in rows:
            row_id = int(row[0]) if row[0] is not None else None
            row_code = str(row[1]) if row[1] is not None else ''
            if row_code in target_codes and row_id is not None and row_id not in target_ids:
                conn.execute(
                    text('UPDATE status_defs SET id = :temp_id WHERE code = :code'),
                    {'temp_id': temp_seed, 'code': row_code},
                )
                temp_seed -= 1

        # 按目标定义回填（存在则更新，不存在则插入）
        for item in TARGET_STATUS_DEFS:
            exists = conn.execute(
                text('SELECT COUNT(1) FROM status_defs WHERE code = :code'),
                {'code': item['code']},
            ).scalar() or 0

            if int(exists) > 0:
                update_sql = """
                        UPDATE status_defs
                        SET id = :id,
                            name = :name,
                            type = :type,
                            color_tag = :color_tag,
                            icon = :icon,
                            valid = 1,
                            sort = :sort,
                            updated_at = :updated_at
                        WHERE code = :code
                        """
                params = {
                    'id': item['id'],
                    'name': item['name'],
                    'type': item['type'],
                    'color_tag': item['color_tag'],
                    'icon': item['icon'],
                    'sort': item['sort'],
                    'updated_at': now_ts,
                    'code': item['code'],
                }
                conn.execute(text(update_sql), params)
            else:
                insert_cols = ['id', 'name', 'code', 'type', 'color_tag']
                insert_vals = [':id', ':name', ':code', ':type', ':color_tag']
                params = {
                    'id': item['id'],
                    'name': item['name'],
                    'code': item['code'],
                    'type': item['type'],
                    'color_tag': item['color_tag'],
                    'icon': item['icon'],
                    'sort': item['sort'],
                    'created_at': now_ts,
                    'updated_at': now_ts,
                }
                insert_cols.extend(['icon', 'valid', 'sort', 'created_at', 'updated_at'])
                insert_vals.extend([':icon', '1', ':sort', ':created_at', ':updated_at'])
                conn.execute(
                    text(
                        f"INSERT INTO status_defs ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})"
                    ),
                    params,
                )

        conn.commit()

    if verbose:
        print('[status-defs-upgrade] done')


if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser(description='修正 status_defs 状态ID语义并支持 id=0')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), help='数据库连接 URL')
    args = parser.parse_args()

    if not args.db_url:
        raise SystemExit('错误: 缺少 --db-url 或 DATABASE_URL')

    upgrade_status_defs_schema(args.db_url, verbose=True)
