"""
导出 MySQL 数据库为可重放 SQL，并可一键同步到目标数据库。

用法示例:
  python database/export_mysql.py
  python database/export_mysql.py --source-db-url mysql+pymysql://user:pass@host:3306/db
  python database/export_mysql.py --source-db-url mysql+pymysql://user:pass@host:3306/db --output-file database/export/full_latest.sql
"""

from __future__ import annotations

import argparse
import json
import os
import re
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

from sqlalchemy import MetaData, create_engine, text, inspect

try:
    from .migrations.user_identity_upgrade import upgrade_identity_schema
    from .migrations.order_condition_opti_upgrade import upgrade_order_condition_schema
    from .migrations.order_phase_upgrade import upgrade_order_phase_schema
except Exception:  # pragma: no cover
    from migrations.user_identity_upgrade import upgrade_identity_schema  # pyright: ignore[reportImplicitRelativeImport]
    from migrations.order_condition_opti_upgrade import upgrade_order_condition_schema  # pyright: ignore[reportImplicitRelativeImport]
    from migrations.order_phase_upgrade import upgrade_order_phase_schema  # pyright: ignore[reportImplicitRelativeImport]



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


def ensure_required_tables(engine, required_tables: Sequence[str]) -> None:
    if not required_tables:
        return

    existing = set(inspect(engine).get_table_names())
    missing = [name for name in required_tables if name not in existing]
    if missing:
        raise RuntimeError(f'源库缺少关键表: {", ".join(missing)}')


def strip_foreign_keys(create_sql: str) -> tuple[str, list[str]]:
    lines = create_sql.splitlines()
    fk_clauses: list[str] = []
    kept: list[str] = []

    for line in lines:
        if 'FOREIGN KEY' in line.upper():
            clause = line.strip().rstrip(',')
            fk_clauses.append(clause)
            continue
        kept.append(line)

    stripped_sql = '\n'.join(kept)
    stripped_sql = re.sub(r',\s*\n\)', '\n)', stripped_sql)
    return stripped_sql, fk_clauses


def build_fk_restore_sql(table_name: str, fk_clauses: Sequence[str]) -> list[str]:
    statements: list[str] = []
    for clause in fk_clauses:
        statements.append(f'ALTER TABLE `{table_name}` ADD {clause};')
    return statements


def export_database(
    source_db_url: str,
    output_file: Path,
    include_tables: set[str] | None = None,
    exclude_tables: set[str] | None = None,
    chunk_size: int = 500,
    strip_fk: bool = True,
    required_tables: Sequence[str] | None = None,
) -> Path:
    include_tables = include_tables or set()
    exclude_tables = exclude_tables or set()
    required_tables = tuple(required_tables or [])

    engine = create_engine(source_db_url)
    ensure_required_tables(engine, required_tables)

    metadata = MetaData()
    metadata.reflect(bind=engine)

    tables = collect_tables(metadata, include_tables, exclude_tables)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fk_restore_statements: list[str] = []

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
            if strip_fk:
                create_sql, fk_clauses = strip_foreign_keys(create_sql)
                fk_restore_statements.extend(build_fk_restore_sql(table_name, fk_clauses))

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

    if strip_fk:
        fk_file = output_file.with_name(f'{output_file.stem}_foreign_keys.sql')
        with open(fk_file, 'w', encoding='utf-8', newline='\n') as fk:
            fk.write('-- StructSim FK Restore SQL\n')
            fk.write(f'-- ExportedAt: {datetime.now().isoformat()}\n\n')
            fk.write('SET FOREIGN_KEY_CHECKS=0;\n')
            if fk_restore_statements:
                for stmt in fk_restore_statements:
                    fk.write(f'{stmt}\n')
            else:
                fk.write('-- 当前最新导出未生成额外外键恢复语句，此文件保留为空占位文件，避免误用历史外键脚本。\n')
            fk.write('SET FOREIGN_KEY_CHECKS=1;\n')

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
    parser.add_argument('--keep-foreign-keys', action='store_true', help='保留建表语句中的外键约束（默认移除）')
    parser.add_argument('--required-tables', default='upload_files,upload_chunks', help='导出前必须存在的关键表，逗号分隔')
    parser.add_argument('--skip-identity-upgrade', action='store_true', help='跳过用户身份字段自动升级')

    args = parser.parse_args()

    if not args.source_db_url:
        print('错误: 未提供源数据库 URL，请设置 DATABASE_URL 或传 --source-db-url')
        return 1

    output_file = build_output_file(args.output_file)
    include_tables = parse_csv(args.only_tables)
    exclude_tables = parse_csv(args.exclude_tables)
    required_tables = sorted(parse_csv(args.required_tables))

    print('=' * 60)
    print('导出数据库')
    print('=' * 60)
    print(f'源库: {args.source_db_url}')
    print(f'输出: {output_file}')
    print(f'移除外键: {"否" if args.keep_foreign_keys else "是"}')
    if required_tables:
        print(f'关键表校验: {", ".join(required_tables)}')

    if not args.skip_identity_upgrade:
        print('预处理: 升级源库用户身份字段...')
        upgrade_identity_schema(args.source_db_url, verbose=True)
        print('预处理: 升级源库订单 condition 表结构...')
        upgrade_order_condition_schema(args.source_db_url, verbose=True)
        print('预处理: 升级源库 orders.phase_id 字段...')
        upgrade_order_phase_schema(args.source_db_url, verbose=True)

    exported = export_database(

        source_db_url=args.source_db_url,
        output_file=output_file,
        include_tables=include_tables,
        exclude_tables=exclude_tables,
        chunk_size=max(1, args.chunk_size),
        strip_fk=not args.keep_foreign_keys,
        required_tables=required_tables,
    )

    print(f'\n导出完成: {exported}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
