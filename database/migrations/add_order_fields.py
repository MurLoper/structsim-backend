"""
添加订单表新字段
- model_level_id: 模型层级ID
- origin_fold_type_id: 原始姿态类型ID
- fold_type_ids: 姿态类型ID列表
- input_json: 输入JSON完整配置
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app, db

def upgrade():
    """添加新字段"""
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text("ALTER TABLE orders ADD COLUMN model_level_id INTEGER"))
            conn.commit()
            print("Added model_level_id")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"Error model_level_id: {e}")

        try:
            conn.execute(db.text("ALTER TABLE orders ADD COLUMN origin_fold_type_id INTEGER"))
            conn.commit()
            print("Added origin_fold_type_id")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"Error origin_fold_type_id: {e}")

        try:
            conn.execute(db.text("ALTER TABLE orders ADD COLUMN fold_type_ids TEXT"))
            conn.commit()
            print("Added fold_type_ids")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"Error fold_type_ids: {e}")

        try:
            conn.execute(db.text("ALTER TABLE orders ADD COLUMN input_json TEXT"))
            conn.commit()
            print("Added input_json")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"Error input_json: {e}")

    print("Migration completed")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        upgrade()
