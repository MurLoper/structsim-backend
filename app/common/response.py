"""
统一响应封装
"""
import uuid
from typing import Any, Optional
from flask import jsonify, g, Response
from app.constants import ErrorCode, ERROR_MESSAGES


def get_trace_id() -> str:
    """获取或生成trace_id"""
    if not hasattr(g, 'trace_id'):
        g.trace_id = str(uuid.uuid4())[:8]
    return g.trace_id


def success(data: Any = None, msg: str = "ok") -> Response:
    """成功响应"""
    return jsonify({
        "code": ErrorCode.SUCCESS,
        "msg": msg,
        "data": data,
        "trace_id": get_trace_id()
    })


def error(
    code: ErrorCode, 
    msg: Optional[str] = None, 
    data: Any = None,
    http_status: int = 200
) -> tuple[Response, int]:
    """错误响应"""
    return jsonify({
        "code": code,
        "msg": msg or ERROR_MESSAGES.get(code, "未知错误"),
        "data": data,
        "trace_id": get_trace_id()
    }), http_status


def paginated(
    items: list,
    total: int,
    page: int,
    page_size: int,
    msg: str = "ok"
) -> Response:
    """分页响应 - 使用snake_case，由全局中间件统一转换为camelCase"""
    return jsonify({
        "code": ErrorCode.SUCCESS,
        "msg": msg,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        },
        "trace_id": get_trace_id()
    })

