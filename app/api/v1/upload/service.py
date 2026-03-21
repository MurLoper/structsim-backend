"""
文件上传业务逻辑层
"""
import time
import uuid
from typing import Dict, Optional
from werkzeug.datastructures import FileStorage

from app.common.errors import BusinessError, NotFoundError
from app.constants import ErrorCode
from .repository import upload_repository
from .storage import storage_manager


class UploadService:
    """上传服务"""

    def check_file_exists(self, file_hash: str, user_identity: str) -> Dict:
        """检查文件是否存在（秒传）"""
        existing = upload_repository.find_by_hash(file_hash, user_identity)


        if existing:
            return {
                'exists': True,
                'file_id': existing.id,
                'storage_path': existing.storage_path
            }
        return {'exists': False}

    def init_upload(self, file_hash: str, file_name: str,
                    file_size: int, chunk_size: int,
                    user_identity: str, mime_type: Optional[str] = None) -> Dict:

        """初始化上传会话"""

        # 检查是否已存在
        existing = self.check_file_exists(file_hash, user_identity)

        if existing['exists']:
            raise BusinessError(ErrorCode.VALIDATION_ERROR,
                              "文件已存在，无需重复上传")

        # 计算分片数
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        # 创建上传记录
        now = int(time.time())
        upload_data = {
            'upload_id': str(uuid.uuid4()),
            'file_hash': file_hash,
            'file_name': file_name,
            'file_size': file_size,
            'mime_type': mime_type,
            'user_id': str(user_identity),

            'chunk_size': chunk_size,
            'total_chunks': total_chunks,
            'status': 'uploading',
            'created_at': now,
            'updated_at': now,
            'expires_at': now + 86400
        }

        upload = upload_repository.create(upload_data)

        return {
            'upload_id': upload.upload_id,
            'total_chunks': upload.total_chunks,
            'uploaded_chunks': [],
            'chunk_size': upload.chunk_size
        }

    def upload_chunk(self, upload_id: str, chunk_index: int,
                     chunk_hash: str, chunk_file: FileStorage) -> Dict:
        """上传单个分片"""

        upload = upload_repository.find_by_upload_id(upload_id)
        if not upload:
            raise NotFoundError("上传会话")

        if upload.status != 'uploading':
            raise BusinessError(ErrorCode.VALIDATION_ERROR,
                              f"上传状态异常: {upload.status}")

        if chunk_index >= upload.total_chunks:
            raise BusinessError(ErrorCode.VALIDATION_ERROR,
                              f"分片索引超出范围: {chunk_index}")

        # 保存并校验分片
        success = storage_manager.save_chunk(
            upload_id, chunk_index, chunk_file.stream, chunk_hash
        )

        if not success:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "分片校验失败")

        # 添加分片记录
        upload_repository.add_chunk(upload_id, chunk_index, chunk_hash)

        # 获取已上传数量
        uploaded_chunks = upload_repository.get_uploaded_chunks(upload_id)
        progress = len(uploaded_chunks) / upload.total_chunks

        return {
            'chunk_index': chunk_index,
            'uploaded': True,
            'progress': round(progress, 4)
        }

    def get_status(self, upload_id: str) -> Dict:
        """获取上传进度"""
        upload = upload_repository.find_by_upload_id(upload_id)
        if not upload:
            raise NotFoundError("上传会话")

        uploaded_chunks = upload_repository.get_uploaded_chunks(upload_id)
        progress = len(uploaded_chunks) / upload.total_chunks

        return {
            'upload_id': upload.upload_id,
            'status': upload.status,
            'total_chunks': upload.total_chunks,
            'uploaded_chunks': uploaded_chunks,
            'progress': round(progress, 4),
            'file_name': upload.file_name
        }

    def merge_chunks(self, upload_id: str) -> Dict:
        """合并分片为最终文件"""
        upload = upload_repository.find_by_upload_id(upload_id)
        if not upload:
            raise NotFoundError("上传会话")

        # 验证所有分片已上传
        uploaded_chunks = upload_repository.get_uploaded_chunks(upload_id)
        if len(uploaded_chunks) != upload.total_chunks:
            raise BusinessError(ErrorCode.VALIDATION_ERROR,
                              f"分片未完整上传: {len(uploaded_chunks)}/{upload.total_chunks}")

        # 合并分片
        try:
            storage_path = storage_manager.merge_chunks(
                upload_id, upload.total_chunks, upload.file_name
            )
            upload_repository.mark_completed(upload, storage_path)

            return {
                'file_id': upload.id,
                'storage_path': storage_path,
                'file_url': f"/files/{storage_path}"
            }
        except Exception as e:
            upload_repository.mark_failed(upload, str(e))
            raise BusinessError(ErrorCode.INTERNAL_ERROR, "文件合并失败")

    def cancel_upload(self, upload_id: str) -> None:
        """取消上传"""
        upload = upload_repository.find_by_upload_id(upload_id)
        if upload:
            storage_manager.cleanup_chunks(upload_id)
            upload_repository.delete(upload)


upload_service = UploadService()
