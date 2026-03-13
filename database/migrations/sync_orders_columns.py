#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 orders 表所有缺失字段
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app, db
from sqlalchemy import text, inspect


def migrate():
    """添加 orders 表缺失的所有列"""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        existing_cols = {col['name'] for col in inspector.get_columns('orders')}

        # 定义需要的列
        required_cols = {
            'model_level_id': "INT COMMENT '模型层级ID'",
            'origin_fold_type_id': "INT COMMENT '原始姿态类型ID'",
            'fold_type_ids': "JSON COMMENT '姿态类型ID列表'",
            'input_json': "JSON COMMENT '输入JSON完整配置'",
        }

        added = []
        for col_name, col_def in required_cols.items():
            if col_name not in existing_cols:
                print(f"Adding column: {col_name}")
                sql = f"ALTER TABLE orders ADD COLUMN {col_name} {col_def}"
                db.session.execute(text(sql))
                db.session.commit()
                added.append(col_name)

        if added:
            print(f"Success: Added {len(added)} columns: {', '.join(added)}")
        else:
            print("All columns already exist")


if __name__ == '__main__':
    migrate()
