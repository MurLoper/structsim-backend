"""
文件上传模型
"""
from datetime import datetime
from app import db
from app.models.base import ToDictMixin


class UploadFile(db.Model, ToDictMixin):
    """文件上传记录表"""
    __tablename__ = 'upload_files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 文件标识
    file_hash = db.Column(db.String(64), nullable=False, index=True, comment='文件SHA-256哈希')
    file_name = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_size = db.Column(db.BigInteger, nullable=False, comment='文件大小(字节)')
    mime_type = db.Column(db.String(100), comment='MIME类型')

    # 上传会话
    upload_id = db.Column(db.String(36), unique=True, nullable=False, index=True, comment='上传会话UUID')
    user_id = db.Column(db.String(32), nullable=False, index=True, comment='上传用户标识(域账号)')


    # 分片配置
    chunk_size = db.Column(db.Integer, nullable=False, default=5242880, comment='分片大小(字节)')
    total_chunks = db.Column(db.Integer, nullable=False, comment='总分片数')



    # 状态
    status = db.Column(db.String(20), nullable=False, default='uploading', comment='状态: uploading/merging/completed/failed')
    storage_path = db.Column(db.String(500), comment='存储路径')

    # 元数据
    extra_data = db.Column(db.JSON, comment='额外元数据')
    error_message = db.Column(db.Text, comment='错误信息')

    # 时间戳
    created_at = db.Column(db.Integer, nullable=False, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, nullable=False, default=lambda: int(datetime.utcnow().timestamp()))
    completed_at = db.Column(db.Integer, comment='完成时间')
    expires_at = db.Column(db.Integer, index=True, comment='过期时间')
