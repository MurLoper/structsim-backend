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
from app.models.config import Department
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
    def _resolve_department_id(
        department_id: Any = None,
        department_name: Optional[str] = None,
    ) -> Optional[int]:
        if department_id not in (None, ""):
            try:
                resolved_id = int(department_id)
            except (TypeError, ValueError):
                resolved_id = None
            if resolved_id:
                department = Department.query.filter(
                    Department.id == resolved_id, Department.valid == 1
                ).first()
                if department:
                    return department.id

        normalized_name = str(department_name or "").strip()
        if not normalized_name:
            return None

        department = Department.query.filter(
            Department.valid == 1,
            (Department.name == normalized_name) | (Department.code == normalized_name),
        ).first()
        return department.id if department else None

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
        if payload.get("success_flag") in (1, "1", True, "true", "TRUE", "success", "SUCCESS"):
            return True
        return False

    @staticmethod
    def _serialize_user(user: User, roles: List[Role], permission_codes: List[str]) -> Dict[str, Any]:
        limits = AuthService._merge_role_limits(roles)
        role_ids = list(user.role_ids or [])
        department_name = user.department_name
        return {
            "id": user.domain_account,
            "domainAccount": user.domain_account,
            "lcUserId": user.lc_user_id,
            "userName": user.user_name,
            "realName": user.real_name,
            "email": user.email,
            "avatar": user.avatar,
            "phone": user.phone,
            "departmentId": user.department_id,
            "department": department_name,
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
            "recentProjectIds": list(user.recent_project_ids or []),
            "recentSimTypeIds": list(user.recent_sim_type_ids or []),
            "valid": user.valid,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
            "lastLoginAt": user.last_login_at,
        }

    def get_login_mode(self) -> Dict[str, Any]:
        sso_enabled = bool(current_app.config.get("AUTH_ENABLE_SSO", False))
        sso_login_url = current_app.config.get("AUTH_SSO_LOGIN_URL", "")
        redirect_uri = current_app.config.get("AUTH_SSO_REDIRECT_URI", "")
        test_account_bypass_enabled = bool(
            current_app.config.get("AUTH_ALLOW_TEST_ACCOUNT_BYPASS", False)
        )
        if sso_enabled and sso_login_url and redirect_uri:
            joiner = "&" if "?" in sso_login_url else "?"
            sso_redirect_url = f"{sso_login_url}{joiner}redirect={redirect_uri}"
        else:
            sso_redirect_url = ""

        return {
            "sso_enabled": sso_enabled,
            "sso_redirect_url": sso_redirect_url,
            "test_account_bypass_enabled": test_account_bypass_enabled,
            "uid_expire_seconds": int(
                current_app.config.get("AUTH_COMPANY_UID_EXPIRE_SECONDS", 1800)
            ),
        }

    def _is_test_account_bypass_allowed(self, domain_account: str) -> bool:
        if not bool(current_app.config.get("AUTH_ALLOW_TEST_ACCOUNT_BYPASS", False)):
            return False
        allowlist = current_app.config.get("AUTH_TEST_BYPASS_USERS", []) or []
        normalized_domain = self._normalize_domain_account(domain_account)
        return normalized_domain in set(allowlist)

    def _login_by_existing_db_user(self, domain_account: str) -> Dict[str, Any]:
        normalized_domain = self._normalize_domain_account(domain_account)
        user = self.repository.get_user_by_domain_account(normalized_domain)
        if not user:
            raise BusinessError(
                ErrorCode.VALIDATION_ERROR,
                "测试账号直登已开启，但该账号不在当前数据库中",
            )
        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "账号已被禁用")
        return self._issue_login_result(user)

    def _get_or_create_default_role(self) -> Role:
        role_code = str(current_app.config.get("AUTH_DEFAULT_ROLE_CODE") or "GUEST").strip() or "GUEST"
        role = self.repository.get_role_by_code(role_code)
        if role:
            return role

        permission_codes = [
            "VIEW_DASHBOARD",
            "VIEW_RESULTS",
            "CREATE_ORDER",
            "ORDER_VIEW",
            "ORDER_CREATE",
        ]
        permissions = self.repository.get_permissions_by_codes(permission_codes)
        role = self.repository.create_role(
            {
                "name": "游客",
                "code": role_code,
                "description": "系统自动分配的默认访客角色",
                "permission_ids": [item.id for item in permissions],
                "valid": 1,
                "sort": 900,
            }
        )
        return role

    def _verify_password_by_company_api(self, domain_account: str, password: str) -> Dict[str, Any]:
        verify_url = current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_URL", "")
        if not verify_url:
            if bool(current_app.config.get("AUTH_USE_FAKE_COMPANY_VERIFY", False)):
                return {"success": True, "domain_account": domain_account}
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司账号密码校验接口")

        timeout = float(current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT", 8.0))
        method = current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_METHOD", "POST").upper()
        payload = {"domain_account": domain_account, "password": password}
        headers = self._get_company_api_headers()

        try:
            if method == "GET":
                response = requests.get(verify_url, params=payload, headers=headers, timeout=timeout)
            else:
                response = requests.post(verify_url, json=payload, headers=headers, timeout=timeout)
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

        verify_info = data.get("data") if isinstance(data.get("data"), dict) else data
        return verify_info if isinstance(verify_info, dict) else {}

    def _get_company_api_headers(self) -> Dict[str, str]:
        app_id = current_app.config.get("AUTH_COMPANY_APP_ID", "")
        secret_credit = current_app.config.get("AUTH_COMPANY_SECRET_CREDIT", "")
        headers: Dict[str, str] = {}
        if app_id:
            headers["X-App-Id"] = app_id
        if secret_credit:
            headers["X-Secret-Credit"] = secret_credit
        return headers

    @staticmethod
    def _extract_company_access_token(payload: Optional[Dict[str, Any]]) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        candidates = [
            payload.get("access_token"),
            payload.get("accessToken"),
            payload.get("token"),
        ]
        auth_data = payload.get("auth") if isinstance(payload.get("auth"), dict) else None
        if auth_data:
            candidates.extend(
                [
                    auth_data.get("access_token"),
                    auth_data.get("accessToken"),
                    auth_data.get("token"),
                ]
            )

        for item in candidates:
            value = str(item or "").strip()
            if value:
                return value
        return None

    def _fetch_user_info_by_domain_account(
        self,
        domain_account: str,
        access_token: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        info_url = current_app.config.get("AUTH_GET_USER_INFO_URL", "")
        if not info_url:
            if bool(current_app.config.get("AUTH_USE_FAKE_COMPANY_VERIFY", False)):
                return {
                    "domain_account": domain_account,
                    "user_name": domain_account,
                    "real_name": domain_account,
                    "email": f"{domain_account}@company.local",
                    "department": "mock",
                    "department_id": self._resolve_department_id(department_name="mock"),
                }
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司用户信息接口")

        timeout = float(current_app.config.get("AUTH_GET_USER_INFO_TIMEOUT", 8.0))
        method = current_app.config.get("AUTH_GET_USER_INFO_METHOD", "GET").upper()
        headers = self._get_company_api_headers()
        payload = {"domain_account": domain_account}
        normalized_access_token = str(access_token or "").strip()
        if normalized_access_token:
            payload["access_token"] = normalized_access_token
            payload["token"] = normalized_access_token
            headers["Authorization"] = f"Bearer {normalized_access_token}"

        try:
            if method == "POST":
                response = requests.post(
                    info_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                    cookies=cookies,
                )
            else:
                response = requests.get(
                    info_url,
                    params=payload,
                    headers=headers,
                    timeout=timeout,
                    cookies=cookies,
                )
        except requests.RequestException as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f"公司用户信息服务不可用: {exc}") from exc

        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {}

        if response.status_code >= 400 or not self._is_success_payload(data):
            msg = data.get("msg") or data.get("message") or "公司用户信息查询失败"
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        user_info = data.get("data") if isinstance(data.get("data"), dict) else data
        return user_info if isinstance(user_info, dict) else {}

    def _fetch_user_info_by_uid(
        self, uid: str, cookies: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        info_url = current_app.config.get("AUTH_COMPANY_UID_INFO_URL", "")
        if not info_url:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司 SSO 用户信息接口")
        headers = self._get_company_api_headers()
        if not headers.get("X-App-Id") or not headers.get("X-Secret-Credit"):
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "未配置公司 SSO 凭证(appid/secret-credit)")

        timeout = float(current_app.config.get("AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT", 8.0))

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
        user_name = self._normalize_user_name(
            info.get("user_name") or info.get("userName") or info.get("userNameEn")
        )
        real_name = (
            info.get("real_name")
            or info.get("realName")
            or info.get("realname")
            or info.get("name")
            or user_name
            or normalized_domain
        )
        email = info.get("email") or f"{normalized_domain}@company.local"
        department_name = info.get("department") or info.get("departmentName")
        department_id = self._resolve_department_id(
            department_id=info.get("department_id") or info.get("departmentId"),
            department_name=department_name,
        )
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
            "department_id": department_id,
            "valid": 1,
        }

    def _fetch_user_info_by_access_token(
        self,
        access_token: str,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        normalized_token = str(access_token or "").strip()
        if not normalized_token:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "缺少 opt_access_token")

        info_url = current_app.config.get("AUTH_GET_USER_INFO_URL", "")
        if not info_url:
            domain_account = self._normalize_domain_account(
                str(
                    (cookies or {}).get("domain_account")
                    or (cookies or {}).get("user_account")
                    or (cookies or {}).get("user_name")
                    or "embed_mock_user"
                )
            )
            return {
                "domain_account": domain_account,
                "user_account": domain_account,
                "user_name": (cookies or {}).get("user_name") or domain_account,
                "real_name": (cookies or {}).get("real_name")
                or (cookies or {}).get("user_name")
                or domain_account,
                "email": f"{domain_account}@company.local",
                "department": "mock",
                "department_id": self._resolve_department_id(department_name="mock"),
            }

        timeout = float(current_app.config.get("AUTH_GET_USER_INFO_TIMEOUT", 8.0))
        method = current_app.config.get("AUTH_GET_USER_INFO_METHOD", "GET").upper()
        headers = self._get_company_api_headers()
        headers["Authorization"] = f"Bearer {normalized_token}"
        payload = {"token": normalized_token}

        try:
            if method == "POST":
                response = requests.post(
                    info_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                    cookies=cookies,
                )
            else:
                response = requests.get(
                    info_url,
                    params=payload,
                    headers=headers,
                    timeout=timeout,
                    cookies=cookies,
                )
        except requests.RequestException as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f"公司用户信息服务不可用: {exc}") from exc

        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {}

        if response.status_code >= 400 or not self._is_success_payload(data):
            msg = (
                data.get("error_msg")
                or data.get("success_msg")
                or data.get("msg")
                or data.get("message")
                or "公司用户信息查询失败"
            )
            raise BusinessError(ErrorCode.VALIDATION_ERROR, msg)

        user_info = data.get("data") if isinstance(data.get("data"), dict) else data
        return user_info if isinstance(user_info, dict) else {}

    def _assign_default_role_if_missing(self, user_payload: Dict[str, Any], user: Optional[User] = None) -> Dict[str, Any]:
        existing_role_ids = list((user.role_ids if user else None) or [])
        if existing_role_ids:
            user_payload["role_ids"] = existing_role_ids
            return user_payload

        incoming_role_ids = list(user_payload.get("role_ids") or [])
        if incoming_role_ids:
            return user_payload

        default_role = self._get_or_create_default_role()
        user_payload["role_ids"] = [default_role.id]
        return user_payload

    def _upsert_authenticated_user(self, payload: Dict[str, Any]) -> User:
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
                legacy.department_id = payload.get("department_id")
                legacy.valid = 1
                normalized_payload = self._assign_default_role_if_missing(payload, legacy)
                legacy.role_ids = normalized_payload.get("role_ids")
                self.repository.update_last_login(legacy, int(time.time()))
                return legacy

        normalized_payload = self._assign_default_role_if_missing(payload, user)
        return self.repository.upsert_user_by_domain_account(
            normalized_payload["domain_account"], normalized_payload
        )

    def _issue_login_result(self, user: User) -> Dict[str, Any]:
        permission_codes = self._get_permission_codes(user.role_ids)
        access_token = create_access_token(
            identity=str(user.domain_account),
            additional_claims={"permissions": permission_codes},
        )
        self.repository.update_last_login(user, int(time.time()))
        return {"token": access_token}

    def login(self, domain_account: str, password: str) -> Dict[str, Any]:
        login_mode = self.get_login_mode()
        if login_mode.get("sso_enabled"):
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "当前已启用 SSO，请走 SSO 登录")

        normalized_domain = self._normalize_domain_account(domain_account)
        if self._is_test_account_bypass_allowed(normalized_domain):
            return self._login_by_existing_db_user(normalized_domain)

        verify_info = self._verify_password_by_company_api(normalized_domain, password)
        company_access_token = self._extract_company_access_token(verify_info)
        if current_app.config.get("AUTH_GET_USER_INFO_URL"):
            info = self._fetch_user_info_by_domain_account(
                normalized_domain,
                access_token=company_access_token,
            )
        else:
            info = verify_info
        payload = self._build_user_payload(normalized_domain, info)
        user = self._upsert_authenticated_user(payload)

        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "账号已被禁用")

        return self._issue_login_result(user)

    def login_by_uid(
        self, uid: str, cookie_dict: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        if not uid:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "缺少 uid")

        uid_info = self._fetch_user_info_by_uid(uid, cookie_dict)
        domain_account = self._normalize_domain_account(
            str(uid_info.get("domain_account") or uid_info.get("domainAccount") or "")
        )
        if not domain_account:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "公司接口未返回域账号，无法登录")

        info = uid_info
        if current_app.config.get("AUTH_GET_USER_INFO_URL"):
            detail_info = self._fetch_user_info_by_domain_account(
                domain_account,
                access_token=self._extract_company_access_token(uid_info),
                cookies=cookie_dict,
            )
            info = {**uid_info, **detail_info}
        payload = self._build_user_payload(domain_account, info)
        user = self._upsert_authenticated_user(payload)

        if user.valid != 1:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "账号已被禁用")

        return self._issue_login_result(user)

    def login_by_opt_access_token(
        self,
        access_token: str,
        cookie_dict: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        user_info = self._fetch_user_info_by_access_token(access_token, cookie_dict)
        domain_account = self._normalize_domain_account(
            str(
                user_info.get("domain_account")
                or user_info.get("domainAccount")
                or user_info.get("user_account")
                or user_info.get("userAccount")
                or (cookie_dict or {}).get("domain_account")
                or (cookie_dict or {}).get("user_account")
                or ""
            )
        )
        if not domain_account:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "公司接口未返回域账号，无法登录")

        payload = self._build_user_payload(domain_account, user_info)
        user = self._upsert_authenticated_user(payload)
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

    def get_current_session(self, user_identity: Any) -> Dict[str, Any]:
        user = self.get_current_user(user_identity)
        menus = self.get_user_menus(user_identity)
        try:
            from app.api.v1.orders.service import orders_service

            submit_limits = orders_service.get_submit_limits(str(user.get("domainAccount") or ""))
        except Exception:
            submit_limits = {}

        if submit_limits:
            user = {
                **user,
                "maxBatchSize": submit_limits.get("max_batch_size", user.get("maxBatchSize")),
                "maxCpuCores": submit_limits.get("max_cpu_cores", user.get("maxCpuCores")),
                "dailyRoundLimitDefault": submit_limits.get(
                    "daily_round_limit_default", user.get("dailyRoundLimitDefault")
                ),
                "dailyRoundLimit": submit_limits.get("daily_round_limit", user.get("dailyRoundLimit")),
                "todayUsedRounds": submit_limits.get("today_used_rounds", 0),
                "todayRemainingRounds": submit_limits.get("today_remaining_rounds", 0),
            }
        return {"user": user, "menus": menus}

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
