"""
异常基类与错误处理
"""
from typing import Any, Optional
from app.constants import ErrorCode, ERROR_MESSAGES


class BusinessError(Exception):
    """业务异常基类"""
    
    def __init__(
        self, 
        code: ErrorCode, 
        msg: Optional[str] = None,
        data: Any = None,
        field: Optional[str] = None
    ):
        self.code = code
        self.msg = msg or ERROR_MESSAGES.get(code, "未知错误")
        self.data = data
        self.field = field
        super().__init__(self.msg)
    
    def to_dict(self) -> dict:
        result = {
            "code": self.code,
            "msg": self.msg,
            "data": self.data
        }
        if self.field:
            result["field"] = self.field
        return result


class ValidationError(BusinessError):
    """数据校验异常"""
    
    def __init__(self, msg: str, errors: Optional[list] = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            msg=msg,
            data={"errors": errors} if errors else None
        )


class NotFoundError(BusinessError):
    """资源不存在异常"""
    
    def __init__(self, resource: str, resource_id: Any = None):
        msg = f"{resource}不存在"
        if resource_id:
            msg = f"{resource} (ID: {resource_id}) 不存在"
        super().__init__(code=ErrorCode.RESOURCE_NOT_FOUND, msg=msg)


class PermissionError(BusinessError):
    """权限异常"""
    
    def __init__(self, msg: str = "权限不足"):
        super().__init__(code=ErrorCode.PERMISSION_DENIED, msg=msg)


class AuthenticationError(BusinessError):
    """认证异常"""
    
    def __init__(self, code: ErrorCode = ErrorCode.TOKEN_INVALID, msg: str = "认证失败"):
        super().__init__(code=code, msg=msg)

