"""
通用装饰器
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from flask import request, g
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.common.response import error
from app.constants import ErrorCode

logger = logging.getLogger(__name__)


def require_permission(permission: str):
    """权限校验装饰器"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                identity = get_jwt_identity()
                claims = get_jwt() or {}
                user_permissions = claims.get('permissions', [])
                if isinstance(identity, dict):
                    user_id = identity.get('id')
                elif isinstance(identity, str) and identity.isdigit():
                    user_id = int(identity)
                else:
                    user_id = identity
                
                if permission not in user_permissions:
                    logger.warning(f"Permission denied: {permission} for user {user_id}")
                    return error(ErrorCode.PERMISSION_DENIED, f"缺少权限: {permission}", http_status=403)
                
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Permission check failed: {e}")
                return error(ErrorCode.TOKEN_INVALID, "认证失败", http_status=401)
        return decorated_function
    return decorator


def log_request(f: Callable) -> Callable:
    """请求日志装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        trace_id = getattr(g, 'trace_id', 'unknown')
        
        logger.info(f"[{trace_id}] {request.method} {request.path} - Start")
        
        try:
            result = f(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"[{trace_id}] {request.method} {request.path} - End ({elapsed:.2f}ms)")
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"[{trace_id}] {request.method} {request.path} - Error ({elapsed:.2f}ms): {e}")
            raise
    return decorated_function


def validate_json(schema_class):
    """JSON数据校验装饰器"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                json_data = request.get_json(force=True, silent=True) or {}
                validated = schema_class(**json_data)
                g.validated_data = validated
                return f(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Validation error: {e}")
                return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
        return decorated_function
    return decorator

