"""
认证模块请求与响应 schema。
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """密码登录请求：域账号 + 密码"""

    domain_account: str = Field(..., description="域账号")
    password: str = Field(..., min_length=1, description="密码")

    @field_validator("domain_account")
    @classmethod
    def validate_domain_account(cls, value: str) -> str:
        candidate = (value or "").strip()
        if not candidate:
            raise ValueError("域账号不能为空")
        return candidate


class LoginResponse(BaseModel):
    token: str = Field(..., description="JWT 访问令牌")


class UserPublicInfo(BaseModel):
    id: str
    domain_account: str
    user_name: Optional[str] = None
    real_name: Optional[str] = None
    email: str
    lc_user_id: Optional[str] = None
