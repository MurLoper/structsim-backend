"""
添加upload_chunks表并移除upload_files.uploaded_chunks字段
"""
from app import create_app, db
from sqlalchemy import text


def upgrade():
    """升级数据库"""
    app = create_app()
    with app.app_context():
        conn = db.session.connection()

        # 创建upload_chunks表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS upload_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id VARCHAR(36) NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_hash VARCHAR(64),
                uploaded_at INTEGER NOT NULL,
                FOREIGN KEY (upload_id) REFERENCES upload_files(upload_id),
                UNIQUE (upload_id, chunk_index)
            )
        """))

        # 创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_upload_id ON upload_chunks(upload_id)
        """))

        db.session.commit()
        print("Migration completed: upload_chunks table created")


if __name__ == '__main__':
    upgrade()
