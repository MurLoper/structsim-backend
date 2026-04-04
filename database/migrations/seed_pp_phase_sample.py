"""
为外部 simlation_project.pp_phase 生成一批示例关联数据。

规则：
1. 从本地主库读取 projects.id
2. 从外部 simlation_project.phase 读取可用 phase_id
3. 对尚未存在映射的 project_id 按稳定顺序轮询分配 phase_id

说明：
- 仅用于当前“简单表结构联调”阶段
- 不会覆盖外部库已有映射
- 依赖 .env / config.py 中的主库与外部库连接配置
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pymysql
from sqlalchemy import text

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app, db  # noqa: E402


def _connect_external(app):
    return pymysql.connect(
        host=app.config['EXTERNAL_MYSQL_HOST'],
        port=app.config['EXTERNAL_MYSQL_PORT'],
        user=app.config['EXTERNAL_MYSQL_USER'],
        password=app.config['EXTERNAL_MYSQL_PASSWORD'],
        charset=app.config['EXTERNAL_MYSQL_CHARSET'],
        connect_timeout=int(app.config['EXTERNAL_MYSQL_CONNECT_TIMEOUT']),
        read_timeout=int(app.config['EXTERNAL_MYSQL_READ_TIMEOUT']),
        write_timeout=int(app.config['EXTERNAL_MYSQL_WRITE_TIMEOUT']),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def seed_pp_phase_sample(dry_run: bool = False) -> dict[str, int]:
    app = create_app()
    with app.app_context():
        local_projects = db.session.execute(text('SELECT id FROM projects ORDER BY id ASC')).scalars().all()
        if not local_projects:
            return {'projectCount': 0, 'insertedCount': 0, 'skippedCount': 0}

        schema_name = app.config['EXTERNAL_MYSQL_SCHEMA_SIMLATION_PROJECT']
        conn = _connect_external(app)
        try:
            with conn.cursor() as cur:
                cur.execute(f'SELECT phase_id FROM {schema_name}.phase ORDER BY phase_id ASC')
                phase_ids = [int(row['phase_id']) for row in cur.fetchall() if row.get('phase_id') is not None]
                if not phase_ids:
                    raise RuntimeError(f'{schema_name}.phase 中没有可用的 phase_id')

                cur.execute(f'SELECT pp_record_id, phase_id FROM {schema_name}.pp_phase')
                existing_rows = cur.fetchall()
                existing_project_ids = {
                    int(row['pp_record_id'])
                    for row in existing_rows
                    if row.get('pp_record_id') is not None
                }

                min_project_id = min(local_projects)
                insert_rows: list[tuple[int, int]] = []
                for project_id in local_projects:
                    if int(project_id) in existing_project_ids:
                        continue
                    phase_id = phase_ids[(int(project_id) - int(min_project_id)) % len(phase_ids)]
                    insert_rows.append((int(project_id), int(phase_id)))

                if insert_rows and not dry_run:
                    cur.executemany(
                        (
                            f'INSERT INTO {schema_name}.pp_phase (pp_record_id, phase_id) '
                            'VALUES (%s, %s)'
                        ),
                        insert_rows,
                    )
                    conn.commit()
                elif dry_run:
                    conn.rollback()
                else:
                    conn.rollback()

                return {
                    'projectCount': len(local_projects),
                    'insertedCount': len(insert_rows),
                    'skippedCount': len(local_projects) - len(insert_rows),
                }
        finally:
            conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='为外部 simlation_project.pp_phase 生成示例关联数据')
    parser.add_argument('--dry-run', action='store_true', help='只预览，不实际写入')
    args = parser.parse_args()
    result = seed_pp_phase_sample(dry_run=args.dry_run)
    print(result)
