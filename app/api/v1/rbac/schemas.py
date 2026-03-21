"""
RBAC - Pydantic Schema 定义
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(..., min_length=1, max_length=120)
    domain_account: str = Field(..., min_length=1, max_length=32)


    lc_user_id: Optional[str] = Field(None, min_length=1, max_length=64)
    user_name: Optional[str] = Field(None, max_length=100)

    real_name: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    avatar: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role_ids: Optional[List[int]] = None
    valid: Optional[int] = Field(default=1, ge=0, le=1)



class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, min_length=1, max_length=120)

    domain_account: Optional[str] = Field(None, min_length=1, max_length=32)
    lc_user_id: Optional[str] = Field(None, min_length=1, max_length=64)
    user_name: Optional[str] = Field(None, max_length=100)

    real_name: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    avatar: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role_ids: Optional[List[int]] = None
    valid: Optional[int] = Field(default=None, ge=0, le=1)




class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=200)
    permission_ids: Optional[List[int]] = None
    valid: Optional[int] = Field(default=1, ge=0, le=1)
    sort: Optional[int] = Field(default=100, ge=0)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=200)
    permission_ids: Optional[List[int]] = None
    valid: Optional[int] = Field(default=None, ge=0, le=1)
    sort: Optional[int] = Field(default=None, ge=0)


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    type: Optional[str] = Field(None, max_length=20)
    resource: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    valid: Optional[int] = Field(default=1, ge=0, le=1)
    sort: Optional[int] = Field(default=100, ge=0)


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[str] = Field(None, max_length=20)
    resource: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    valid: Optional[int] = Field(default=None, ge=0, le=1)
    sort: Optional[int] = Field(default=None, ge=0)
