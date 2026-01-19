"""
错误码定义
"""
from enum import IntEnum


class ErrorCode(IntEnum):
    """错误码枚举"""
    # 成功
    SUCCESS = 0
    
    # 400xxx - 参数错误
    PARAM_MISSING = 400001
    PARAM_INVALID = 400002
    PARAM_TYPE_ERROR = 400003
    VALIDATION_ERROR = 400004
    
    # 401xxx - 认证错误
    TOKEN_MISSING = 401001
    TOKEN_INVALID = 401002
    TOKEN_EXPIRED = 401003
    LOGIN_FAILED = 401004
    
    # 403xxx - 权限错误
    PERMISSION_DENIED = 403001
    RESOURCE_FORBIDDEN = 403002
    
    # 404xxx - 资源不存在
    RESOURCE_NOT_FOUND = 404001
    USER_NOT_FOUND = 404002
    PROJECT_NOT_FOUND = 404003
    ORDER_NOT_FOUND = 404004
    CONFIG_NOT_FOUND = 404005
    NOT_FOUND = 404001  # 通用资源不存在

    # 409xxx - 业务逻辑错误
    BUSINESS_ERROR = 409001
    DUPLICATE_RESOURCE = 409002

    # 500xxx - 服务器错误
    INTERNAL_ERROR = 500001
    DATABASE_ERROR = 500002
    EXTERNAL_SERVICE_ERROR = 500003


# 错误码对应的默认消息
ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "操作成功",
    ErrorCode.PARAM_MISSING: "参数缺失",
    ErrorCode.PARAM_INVALID: "参数无效",
    ErrorCode.PARAM_TYPE_ERROR: "参数类型错误",
    ErrorCode.VALIDATION_ERROR: "数据校验失败",
    ErrorCode.TOKEN_MISSING: "缺少认证令牌",
    ErrorCode.TOKEN_INVALID: "认证令牌无效",
    ErrorCode.TOKEN_EXPIRED: "认证令牌已过期",
    ErrorCode.LOGIN_FAILED: "登录失败",
    ErrorCode.PERMISSION_DENIED: "权限不足",
    ErrorCode.RESOURCE_FORBIDDEN: "禁止访问该资源",
    ErrorCode.RESOURCE_NOT_FOUND: "资源不存在",
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.PROJECT_NOT_FOUND: "项目不存在",
    ErrorCode.ORDER_NOT_FOUND: "订单不存在",
    ErrorCode.CONFIG_NOT_FOUND: "配置不存在",
    ErrorCode.NOT_FOUND: "资源不存在",
    ErrorCode.BUSINESS_ERROR: "业务逻辑错误",
    ErrorCode.DUPLICATE_RESOURCE: "资源已存在",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.DATABASE_ERROR: "数据库错误",
    ErrorCode.EXTERNAL_SERVICE_ERROR: "外部服务错误",
}

