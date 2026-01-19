"""
数据库迁移脚本：为 fold_types 表添加 remark 字段
执行时间: 2024-01-18
"""

from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # 添加 remark 字段
            try:
                db.session.execute(text("ALTER TABLE fold_types ADD COLUMN remark TEXT"))
                print("✓ Added remark column to fold_types")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("⊙ Remark column already exists in fold_types")
                else:
                    raise
            
            # 提交更改
            db.session.commit()
            print("✓ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate()

