"""
通用模块
"""
from .response import success, error, paginated, get_trace_id
from .errors import BusinessError, ValidationError, NotFoundError, PermissionError, AuthenticationError
from .pagination import PageParams, PageResult
from .decorators import require_permission, log_request, validate_json

__all__ = [
    # Response
    'success', 'error', 'paginated', 'get_trace_id',
    # Errors
    'BusinessError', 'ValidationError', 'NotFoundError', 'PermissionError', 'AuthenticationError',
    # Pagination
    'PageParams', 'PageResult',
    # Decorators
    'require_permission', 'log_request', 'validate_json'
]

