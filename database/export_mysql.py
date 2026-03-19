"""
导出 MySQL 数据库为可重放 SQL，并可一键同步到目标数据库。

用法示例:
  python database/export_mysql.py
  python database/export_mysql.py --source-db-url mysql+pymysql://user:pass@host:3306/db
  python database/export_mysql.py --sync-db-url mysql+pymysql://user:pass@target:3306/db
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

from sqlalchemy import MetaData, create_engine, text


sys.path.insert(0, str(Path(__file__).parent.parent))

EXPORT_DIR = Path(__file__).parent / 'export'


def escape_mysql_string(value: str) -> str:
    return (
        value.replace('\\', '\\\\')
        .replace("'", "\\'")
        .replace('\0', '\\0')
        .replace('\n', '\\n')
        .replace('\r', '\\r')
        .replace('\x1a', '\\Z')
    )


def to_sql_literal(value) -> str:
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return f"'{escape_mysql_string(value.isoformat(sep=' '))}'"
    if isinstance(value, (dict, list)):
        return f"'{escape_mysql_string(json.dumps(value, ensure_ascii=False))}'"
    if isinstance(value, bytes):
        return f"X'{value.hex()}'"
    return f"'{escape_mysql_string(str(value))}'"


def parse_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(',') if item.strip()}


def collect_tables(metadata: MetaData, include: set[str], exclude: set[str]) -> List[str]:
    names = list(metadata.tables.keys())
    if include:
        names = [name for name in names if name in include]
    if exclude:
        names = [name for name in names if name not in exclude]
    return sorted(names)


def export_database(
    source_db_url: str,
    output_file: Path,
    include_tables: set[str] | None = None,
    exclude_tables: set[str] | None = None,
    chunk_size: int = 500,
) -> Path:
    include_tables = include_tables or set()
    exclude_tables = exclude_tables or set()

    engine = create_engine(source_db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    tables = collect_tables(metadata, include_tables, exclude_tables)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='\n') as f, engine.connect() as conn:
        f.write('-- StructSim DB Export\n')
        f.write(f'-- ExportedAt: {datetime.now().isoformat()}\n')
        f.write(f'-- TableCount: {len(tables)}\n\n')
        f.write('SET NAMES utf8mb4;\n')
        f.write('SET FOREIGN_KEY_CHECKS=0;\n\n')

        for table_name in tables:
            print(f'导出表: {table_name}')
            create_sql_row = conn.execute(text(f"SHOW CREATE TABLE `{table_name}`")).fetchone()
            if not create_sql_row:
                continue
            create_sql = create_sql_row[1]

            f.write(f'-- Table: {table_name}\n')
            f.write(f'DROP TABLE IF EXISTS `{table_name}`;\n')
            f.write(f'{create_sql};\n\n')

            rows = conn.execute(text(f"SELECT * FROM `{table_name}`")).fetchall()
            if not rows:
                continue

            columns = list(metadata.tables[table_name].columns.keys())
            col_sql = ', '.join(f'`{c}`' for c in columns)

            f.write(f'-- Data: {table_name}\n')
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                values_sql = []
                for row in chunk:
                    values_sql.append(
                        '(' + ', '.join(to_sql_literal(v) for v in row) + ')'
                    )
                f.write(f"INSERT INTO `{table_name}` ({col_sql}) VALUES\n")
                f.write(',\n'.join(values_sql))
                f.write(';\n')
            f.write('\n')

        f.write('SET FOREIGN_KEY_CHECKS=1;\n')

    return output_file


def build_output_file(path_arg: str | None) -> Path:
    if path_arg:
        p = Path(path_arg)
        return p if p.is_absolute() else (Path.cwd() / p)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return EXPORT_DIR / f'database_export_{ts}.sql'


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description='导出 MySQL 数据库到 SQL 文件')
    parser.add_argument('--source-db-url', default=os.getenv('DATABASE_URL'), help='源数据库连接 URL，默认读取 DATABASE_URL')
    parser.add_argument('--output-file', default=None, help='输出 SQL 文件路径')
    parser.add_argument('--only-tables', default=None, help='仅导出指定表，逗号分隔')
    parser.add_argument('--exclude-tables', default=None, help='排除指定表，逗号分隔')
    parser.add_argument('--chunk-size', type=int, default=500, help='INSERT 批量大小')
    parser.add_argument('--sync-db-url', default=None, help='导出完成后直接导入到目标数据库')
    args = parser.parse_args()

    if not args.source_db_url:
        print('错误: 未提供源数据库 URL，请设置 DATABASE_URL 或传 --source-db-url')
        return 1

    output_file = build_output_file(args.output_file)
    include_tables = parse_csv(args.only_tables)
    exclude_tables = parse_csv(args.exclude_tables)

    print('=' * 60)
    print('导出数据库')
    print('=' * 60)
    print(f'源库: {args.source_db_url}')
    print(f'输出: {output_file}')

    exported = export_database(
        source_db_url=args.source_db_url,
        output_file=output_file,
        include_tables=include_tables,
        exclude_tables=exclude_tables,
        chunk_size=max(1, args.chunk_size),
    )

    print(f'\n导出完成: {exported}')

    if args.sync_db_url:
        from import_mysql import import_database

        print('\n开始一键同步到目标库...')
        ok = import_database(sql_file=str(exported), db_url=args.sync_db_url, stop_on_error=True)
        return 0 if ok else 2

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
