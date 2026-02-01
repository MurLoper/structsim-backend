#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库导出工具
导出当前数据库的结构和完整数据到 JSON 文件
"""

import sys
import io
import json
import os
from pathlib import Path
from datetime import datetime

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from sqlalchemy import inspect, text


def get_table_data(table_name: str) -> list:
    """获取表的所有数据"""
    try:
        result = db.session.execute(text(f"SELECT * FROM {table_name}"))
        columns = result.keys()
        rows = []
        for row in result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # 处理特殊类型
                if isinstance(val, bytes):
                    val = val.decode('utf-8', errors='replace')
                elif isinstance(val, datetime):
                    val = int(val.timestamp())
                row_dict[col] = val
            rows.append(row_dict)
        return rows
    except Exception as e:
        print(f"  ⚠️  导出表 {table_name} 失败: {e}")
        return []


def get_all_tables() -> list:
    """获取所有表名"""
    inspector = inspect(db.engine)
    return inspector.get_table_names()


def export_schema() -> dict:
    """导出数据库结构"""
    inspector = inspect(db.engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            col_info = {
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col.get('nullable', True),
                'default': str(col.get('default')) if col.get('default') else None,
            }
            columns.append(col_info)

        # 获取主键
        pk = inspector.get_pk_constraint(table_name)

        # 获取外键
        fks = inspector.get_foreign_keys(table_name)

        # 获取索引
        indexes = inspector.get_indexes(table_name)

        schema[table_name] = {
            'columns': columns,
            'primary_key': pk.get('constrained_columns', []) if pk else [],
            'foreign_keys': fks,
            'indexes': indexes,
        }

    return schema


def export_all_data(output_dir: Path):
    """导出所有表数据到单独的 JSON 文件"""
    tables = get_all_tables()

    # 定义导出顺序（考虑外键依赖）
    export_order = [
        # 基础配置表（无外键依赖）
        'departments', 'permissions', 'roles', 'menus',
        'projects', 'sim_types', 'model_levels', 'fold_types',
        'solvers', 'solver_resources', 'status_defs', 'care_devices',
        'param_defs', 'output_defs', 'condition_defs',
        'automation_modules', 'workflows',
        # 用户表
        'users',
        # 关联表
        'fold_type_sim_type_rels', 'working_conditions',
        'param_groups', 'param_group_param_rels',
        'condition_output_groups', 'cond_out_group_condition_rels', 'cond_out_group_output_rels',
        'param_tpl_sets', 'param_tpl_items', 'cond_out_sets',
        'project_sim_type_rels', 'sim_type_param_group_rels',
        'sim_type_cond_out_group_rels', 'sim_type_solver_rels',
        'user_project_permissions',
        # 业务数据表
        'orders', 'order_results', 'sim_type_results', 'rounds',
    ]

    # 添加未在列表中的表
    for table in tables:
        if table not in export_order:
            export_order.append(table)

    exported_data = {}

    for table in export_order:
        if table not in tables:
            continue
        print(f"  导出表: {table}...")
        data = get_table_data(table)
        if data:
            exported_data[table] = data
            print(f"    ✓ {len(data)} 条记录")
        else:
            print(f"    - 空表")

    return exported_data


def main():
    print("\n" + "=" * 60)
    print("🚀 StructSim 数据库导出工具")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        output_dir = SCRIPT_DIR / 'exported-data'
        output_dir.mkdir(exist_ok=True)

        # 显示当前数据库信息
        current_db = str(db.engine.url)
        db_type = 'SQLite' if 'sqlite' in current_db else 'MySQL'
        print(f"\n📊 数据库类型: {db_type}")
        print(f"📍 连接地址: {current_db}")

        # 导出结构
        print("\n📋 导出数据库结构...")
        schema = export_schema()
        schema_file = output_dir / 'schema.json'
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 结构已保存到: {schema_file}")

        # 导出数据
        print("\n📦 导出数据...")
        all_data = export_all_data(output_dir)

        # 保存完整数据到单个文件
        full_data_file = output_dir / 'full_data.json'
        with open(full_data_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n  ✓ 完整数据已保存到: {full_data_file}")

        # 统计
        total_records = sum(len(data) for data in all_data.values())
        print(f"\n📊 导出统计:")
        print(f"  - 表数量: {len(all_data)}")
        print(f"  - 总记录数: {total_records}")

        print("\n" + "=" * 60)
        print("✅ 导出完成！")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
