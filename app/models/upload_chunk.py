"""
文件上传分片模型
"""
from app import db
from app.models.base import ToDictMixin


class UploadChunk(db.Model, ToDictMixin):
    """文件上传分片记录表"""
    __tablename__ = 'upload_chunks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    upload_id = db.Column(db.String(36), nullable=False, index=True, comment='上传会话UUID')
    chunk_index = db.Column(db.Integer, nullable=False, comment='分片索引')
    chunk_hash = db.Column(db.String(64), comment='分片SHA-256哈希')
    uploaded_at = db.Column(db.Integer, nullable=False, comment='上传时间戳')

    __table_args__ = (
        db.UniqueConstraint('upload_id', 'chunk_index', name='uk_upload_chunk'),
        db.Index('idx_upload_id', 'upload_id'),
    )
