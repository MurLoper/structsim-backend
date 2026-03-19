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
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

from sqlalchemy import create_engine, text


sys.path.insert(0, str(Path(__file__).parent.parent))

EXPORT_DIR = Path(__file__).parent / 'export'


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


def import_database(sql_file: str, db_url: str, stop_on_error: bool = True) -> bool:
    sql_path = Path(sql_file)
    if not sql_path.exists():
        print(f'错误: SQL 文件不存在: {sql_path}')
        return False

    content = sql_path.read_text(encoding='utf-8')
    statements = split_sql_statements(content)
    if not statements:
        print('错误: SQL 文件为空或无可执行语句')
        return False

    print('=' * 60)
    print('导入数据库')
    print('=' * 60)
    print(f'目标库: {db_url}')
    print(f'SQL文件: {sql_path}')
    print(f'语句数: {len(statements)}')

    engine = create_engine(db_url)
    failed = 0

    with engine.connect() as conn:
        conn.execute(text('SET FOREIGN_KEY_CHECKS=0'))
        conn.commit()
        try:
            for idx, stmt in enumerate(statements, 1):
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                    if idx % 50 == 0 or idx == len(statements):
                        print(f'已执行: {idx}/{len(statements)}')
                except Exception as exc:
                    failed += 1
                    conn.rollback()
                    print(f'[失败] {idx}/{len(statements)}: {str(exc)[:200]}')
                    if stop_on_error:
                        raise
        finally:
            conn.execute(text('SET FOREIGN_KEY_CHECKS=1'))
            conn.commit()

    if failed > 0:
        print(f'导入完成（存在失败）: 失败 {failed} 条')
        return not stop_on_error

    print('导入完成（全部成功）')
    return True


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description='导入 SQL 文件到 MySQL')
    parser.add_argument('--sql-file', default=None, help='SQL 文件路径')
    parser.add_argument('--latest', action='store_true', help='自动使用 database/export 最新 SQL 文件')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), help='目标数据库连接 URL，默认读取 DATABASE_URL')
    parser.add_argument('--continue-on-error', action='store_true', help='遇错继续执行，不中断')
    args = parser.parse_args()

    if not args.db_url:
        print('错误: 未提供目标数据库 URL，请设置 DATABASE_URL 或传 --db-url')
        return 1

    sql_file = args.sql_file
    if args.latest:
        latest = get_latest_export_file()
        if not latest:
            print('错误: 未找到可用导出文件')
            return 1
        sql_file = str(latest)

    if not sql_file:
        print('错误: 请提供 --sql-file 或使用 --latest')
        return 1

    ok = import_database(
        sql_file=sql_file,
        db_url=args.db_url,
        stop_on_error=not args.continue_on_error,
    )
    return 0 if ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
