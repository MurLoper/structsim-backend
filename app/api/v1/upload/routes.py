"""
文件上传API路由
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.common import success, error
from app.constants import ErrorCode
from app.common.errors import BusinessError, NotFoundError
from app.common.serializers import get_snake_json
from .schemas import CheckFileRequest, InitUploadRequest, MergeChunksRequest
from .service import upload_service

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')


@upload_bp.route('/check', methods=['POST'])
@jwt_required()
def check_file():
    """检查文件是否存在（秒传）"""
    try:
        user_id = int(get_jwt_identity())
        validated = CheckFileRequest(**(get_snake_json() or {}))
        result = upload_service.check_file_exists(
            validated.file_hash, user_id
        )
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@upload_bp.route('/init', methods=['POST'])
@jwt_required()
def init_upload():
    """初始化上传会话"""
    try:
        user_id = int(get_jwt_identity())
        validated = InitUploadRequest(**(get_snake_json() or {}))
        result = upload_service.init_upload(
            validated.file_hash,
            validated.file_name,
            validated.file_size,
            validated.chunk_size,
            user_id,
            validated.mime_type
        )
        return success(result, "上传会话已创建")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@upload_bp.route('/chunk', methods=['POST'])
@jwt_required()
def upload_chunk():
    """上传单个分片"""
    try:
        upload_id = request.form.get('upload_id')
        chunk_index_str = request.form.get('chunk_index')
        chunk_hash = request.form.get('chunk_hash')
        chunk_file = request.files.get('file')

        if not all([upload_id, chunk_index_str is not None, chunk_hash, chunk_file]):
            return error(ErrorCode.VALIDATION_ERROR, "缺少必要参数", http_status=400)

        chunk_index = int(chunk_index_str)
        result = upload_service.upload_chunk(
            upload_id, chunk_index, chunk_hash, chunk_file
        )
        return success(result)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@upload_bp.route('/status/<upload_id>', methods=['GET'])
@jwt_required()
def get_status(upload_id: str):
    """获取上传进度"""
    try:
        result = upload_service.get_status(upload_id)
        return success(result)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@upload_bp.route('/merge', methods=['POST'])
@jwt_required()
def merge_chunks():
    """合并分片为最终文件"""
    try:
        validated = MergeChunksRequest(**(get_snake_json() or {}))
        result = upload_service.merge_chunks(validated.upload_id)
        return success(result, "文件上传完成")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@upload_bp.route('/cancel/<upload_id>', methods=['DELETE'])
@jwt_required()
def cancel_upload(upload_id: str):
    """取消上传"""
    try:
        upload_service.cancel_upload(upload_id)
        return success(None, "上传已取消")
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)
