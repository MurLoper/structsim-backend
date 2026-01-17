"""
认证模块 - 数据校验层
职责：使用Pydantic定义请求/响应数据结构
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: Optional[str] = Field(None, description="密码（演示环境可选）")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str = Field(..., description="JWT访问令牌")
    user: dict = Field(..., description="用户信息")


class UserPublicInfo(BaseModel):
    """用户公开信息"""
    id: int
    username: str
    email: str
    role: str

