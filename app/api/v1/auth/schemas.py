"""
认证模块 - 数据校验层
职责：使用Pydantic定义请求/响应数据结构
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class LoginRequest(BaseModel):
    """密码登录请求（域账号 + 密码）"""
    domain_account: str = Field(..., description="域账号")
    password: str = Field(..., min_length=1, description="密码")

    @field_validator('domain_account')
    @classmethod
    def validate_domain_account(cls, value: str) -> str:
        candidate = (value or '').strip()
        if not candidate:
            raise ValueError('域账号不能为空')
        return candidate


class LoginResponse(BaseModel):
    """登录响应"""
    token: str = Field(..., description="JWT访问令牌")
    user: dict = Field(..., description="用户信息")


class UserPublicInfo(BaseModel):
    """用户公开信息"""
    id: str
    username: Optional[str] = None
    email: str
    role: str
    domain_account: Optional[str] = None
    lc_user_id: Optional[str] = None

