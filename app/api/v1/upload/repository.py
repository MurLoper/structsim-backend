"""
文件上传数据访问层
"""
import time
from typing import Optional, List
from app.models.upload import UploadFile
from app import db


class UploadRepository:
    """上传文件仓储"""

    @staticmethod
    def find_by_hash(file_hash: str, user_id: int) -> Optional[UploadFile]:
        """根据哈希查找已完成的文件"""
        return UploadFile.query.filter_by(
            file_hash=file_hash,
            user_id=user_id,
            status='completed'
        ).first()

    @staticmethod
    def find_by_upload_id(upload_id: str) -> Optional[UploadFile]:
        """根据上传ID查找"""
        return UploadFile.query.filter_by(upload_id=upload_id).first()

    @staticmethod
    def create(upload_data: dict) -> UploadFile:
        """创建上传记录"""
        upload = UploadFile(**upload_data)
        db.session.add(upload)
        db.session.commit()
        return upload

    @staticmethod
    def update_chunks(upload: UploadFile, chunk_index: int) -> None:
        """更新已上传分片列表"""
        chunks = upload.uploaded_chunks or []
        if chunk_index not in chunks:
            chunks.append(chunk_index)
            chunks.sort()
        upload.uploaded_chunks = chunks
        upload.updated_at = int(time.time())
        db.session.commit()

    @staticmethod
    def mark_completed(upload: UploadFile, storage_path: str) -> None:
        """标记为已完成"""
        upload.status = 'completed'
        upload.storage_path = storage_path
        upload.completed_at = int(time.time())
        upload.updated_at = int(time.time())
        db.session.commit()

    @staticmethod
    def mark_failed(upload: UploadFile, error_msg: str) -> None:
        """标记为失败"""
        upload.status = 'failed'
        upload.error_message = error_msg
        upload.updated_at = int(time.time())
        db.session.commit()

    @staticmethod
    def delete(upload: UploadFile) -> None:
        """删除上传记录"""
        db.session.delete(upload)
        db.session.commit()


upload_repository = UploadRepository()
