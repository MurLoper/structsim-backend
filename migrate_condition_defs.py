"""
数据库迁移脚本：为 condition_defs 表添加字段
执行时间: 2024-01-17
"""

from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # 检查并添加 category 字段
            try:
                db.session.execute(text("ALTER TABLE condition_defs ADD COLUMN category VARCHAR(50)"))
                print("✓ Added category column")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("⊙ Category column already exists")
                else:
                    raise

            # 检查并添加 unit 字段
            try:
                db.session.execute(text("ALTER TABLE condition_defs ADD COLUMN unit VARCHAR(20)"))
                print("✓ Added unit column")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("⊙ Unit column already exists")
                else:
                    raise

            # 重命名 schema 字段为 condition_schema（避免 SQL 关键字冲突）
            try:
                db.session.execute(text("ALTER TABLE condition_defs CHANGE COLUMN `schema` condition_schema JSON"))
                print("✓ Renamed schema to condition_schema")
            except Exception as e:
                if "Unknown column" in str(e) and "schema" in str(e):
                    print("⊙ Schema column doesn't exist or already renamed")
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

