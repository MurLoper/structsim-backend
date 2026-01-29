#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加菜单表新字段
支持 MySQL 和 SQLite
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from app import create_app, db


def get_existing_columns(table_name: str) -> set:
    """获取表的现有字段"""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    return {col['name'] for col in columns}


def add_column_if_not_exists(table: str, column: str, definition: str):
    """如果字段不存在则添加"""
    existing = get_existing_columns(table)
    if column in existing:
        print(f"  ✓ {column} 已存在，跳过")
        return False

    db_url = str(db.engine.url)
    is_mysql = 'mysql' in db_url

    if is_mysql:
        sql = f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"
    else:
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"

    db.session.execute(text(sql))
    db.session.commit()
    print(f"  ✓ 添加字段: {column}")
    return True
