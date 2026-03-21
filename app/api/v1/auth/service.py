"""
认证模块 - 业务逻辑层
职责：处理业务逻辑、调用Repository、事务管理
"""
import time
from typing import Optional, List, Dict, Any

import requests
from flask import current_app
from flask_jwt_extended import create_access_token

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
            permissions = Permission.query.filter(Permission.valid == 1).order_by(
                Permission.sort.asc(), Permission.id.asc()
            ).all()
            return [p.code for p in permissions]
        permission_ids = set()
        for role in roles:
            permission_ids.update(role.permission_ids or [])
        if not permission_ids:
            return []
        permissions = Permission.query.filter(
            Permission.id.in_(permission_ids), Permission.valid == 1
        ).order_by(Permission.sort.asc(), Permission.id.asc()).all()
        return [p.code for p in permissions]

    @staticmethod
    def _normalize_domain_account(domain_account: str) -> str:
        return (domain_account or '').strip().lower()

    @staticmethod
    def _normalize_user_name(user_name: Optional[str]) -> Optional[str]:
        if user_name is None:
            return None
        normalized = ''.join(str(user_name).split())
        return normalized or None

    @staticmethod
    def _is_success_payload(payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        if payload.get('success') is True:
            return True
        if payload.get('code') in (0, '0', 200, '200'):
            return True
        if payload.get('login_flag') in (1, '1', True, 'true', 'SUCCESS', 'success'):
            return True
        return False

    def get_login_mode(self) -> Dict[str, Any]:
        """获取登录模式配置"""
        sso_enabled = bool(current_app.config.get('AUTH_ENABLE_SSO', False))
        sso_login_url = current_app.config.get('AUTH_SSO_LOGIN_URL', '')
        redirect_uri = current_app.config.get('AUTH_SSO_REDIRECT_URI', '')
        if sso_enabled and sso_login_url and redirect_uri:
            joiner = '&' if '?' in sso_login_url else '?'
            sso_redirect_url = f"{sso_login_url}{joiner}redirect={redirect_uri}"
        else:
            sso_redirect_url = ''

        return {
            'sso_enabled': sso_enabled,
            'sso_redirect_url': sso_redirect_url,
            'uid_expire_seconds': int(current_app.config.get('AUTH_COMPANY_UID_EXPIRE_SECONDS', 1800)),
        }

    def _verify_password_by_company_api(self, domain_account: str, password: str) -> Dict[str, Any]:
        verify_url = current_app.config.get('AUTH_COMPANY_PASSWORD_VERIFY_URL', '')
        if not verify_url:
            if bool(current_app.config.get('AUTH_USE_FAKE_COMPANY_VERIFY', False)):
                return {
                    'domain_account': domain_account,
                    'user_name': domain_account,
                    'real_name': domain_account,
                    'email': f'{domain_account}@company.local',
                    'department': 'mock',
                }
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '未配置公司账号密码校验接口')

        timeout = float(current_app.config.get('AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT', 8.0))
        method = current_app.config.get('AUTH_COMPANY_PASSWORD_VERIFY_METHOD', 'POST').upper()
        payload = {'domain_account': domain_account, 'password': password}

        try:
            if method == 'GET':
                resp = requests.get(verify_url, params=payload, timeout=timeout)
            else:
                resp = requests.post(verify_url, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f'公司认证服务不可用: {exc}') from exc

        if resp.status_code >= 500:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, '公司认证服务异常')

        try:
            data = resp.json() if resp.text else {}
        except ValueError:
            data = {}

        if resp.status_code >= 400:
            msg = data.get('msg') or data.get('message') or '账号或密码错误'
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        if not self._is_success_payload(data):
            msg = data.get('msg') or data.get('message') or '账号或密码错误'
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        user_info = data.get('data') if isinstance(data.get('data'), dict) else data
        return user_info if isinstance(user_info, dict) else {}

    def _fetch_user_info_by_uid(self, uid: str, cookies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        info_url = current_app.config.get('AUTH_COMPANY_UID_INFO_URL', '')
        app_id = current_app.config.get('AUTH_COMPANY_APP_ID', '')
        secret_credit = current_app.config.get('AUTH_COMPANY_SECRET_CREDIT', '')
        if not info_url:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '未配置公司SSO用户信息接口')
        if not app_id or not secret_credit:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '未配置公司SSO凭证(appid/secret-credit)')

        timeout = float(current_app.config.get('AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT', 8.0))
        headers = {
            'X-App-Id': app_id,
            'X-Secret-Credit': secret_credit,
        }

        try:
            resp = requests.get(
                info_url,
                params={'uid': uid},
                headers=headers,
                timeout=timeout,
                cookies=cookies,
            )
        except requests.RequestException as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f'SSO用户信息查询失败: {exc}') from exc

        try:
            data = resp.json() if resp.text else {}
        except ValueError:
            data = {}

        if resp.status_code >= 400 or not self._is_success_payload(data):
            msg = data.get('msg') or data.get('message') or 'SSO用户信息校验失败'
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        user_info = data.get('data') if isinstance(data.get('data'), dict) else data
        return user_info if isinstance(user_info, dict) else {}

    def _build_user_payload(self, domain_account: str, info: Dict[str, Any]) -> Dict[str, Any]:
        normalized_domain = self._normalize_domain_account(
            str(info.get('domain_account') or info.get('domainAccount') or domain_account)
        )
        user_name_raw = info.get('user_name') or info.get('userName')
        user_name = self._normalize_user_name(user_name_raw)
        real_name = info.get('real_name') or info.get('realName') or info.get('name') or normalized_domain
        email = info.get('email') or f'{normalized_domain}@company.local'
        department = info.get('department')
        lc_user_id = info.get('lc_user_id') or info.get('lcUserId') or info.get('user_id') or info.get('userId')

        name = info.get('name') or real_name

        return {
            'domain_account': normalized_domain,
            'lc_user_id': str(lc_user_id).strip() if lc_user_id is not None and str(lc_user_id).strip() else None,
            'user_name': str(user_name) if user_name else None,
            'real_name': str(real_name) if real_name else normalized_domain,
            'email': str(email),
            'username': normalized_domain,
            'name': str(name),
            'department': department,
            'valid': 1,
        }

    def _issue_login_result(self, user) -> Dict[str, Any]:
        permission_codes = self._get_permission_codes(user.role_ids)
        role_codes = self._get_role_codes(user.role_ids)

        access_token = create_access_token(
            identity=str(user.domain_account),
            additional_claims={'permissions': permission_codes},
        )

        self.repository.update_last_login(user, int(time.time()))

        user_data = user.to_dict()
        user_data.update({
            'id': user.domain_account,
            'db_id': user.id,
            'user_id': user.lc_user_id,
            'role_ids': user.role_ids or [],
            'roleCodes': role_codes,
            'permissions': permission_codes,
            'permissionCodes': permission_codes,
        })

        return {'token': access_token, 'user': user_data}

    def login(self, domain_account: str, password: str) -> Dict[str, Any]:
        """域账号 + 密码登录（密码只透传公司接口，不入库）"""
        login_mode = self.get_login_mode()
        if login_mode.get('sso_enabled'):
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '当前已启用SSO，请走SSO登录')

        normalized_domain = self._normalize_domain_account(domain_account)
        info = self._verify_password_by_company_api(normalized_domain, password)
        payload = self._build_user_payload(normalized_domain, info)

        user = self.repository.get_user_by_domain_account(payload['domain_account'])
        if not user and payload.get('lc_user_id'):
            user = self.repository.get_user_by_lc_user_id(payload['lc_user_id'])
            if user and user.domain_account != payload['domain_account']:
                user.domain_account = payload['domain_account']

        if not user:
            legacy = self.repository.get_user_by_email(payload['email'])
            if legacy and not legacy.domain_account:
                legacy.domain_account = payload['domain_account']
                legacy.lc_user_id = payload.get('lc_user_id')
                legacy.user_name = payload['user_name']
                legacy.real_name = payload['real_name']
                legacy.name = payload['name']
                legacy.username = payload['domain_account']
                legacy.department = payload['department']
                legacy.valid = 1
                user = legacy
                self.repository.update_last_login(user, int(time.time()))
            else:
                user = self.repository.upsert_user_by_domain_account(payload['domain_account'], payload)
        else:
            user = self.repository.upsert_user_by_domain_account(payload['domain_account'], payload)

        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '账号已被禁用')

        return self._issue_login_result(user)

    def login_by_uid(self, uid: str, cookie_dict: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """SSO回调：必须通过uid查询公司接口获取域账号与用户信息后登录"""
        if not uid:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '缺少uid')

        info = self._fetch_user_info_by_uid(uid, cookie_dict)
        domain_account = self._normalize_domain_account(
            str(info.get('domain_account') or info.get('domainAccount') or '')
        )
        if not domain_account:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '公司接口未返回域账号，无法登录')

        payload = self._build_user_payload(domain_account, info)
        if payload.get('lc_user_id'):
            existing = self.repository.get_user_by_lc_user_id(payload['lc_user_id'])
            if existing and existing.domain_account != payload['domain_account']:
                existing.domain_account = payload['domain_account']
        user = self.repository.upsert_user_by_domain_account(payload['domain_account'], payload)

        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, '账号已被禁用')

        return self._issue_login_result(user)

    def _resolve_user_by_identity(self, user_identity: Any):
        """根据JWT identity解析用户（优先域账号，兼容老token的数据库ID）"""
        if user_identity is None:
            return None

        if isinstance(user_identity, (int, float)):
            return self.repository.get_user_by_id(int(user_identity))

        identity_str = str(user_identity).strip()
        if not identity_str:
            return None

        user = self.repository.get_user_by_domain_account(self._normalize_domain_account(identity_str))
        if user:
            return user

        if identity_str.isdigit():
            return self.repository.get_user_by_id(int(identity_str))

        return None

    def get_current_user(self, user_identity: Any) -> Dict:
        """获取当前用户信息"""
        user = self._resolve_user_by_identity(user_identity)

        if not user:
            raise NotFoundError("用户不存在")

        permission_codes = self._get_permission_codes(user.role_ids)
        role_codes = self._get_role_codes(user.role_ids)
        user_data = user.to_dict()
        user_data.update({
            'id': user.domain_account,
            'db_id': user.id,
            'user_id': user.lc_user_id,
            'role_ids': user.role_ids or [],
            'roleCodes': role_codes,
            'permissions': permission_codes,
            'permissionCodes': permission_codes,
        })

        return user_data

    def get_all_users(self) -> List[Dict]:
        """获取所有用户列表"""
        users = self.repository.get_all_valid_users()
        return [user.to_public_dict() for user in users]

    def logout(self, user_identity: Any) -> Dict:
        """用户登出"""
        return {'message': '登出成功'}

    def get_user_menus(self, user_identity: Any) -> List[Dict]:
        """获取用户有权限的菜单列表（树形结构）"""
        user = self._resolve_user_by_identity(user_identity)
        if not user:
            raise NotFoundError("用户不存在")

        permission_codes = self._get_permission_codes(user.role_ids)
        is_admin = 'ADMIN' in [
            r.code for r in Role.query.filter(Role.id.in_(user.role_ids or []), Role.valid == 1).all() if r.code
        ]

        all_menus = Menu.query.filter(
            Menu.valid == 1,
            Menu.menu_type == 'MENU'
        ).order_by(Menu.sort.asc(), Menu.id.asc()).all()

        if is_admin:
            user_menus = all_menus
        else:
            user_menus = [m for m in all_menus if not m.permission_code or m.permission_code in permission_codes]

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
                    'children': self._build_menu_tree(menus, menu.id),
                }
                tree.append(node)
        return tree


# 单例实例
auth_service = AuthService()
