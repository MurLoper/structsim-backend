"""
文件上传请求验证模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class CheckFileRequest(BaseModel):
    """检查文件是否存在"""
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_name: str = Field(..., max_length=255)
    file_size: int = Field(..., gt=0)


class InitUploadRequest(BaseModel):
    """初始化上传"""
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_name: str = Field(..., max_length=255)
    file_size: int = Field(..., gt=0, le=2147483648)
    chunk_size: int = Field(default=5242880, ge=1048576, le=10485760)
    mime_type: Optional[str] = None


class MergeChunksRequest(BaseModel):
    """合并分片"""
    upload_id: str = Field(..., min_length=36, max_length=36)
