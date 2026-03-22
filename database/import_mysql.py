"""
导入 SQL 到 MySQL（外键安全），支持直接导入最新导出文件。

用法示例:
  python database/import_mysql.py --db-url mysql+pymysql://user:pass@host:3306/db --sql-file database/export/xxx.sql
  python database/import_mysql.py --db-url mysql+pymysql://user:pass@host:3306/db --latest
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:  # pragma: no cover
    _load_dotenv = None


def load_env() -> None:
    if _load_dotenv is not None:
        _load_dotenv()

from sqlalchemy import create_engine, text, inspect


sys.path.insert(0, str(Path(__file__).parent.parent))

EXPORT_DIR = Path(__file__).parent / 'export'


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def ensure_required_tables(engine, required_tables: list[str]) -> list[str]:
    if not required_tables:
        return []
    existing = set(inspect(engine).get_table_names())
    return [name for name in required_tables if name not in existing]


def drop_all_tables(conn) -> None:
    rows = conn.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'")
    )
    table_names = [row[0] for row in rows.fetchall()]
    for name in table_names:
        conn.execute(text(f"DROP TABLE IF EXISTS `{name}`"))
    conn.commit()


def split_sql_statements(sql: str) -> List[str]:
    statements: List[str] = []
    buff: List[str] = []
    in_single = False
    in_double = False
    in_line_comment = False
    in_block_comment = False
    i = 0
    n = len(sql)

    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ''

        if in_line_comment:
            if ch == '\n':
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if ch == '*' and nxt == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if not in_single and not in_double:
            if ch == '-' and nxt == '-':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and nxt == '*':
                in_block_comment = True
                i += 2
                continue

        if ch == "'" and not in_double:
            escaped = i > 0 and sql[i - 1] == '\\'
            if not escaped:
                in_single = not in_single
            buff.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            escaped = i > 0 and sql[i - 1] == '\\'
            if not escaped:
                in_double = not in_double
            buff.append(ch)
            i += 1
            continue

        if ch == ';' and not in_single and not in_double:
            stmt = ''.join(buff).strip()
            if stmt:
                statements.append(stmt)
            buff = []
            i += 1
            continue

        buff.append(ch)
        i += 1

    tail = ''.join(buff).strip()
    if tail:
        statements.append(tail)

    return statements


def get_latest_export_file() -> Path | None:
    if not EXPORT_DIR.exists():
        return None
    files = sorted(EXPORT_DIR.glob('database_export_*.sql'), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def apply_fk_statements(conn, fk_sql_file: str) -> None:
    fk_path = Path(fk_sql_file)
    if not fk_path.exists():
        print(f'警告: 外键恢复文件不存在，已跳过: {fk_path}')
        return

    fk_statements = split_sql_statements(fk_path.read_text(encoding='utf-8'))
    print(f'开始恢复外键: {fk_path} ({len(fk_statements)} 条)')
    for stmt in fk_statements:
        conn.exec_driver_sql(stmt)
        conn.commit()
    print('外键恢复完成')


def import_database(
    sql_file: str | None,
    db_url: str,
    stop_on_error: bool = True,
    fk_sql_file: str | None = None,
    required_tables: list[str] | None = None,
    drop_all_first: bool = False,
    fk_only: bool = False,
) -> bool:
    sql_path: Path | None = None
    statements: List[str] = []

    if sql_file:
        sql_path = Path(sql_file)
        if not sql_path.exists():
            print(f'错误: SQL 文件不存在: {sql_path}')
            return False

        content = sql_path.read_text(encoding='utf-8')
        statements = split_sql_statements(content)
        if not statements:
            print('错误: SQL 文件为空或无可执行语句')
            return False

    if not statements and not fk_sql_file:
        print('错误: 请提供可执行的 --sql-file，或使用 --fk-sql-file 配合 --fk-only')
        return False

    print('=' * 60)
    print('导入数据库' if not fk_only else '恢复外键')
    print('=' * 60)
    print(f'目标库: {db_url}')
    if statements and sql_path is not None:
        print(f'SQL文件: {sql_path}')
        print(f'语句数: {len(statements)}')
    if fk_only and fk_sql_file:
        print(f'外键文件: {fk_sql_file}')

    required_tables = required_tables or []
    engine = create_engine(db_url)
    failed = 0

    with engine.connect() as conn:
        conn.execute(text('SET FOREIGN_KEY_CHECKS=0'))
        conn.commit()
        try:
            if drop_all_first and statements:
                print('先清空目标库所有表...')
                drop_all_tables(conn)

            if statements and not fk_only:
                for idx, stmt in enumerate(statements, 1):
                    try:
                        conn.exec_driver_sql(stmt)
                        conn.commit()
                        if idx % 50 == 0 or idx == len(statements):
                            print(f'已执行: {idx}/{len(statements)}')
                    except Exception as exc:
                        failed += 1
                        conn.rollback()
                        print(f'[失败] {idx}/{len(statements)}: {str(exc)[:200]}')
                        if stop_on_error:
                            raise

            if fk_sql_file:
                apply_fk_statements(conn, fk_sql_file)
        finally:
            conn.execute(text('SET FOREIGN_KEY_CHECKS=1'))
            conn.commit()

    missing_tables = ensure_required_tables(engine, required_tables)
    if missing_tables:
        print(f'导入后关键表缺失: {", ".join(missing_tables)}')
        return False

    if failed > 0:
        print(f'导入完成（存在失败）: 失败 {failed} 条')
        return not stop_on_error

    print('导入完成（全部成功）')
    return True


def main() -> int:
    load_env()

    parser = argparse.ArgumentParser(description='导入 SQL 文件到 MySQL')
    parser.add_argument('--sql-file', default=None, help='SQL 文件路径')
    parser.add_argument('--latest', action='store_true', help='自动使用 database/export 最新 SQL 文件')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), help='目标数据库连接 URL，默认读取 DATABASE_URL')
    parser.add_argument('--fk-sql-file', default=None, help='导入完成后执行的外键恢复 SQL 文件路径')
    parser.add_argument('--apply-latest-fk', action='store_true', help='自动应用与 --latest SQL 对应的 *_foreign_keys.sql')
    parser.add_argument('--fk-only', action='store_true', help='仅执行外键恢复，不重新导入主 SQL')
    parser.add_argument('--required-tables', default='upload_files,upload_chunks', help='导入后必须存在的关键表，逗号分隔')
    parser.add_argument('--drop-all-first', action='store_true', help='导入前先删除目标库全部业务表（用于全量覆盖）')
    parser.add_argument('--continue-on-error', action='store_true', help='遇错继续执行，不中断')
    args = parser.parse_args()

    if not args.db_url:
        print('错误: 未提供目标数据库 URL，请设置 DATABASE_URL 或传 --db-url')
        return 1

    sql_file = args.sql_file
    latest: Path | None = None
    if args.latest:
        latest = get_latest_export_file()
        if not latest:
            print('错误: 未找到可用导出文件')
            return 1
        sql_file = str(latest)

    if not sql_file and not args.fk_only:
        print('错误: 请提供 --sql-file 或使用 --latest')
        return 1

    fk_sql_file = args.fk_sql_file
    if args.apply_latest_fk and latest is not None:
        fk_sql_file = str(latest.with_name(f'{latest.stem}_foreign_keys.sql'))

    if args.fk_only and not fk_sql_file:
        print('错误: --fk-only 模式下必须提供 --fk-sql-file，或配合 --latest --apply-latest-fk 使用')
        return 1

    required_tables = parse_csv(args.required_tables)

    ok = import_database(
        sql_file=sql_file,
        db_url=args.db_url,
        stop_on_error=not args.continue_on_error,
        fk_sql_file=fk_sql_file,
        required_tables=required_tables,
        drop_all_first=args.drop_all_first,
        fk_only=args.fk_only,
    )
    return 0 if ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
