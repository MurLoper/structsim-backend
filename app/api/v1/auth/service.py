"""
认证业务服务。

统一使用 `domain_account` 作为业务主键和 JWT identity。
"""
import time
from typing import Any, Dict, List, Optional

import requests
from flask import current_app
from flask_jwt_extended import create_access_token

from app.common.errors import BusinessError, NotFoundError
from app.constants import ErrorCode
from app.models.auth import Menu, Permission, Role, User
from .repository import auth_repository


class AuthService:
    def __init__(self):
        self.repository = auth_repository

    def _get_valid_roles(self, role_ids: Optional[List[int]]) -> List[Role]:
        ids = list(role_ids or [])
        if not ids:
            return []
        return Role.query.filter(Role.id.in_(ids), Role.valid == 1).all()

    def _get_permission_codes(self, role_ids: Optional[List[int]]) -> List[str]:
        roles = self._get_valid_roles(role_ids)
        if not roles:
            return []
        if any(role.code == "ADMIN" for role in roles if role.code):
            permissions = (
                Permission.query.filter(Permission.valid == 1)
                .order_by(Permission.sort.asc(), Permission.id.asc())
                .all()
            )
            return [item.code for item in permissions]

        permission_ids: set[int] = set()
        for role in roles:
            permission_ids.update(role.permission_ids or [])
        if not permission_ids:
            return []
        permissions = (
            Permission.query.filter(Permission.id.in_(permission_ids), Permission.valid == 1)
            .order_by(Permission.sort.asc(), Permission.id.asc())
            .all()
        )
        return [item.code for item in permissions]

    @staticmethod
    def _merge_role_limits(roles: List[Role]) -> Dict[str, Any]:
        max_cpu_cores: Optional[int] = None
        max_batch_size: Optional[int] = None
        daily_round_limit_default: Optional[int] = None
        node_values: set[int] = set()

        for role in roles:
            if isinstance(role.max_cpu_cores, int) and role.max_cpu_cores > 0:
                max_cpu_cores = max(max_cpu_cores or 0, role.max_cpu_cores)
            if isinstance(role.max_batch_size, int) and role.max_batch_size > 0:
                max_batch_size = max(max_batch_size or 0, role.max_batch_size)
            if (
                isinstance(role.daily_round_limit_default, int)
                and role.daily_round_limit_default > 0
            ):
                daily_round_limit_default = max(
                    daily_round_limit_default or 0, role.daily_round_limit_default
                )
            for node in role.node_list or []:
                try:
                    node_values.add(int(node))
                except (TypeError, ValueError):
                    continue

        return {
            "maxCpuCores": max_cpu_cores or 192,
            "maxBatchSize": max_batch_size or 200,
            "dailyRoundLimitDefault": daily_round_limit_default or 500,
            "nodeList": sorted(node_values),
        }

    @staticmethod
    def _resolve_effective_daily_round_limit(
        user_daily_round_limit: Any, role_daily_round_limit_default: int
    ) -> int:
        if isinstance(user_daily_round_limit, int) and user_daily_round_limit > 0:
            return user_daily_round_limit
        return int(role_daily_round_limit_default or 500)

    @staticmethod
    def _normalize_domain_account(domain_account: str) -> str:
        return (domain_account or "").strip().lower()

    @staticmethod
    def _normalize_user_name(user_name: Optional[str]) -> Optional[str]:
        if user_name is None:
            return None
        normalized = "".join(str(user_name).split())
        return normalized or None

    @staticmethod
    def _is_success_payload(payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        if payload.get("success") is True:
            return True
        if payload.get("code") in (0, "0", 200, "200"):
            return True
        if payload.get("login_flag") in (1, "1", True, "true", "SUCCESS", "success"):
            return True
        return False

    @staticmethod
    def _serialize_user(user: User, roles: List[Role], permission_codes: List[str]) -> Dict[str, Any]:
        limits = AuthService._merge_role_limits(roles)
        role_ids = list(user.role_ids or [])
        return {
            "id": user.domain_account,
            "domainAccount": user.domain_account,
            "lcUserId": user.lc_user_id,
            "userName": user.user_name,
            "realName": user.real_name,
            "email": user.email,
            "avatar": user.avatar,
            "phone": user.phone,
            "department": user.department,
            "roleIds": role_ids,
            "roleIdList": role_ids,
            "roleCodes": [role.code for role in roles if role.code],
            "permissions": permission_codes,
            "permissionCodes": permission_codes,
            "maxCpuCores": limits["maxCpuCores"],
            "maxBatchSize": limits["maxBatchSize"],
            "nodeList": limits["nodeList"],
            "dailyRoundLimitDefault": limits["dailyRoundLimitDefault"],
            "dailyRoundLimit": AuthService._resolve_effective_daily_round_limit(
                user.daily_round_limit, limits["dailyRoundLimitDefault"]
            ),
            "valid": user.valid,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
            "lastLoginAt": user.last_login_at,
        }

    def get_login_mode(self) -> Dict[str, Any]:
        sso_enabled = bool(current_app.config.get("AUTH_ENABLE_SSO", False))
        sso_login_url = current_app.config.get("AUTH_SSO_LOGIN_URL", "")
        redirect_uri = current_app.config.get("AUTH_SSO_REDIRECT_URI", "")
        if sso_enabled and sso_login_url and redirect_uri:
            joiner = "&" if "?" in sso_login_url else "?"
            sso_redirect_url = f"{sso_login_url}{joiner}redirect={redirect_uri}"
        else:
            sso_redirect_url = ""

        return {
            "sso_enabled": sso_enabled,
            "sso_redirect_url": sso_redirect_url,
            "uid_expire_seconds": int(
                current_app.config.get("AUTH_COMPANY_UID_EXPIRE_SECONDS", 1800)
            ),
        }

    def _verify_password_by_company_api(self, domain_account: str, password: str) -> Dict[str, Any]:
        verify_url = current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_URL", "")
        if not verify_url:
            if bool(current_app.config.get("AUTH_USE_FAKE_COMPANY_VERIFY", False)):
                return {
                    "domain_account": domain_account,
                    "user_name": domain_account,
                    "real_name": domain_account,
                    "email": f"{domain_account}@company.local",
                    "department": "mock",
                }
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司账号密码校验接口")

        timeout = float(current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT", 8.0))
        method = current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_METHOD", "POST").upper()
        payload = {"domain_account": domain_account, "password": password}

        try:
            if method == "GET":
                response = requests.get(verify_url, params=payload, timeout=timeout)
            else:
                response = requests.post(verify_url, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f"公司认证服务不可用: {exc}") from exc

        if response.status_code >= 500:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, "公司认证服务异常")

        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {}

        if response.status_code >= 400 or not self._is_success_payload(data):
            msg = data.get("msg") or data.get("message") or "账号或密码错误"
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        user_info = data.get("data") if isinstance(data.get("data"), dict) else data
        return user_info if isinstance(user_info, dict) else {}

    def _fetch_user_info_by_uid(
        self, uid: str, cookies: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        info_url = current_app.config.get("AUTH_COMPANY_UID_INFO_URL", "")
        app_id = current_app.config.get("AUTH_COMPANY_APP_ID", "")
        secret_credit = current_app.config.get("AUTH_COMPANY_SECRET_CREDIT", "")
        if not info_url:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司 SSO 用户信息接口")
        if not app_id or not secret_credit:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司 SSO 凭证(appid/secret-credit)")

        timeout = float(current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT", 8.0))
        headers = {"X-App-Id": app_id, "X-Secret-Credit": secret_credit}

        try:
            response = requests.get(
                info_url,
                params={"uid": uid},
                headers=headers,
                timeout=timeout,
                cookies=cookies,
            )
        except requests.RequestException as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f"SSO 用户信息查询失败: {exc}") from exc

        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {}

        if response.status_code >= 400 or not self._is_success_payload(data):
            msg = data.get("msg") or data.get("message") or "SSO 用户信息校验失败"
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        user_info = data.get("data") if isinstance(data.get("data"), dict) else data
        return user_info if isinstance(user_info, dict) else {}

    def _build_user_payload(self, domain_account: str, info: Dict[str, Any]) -> Dict[str, Any]:
        normalized_domain = self._normalize_domain_account(
            str(info.get("domain_account") or info.get("domainAccount") or domain_account)
        )
        user_name = self._normalize_user_name(info.get("user_name") or info.get("userName"))
        real_name = (
            info.get("real_name")
            or info.get("realName")
            or info.get("name")
            or user_name
            or normalized_domain
        )
        email = info.get("email") or f"{normalized_domain}@company.local"
        department = info.get("department")
        lc_user_id = (
            info.get("lc_user_id")
            or info.get("lcUserId")
            or info.get("user_id")
            or info.get("userId")
        )

        return {
            "domain_account": normalized_domain,
            "lc_user_id": str(lc_user_id).strip()
            if lc_user_id is not None and str(lc_user_id).strip()
            else None,
            "user_name": str(user_name) if user_name else None,
            "real_name": str(real_name) if real_name else normalized_domain,
            "email": str(email),
            "department": department,
            "valid": 1,
        }

    def _issue_login_result(self, user: User) -> Dict[str, Any]:
        roles = self._get_valid_roles(user.role_ids)
        permission_codes = self._get_permission_codes(user.role_ids)
        access_token = create_access_token(
            identity=str(user.domain_account),
            additional_claims={"permissions": permission_codes},
        )
        self.repository.update_last_login(user, int(time.time()))
        return {"token": access_token, "user": self._serialize_user(user, roles, permission_codes)}

    def login(self, domain_account: str, password: str) -> Dict[str, Any]:
        login_mode = self.get_login_mode()
        if login_mode.get("sso_enabled"):
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "当前已启用 SSO，请走 SSO 登录")

        normalized_domain = self._normalize_domain_account(domain_account)
        info = self._verify_password_by_company_api(normalized_domain, password)
        payload = self._build_user_payload(normalized_domain, info)

        user = self.repository.get_user_by_domain_account(payload["domain_account"])
        if not user and payload.get("lc_user_id"):
            user = self.repository.get_user_by_lc_user_id(payload["lc_user_id"])
            if user and user.domain_account != payload["domain_account"]:
                user.domain_account = payload["domain_account"]

        if not user:
            legacy = self.repository.get_user_by_email(payload["email"])
            if legacy and not legacy.domain_account:
                legacy.domain_account = payload["domain_account"]
                legacy.lc_user_id = payload.get("lc_user_id")
                legacy.user_name = payload["user_name"]
                legacy.real_name = payload["real_name"]
                legacy.department = payload["department"]
                legacy.valid = 1
                user = legacy
                self.repository.update_last_login(user, int(time.time()))
            else:
                user = self.repository.upsert_user_by_domain_account(
                    payload["domain_account"], payload
                )
        else:
            user = self.repository.upsert_user_by_domain_account(payload["domain_account"], payload)

        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "账号已被禁用")

        return self._issue_login_result(user)

    def login_by_uid(
        self, uid: str, cookie_dict: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        if not uid:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "缺少 uid")

        info = self._fetch_user_info_by_uid(uid, cookie_dict)
        domain_account = self._normalize_domain_account(
            str(info.get("domain_account") or info.get("domainAccount") or "")
        )
        if not domain_account:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "公司接口未返回域账号，无法登录")

        payload = self._build_user_payload(domain_account, info)
        if payload.get("lc_user_id"):
            existing = self.repository.get_user_by_lc_user_id(payload["lc_user_id"])
            if existing and existing.domain_account != payload["domain_account"]:
                existing.domain_account = payload["domain_account"]
        user = self.repository.upsert_user_by_domain_account(payload["domain_account"], payload)

        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "账号已被禁用")

        return self._issue_login_result(user)

    def _resolve_user_by_identity(self, user_identity: Any):
        if user_identity is None:
            return None
        if isinstance(user_identity, (int, float)):
            return self.repository.get_user_by_id(int(user_identity))

        identity_str = str(user_identity).strip()
        if not identity_str:
            return None

        user = self.repository.get_user_by_domain_account(
            self._normalize_domain_account(identity_str)
        )
        if user:
            return user
        if identity_str.isdigit():
            return self.repository.get_user_by_id(int(identity_str))
        return None

    def get_current_user(self, user_identity: Any) -> Dict[str, Any]:
        user = self._resolve_user_by_identity(user_identity)
        if not user:
            raise NotFoundError("用户不存在")

        roles = self._get_valid_roles(user.role_ids)
        permission_codes = self._get_permission_codes(user.role_ids)
        return self._serialize_user(user, roles, permission_codes)

    def get_all_users(self) -> List[Dict[str, Any]]:
        users = self.repository.get_all_valid_users()
        return [user.to_public_dict() for user in users]

    def logout(self, user_identity: Any) -> Dict[str, Any]:
        return {"message": "登出成功"}

    def get_user_menus(self, user_identity: Any) -> List[Dict[str, Any]]:
        user = self._resolve_user_by_identity(user_identity)
        if not user:
            raise NotFoundError("用户不存在")

        permission_codes = self._get_permission_codes(user.role_ids)
        is_admin = "ADMIN" in [role.code for role in self._get_valid_roles(user.role_ids) if role.code]

        all_menus = (
            Menu.query.filter(Menu.valid == 1, Menu.menu_type == "MENU")
            .order_by(Menu.sort.asc(), Menu.id.asc())
            .all()
        )

        if is_admin:
            user_menus = all_menus
        else:
            user_menus = [
                menu
                for menu in all_menus
                if not menu.permission_code or menu.permission_code in permission_codes
            ]

        return self._build_menu_tree(user_menus)

    def _build_menu_tree(self, menus: List[Menu], parent_id: int = 0) -> List[Dict[str, Any]]:
        tree: List[Dict[str, Any]] = []
        for menu in menus:
            if menu.parent_id != parent_id:
                continue
            node = {
                "id": menu.id,
                "name": menu.name,
                "titleI18nKey": menu.title_i18n_key,
                "icon": menu.icon,
                "path": menu.path,
                "component": menu.component,
                "hidden": menu.hidden == 1,
                "permissionCode": menu.permission_code,
                "sort": menu.sort,
                "children": self._build_menu_tree(menus, menu.id),
            }
            tree.append(node)
        return tree


auth_service = AuthService()
