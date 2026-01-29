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
from app.models.auth import Role, Permission, Menu
from .repository import auth_repository


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.repository = auth_repository

    def _get_role_codes(self, role_ids: Optional[List[int]]) -> List[str]:
        """获取角色编码列表"""
        role_ids = list(role_ids or [])
        if not role_ids:
            return []
        roles = Role.query.filter(Role.id.in_(role_ids), Role.valid == 1).all()
        return [r.code for r in roles if r.code]

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
        用户登录（模拟大网SSO登录）
        Args:
            email: 用户邮箱
            password: 密码（可选，模拟模式下不验证）
        Returns:
            包含token和用户信息的字典
        Raises:
            NotFoundError: 用户不存在
            BusinessError: 账号被禁用
        Note:
            当前为模拟模式，不验证密码。
            实际生产环境应对接大网SSO/Keycloak进行认证。
        """
        user = self.repository.get_user_by_email(email)

        if not user:
            raise NotFoundError("用户不存在")

        # 检查账号状态
        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "账号已被禁用")

        # 模拟模式：不验证密码，直接通过
        # 生产环境应替换为大网SSO/Keycloak认证
        
        permission_codes = self._get_permission_codes(user.role_ids)
        role_codes = self._get_role_codes(user.role_ids)

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
            'roleCodes': role_codes,
            'permissions': permission_codes,
            'permissionCodes': permission_codes
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
        role_codes = self._get_role_codes(user.role_ids)
        user_data = user.to_dict()
        user_data.update({
            'role_ids': user.role_ids or [],
            'roleCodes': role_codes,
            'permissions': permission_codes,
            'permissionCodes': permission_codes
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

    def get_user_menus(self, user_id: int) -> List[Dict]:
        """
        获取用户有权限的菜单列表（树形结构）
        Args:
            user_id: 用户ID
        Returns:
            菜单树形列表
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        # 获取用户权限编码列表
        permission_codes = self._get_permission_codes(user.role_ids)
        is_admin = 'ADMIN' in [r.code for r in Role.query.filter(
            Role.id.in_(user.role_ids or []), Role.valid == 1
        ).all() if r.code]

        # 获取所有有效菜单
        all_menus = Menu.query.filter(
            Menu.valid == 1,
            Menu.menu_type == 'MENU'
        ).order_by(Menu.sort.asc(), Menu.id.asc()).all()

        # 过滤用户有权限的菜单
        if is_admin:
            user_menus = all_menus
        else:
            user_menus = [
                m for m in all_menus
                if not m.permission_code or m.permission_code in permission_codes
            ]

        # 构建树形结构
        return self._build_menu_tree(user_menus)

    def _build_menu_tree(self, menus: List[Menu], parent_id: int = 0) -> List[Dict]:
        """构建菜单树"""
        tree = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = {
                    'id': menu.id,
                    'name': menu.name,
                    'titleI18nKey': menu.title_i18n_key,
                    'icon': menu.icon,
                    'path': menu.path,
                    'component': menu.component,
                    'hidden': menu.hidden == 1,
                    'permissionCode': menu.permission_code,
                    'sort': menu.sort,
                    'children': self._build_menu_tree(menus, menu.id)
                }
                tree.append(node)
        return tree


# 单例实例
auth_service = AuthService()

