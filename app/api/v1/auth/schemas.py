"""
认证模块请求与响应 schema。
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """密码登录请求：域账号 + 密码"""

    domain_account: str = Field(..., description="域账号")
    password_ciphertext: str = Field(..., min_length=1, description="RSA-OAEP 加密后的密码")
    key_id: str = Field(..., min_length=1, max_length=64, description="公钥版本标识")

    @field_validator("domain_account")
    @classmethod
    def validate_domain_account(cls, value: str) -> str:
        candidate = (value or "").strip()
        if not candidate:
            raise ValueError("域账号不能为空")
        return candidate


class LoginResponse(BaseModel):
    token: str = Field(..., description="JWT 访问令牌")


class LoginPublicKeyResponse(BaseModel):
    key_id: str = Field(..., description="登录公钥版本标识")
    algorithm: str = Field(..., description="加密算法")
    public_key_pem: str = Field(..., description="PEM 格式公钥")


class SessionResponse(BaseModel):
    user: dict = Field(..., description="当前用户信息")
    menus: list[dict] = Field(..., description="当前用户菜单")


class UserPublicInfo(BaseModel):
    id: str
    domain_account: str
    user_name: Optional[str] = None
    real_name: Optional[str] = None
    email: str
    lc_user_id: Optional[str] = None
