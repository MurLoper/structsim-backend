"""
认证模块 - 业务逻辑层
职责：处理业务逻辑、调用Repository、事务管理
禁止：直接处理HTTP请求/响应、直接操作数据库
"""
import time
from typing import Optional, List, Dict
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

from app.common.errors import NotFoundError, BusinessError
from app.constants import ErrorCode
from app.models.auth import Role, Permission
from .repository import auth_repository


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.repository = auth_repository

    def _get_permission_codes(self, role_ids: Optional[List[int]]) -> List[str]:
        role_ids = list(role_ids or [])
        if not role_ids:
            return []
        roles = Role.query.filter(Role.id.in_(role_ids), Role.valid == 1).all()
        if not roles:
            return []
        if any(role.code == 'ADMIN' for role in roles if role.code):
            permissions = Permission.query.filter(Permission.valid == 1).order_by(Permission.sort.asc(), Permission.id.asc()).all()
            return [p.code for p in permissions]
        permission_ids = set()
        for role in roles:
            permission_ids.update(role.permission_ids or [])
        if not permission_ids:
            return []
        permissions = Permission.query.filter(Permission.id.in_(permission_ids), Permission.valid == 1).order_by(Permission.sort.asc(), Permission.id.asc()).all()
        return [p.code for p in permissions]
    
    def login(self, email: str, password: Optional[str] = None) -> Dict:
        """
        用户登录
        Args:
            email: 用户邮箱
            password: 密码（演示环境可选）
        Returns:
            包含token和用户信息的字典
        Raises:
            NotFoundError: 用户不存在
            BusinessError: 密码错误
        """
        user = self.repository.get_user_by_email(email)
        
        if not user:
            raise NotFoundError("用户不存在")
        
        # 演示环境：跳过密码验证
        # 生产环境：取消注释以下代码
        # if password and not check_password_hash(user.password_hash, password):
        #     raise BusinessError(ErrorCode.VALIDATION_ERROR, "密码错误")
        
        permission_codes = self._get_permission_codes(user.role_ids)

        # 生成访问令牌
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'permissions': permission_codes
            }
        )
        
        # 更新最后登录时间
        self.repository.update_last_login(user, int(time.time()))

        user_data = user.to_dict()
        user_data.update({
            'role_ids': user.role_ids or [],
            'permissions': permission_codes,
            'permission_codes': permission_codes
        })
        
        return {
            'token': access_token,
            'user': user_data
        }
    
    def get_current_user(self, user_id: int) -> Dict:
        """
        获取当前用户信息
        Args:
            user_id: 用户ID
        Returns:
            用户信息字典
        Raises:
            NotFoundError: 用户不存在
        """
        user = self.repository.get_user_by_id(user_id)
        
        if not user:
            raise NotFoundError("用户不存在")

        permission_codes = self._get_permission_codes(user.role_ids)
        user_data = user.to_dict()
        user_data.update({
            'role_ids': user.role_ids or [],
            'permissions': permission_codes,
            'permission_codes': permission_codes
        })
        
        return user_data
    
    def get_all_users(self) -> List[Dict]:
        """
        获取所有用户列表（用于演示登录选择）
        Returns:
            用户公开信息列表
        """
        users = self.repository.get_all_valid_users()
        return [user.to_public_dict() for user in users]
    
    def logout(self, user_id: int) -> Dict:
        """
        用户登出
        Args:
            user_id: 用户ID
        Returns:
            成功消息
        Note:
            实际应用中可能需要将token加入黑名单
        """
        # 这里可以添加token黑名单逻辑
        return {'message': '登出成功'}


# 单例实例
auth_service = AuthService()

