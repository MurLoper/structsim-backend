#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 orders.model_level_id 字段
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app, db
from sqlalchemy import text, inspect


def migrate():
    """添加缺失的 model_level_id 列"""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('orders')]

        if 'model_level_id' not in columns:
            print("Adding orders.model_level_id column...")
            sql = "ALTER TABLE orders ADD COLUMN model_level_id INT COMMENT '模型层级ID'"
            db.session.execute(text(sql))
            db.session.commit()
            print("Success: Column added")
        else:
            print("Column model_level_id already exists")


if __name__ == '__main__':
    migrate()
