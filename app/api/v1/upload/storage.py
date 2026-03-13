"""
文件存储管理
"""
import os
import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO
from werkzeug.utils import secure_filename


class StorageManager:
    """文件存储管理器"""

    def __init__(self, base_path: str = './storage'):
        self.base_path = Path(base_path)
        self.chunks_dir = self.base_path / 'chunks'
        self.files_dir = self.base_path / 'files'
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录存在"""
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def get_chunk_path(self, upload_id: str, chunk_index: int) -> Path:
        """获取分片存储路径"""
        upload_dir = self.chunks_dir / upload_id
        upload_dir.mkdir(exist_ok=True)
        return upload_dir / f"chunk_{chunk_index}"

    def save_chunk(self, upload_id: str, chunk_index: int,
                   chunk_data: BinaryIO, expected_hash: str) -> bool:
        """保存分片并校验哈希"""
        chunk_path = self.get_chunk_path(upload_id, chunk_index)

        # 计算哈希并保存
        hasher = hashlib.sha256()
        with open(chunk_path, 'wb') as f:
            chunk_data.seek(0)
            while True:
                data = chunk_data.read(8192)
                if not data:
                    break
                hasher.update(data)
                f.write(data)

        # 校验哈希
        if hasher.hexdigest() != expected_hash:
            chunk_path.unlink()
            return False
        return True

    def merge_chunks(self, upload_id: str, total_chunks: int, file_name: str) -> str:
        """合并分片为最终文件"""
        from datetime import datetime

        # 生成存储路径
        now = datetime.now()
        date_path = self.files_dir / str(now.year) / f"{now.month:02d}"
        date_path.mkdir(parents=True, exist_ok=True)

        safe_name = secure_filename(file_name)
        final_path = date_path / f"{upload_id[:8]}_{safe_name}"

        # 合并分片
        with open(final_path, 'wb') as outfile:
            for i in range(total_chunks):
                chunk_path = self.get_chunk_path(upload_id, i)
                if not chunk_path.exists():
                    raise FileNotFoundError(f"分片 {i} 不存在")
                with open(chunk_path, 'rb') as infile:
                    outfile.write(infile.read())

        # 清理分片
        self.cleanup_chunks(upload_id)

        return str(final_path.relative_to(self.base_path))

    def cleanup_chunks(self, upload_id: str) -> None:
        """清理分片目录"""
        chunk_dir = self.chunks_dir / upload_id
        if chunk_dir.exists():
            shutil.rmtree(chunk_dir)


storage_manager = StorageManager()
