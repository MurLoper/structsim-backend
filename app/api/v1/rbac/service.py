"""
RBAC 业务层。
"""
from typing import Dict, List, Optional

from app.common.errors import BusinessError, NotFoundError
from app.constants import ErrorCode
from app.extensions import db
from app.models.auth import Menu, Permission, Role, User
from app.models.config import Department
from .repository import (
    menu_repository,
    permission_repository,
    role_repository,
    user_repository,
)

ADMIN_EMAIL = "alice@sim.com"


def _normalize_user_payload(data: dict) -> dict:
    payload = dict(data)
    if "roleIds" in payload:
        payload["role_ids"] = payload.pop("roleIds")
    if "departmentId" in payload:
        payload["department_id"] = payload.pop("departmentId")
    if "user_id" in payload and "lc_user_id" not in payload:
        payload["lc_user_id"] = payload.get("user_id")
    if payload.get("domain_account"):
        payload["domain_account"] = str(payload["domain_account"]).strip().lower()
    if "user_name" in payload and payload.get("user_name") is not None:
        payload["user_name"] = "".join(str(payload["user_name"]).split()) or None
    payload.pop("password", None)
    return payload


def _resolve_department_id(payload: dict) -> dict:
    normalized = dict(payload)
    if "department_id" not in normalized and "department" not in normalized:
        return normalized

    department_id = normalized.get("department_id")
    department_name = normalized.get("department")

    if department_id not in (None, ""):
        try:
            department_id = int(department_id)
        except (TypeError, ValueError):
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "部门ID不合法")
        department = Department.query.filter(
            Department.id == department_id, Department.valid == 1
        ).first()
        if not department:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "部门不存在或已禁用")
        normalized["department_id"] = department.id
        normalized.pop("department", None)
        return normalized

    department_name = str(department_name or "").strip()
    if not department_name:
        normalized["department_id"] = None
        normalized.pop("department", None)
        return normalized

    department = Department.query.filter(
        Department.valid == 1,
        (Department.name == department_name) | (Department.code == department_name),
    ).first()
    if not department:
        raise BusinessError(ErrorCode.VALIDATION_ERROR, "部门不存在，请先在部门配置中维护")

    normalized["department_id"] = department.id
    normalized.pop("department", None)
    return normalized


def _normalize_role_payload(data: dict) -> dict:
    payload = dict(data)
    if "permissionIds" in payload:
        payload["permission_ids"] = payload.pop("permissionIds")
    if "nodeList" in payload:
        payload["node_list"] = payload.pop("nodeList")
    if payload.get("node_list") is not None:
        normalized_nodes: List[int] = []
        for node in payload.get("node_list") or []:
            try:
                normalized_nodes.append(int(node))
            except (TypeError, ValueError):
                continue
        payload["node_list"] = sorted(set(normalized_nodes))
    return payload


def _normalize_menu_payload(data: dict) -> dict:
    payload = dict(data)
    if "parentId" in payload:
        payload["parent_id"] = payload.pop("parentId")
    if "titleI18nKey" in payload:
        payload["title_i18n_key"] = payload.pop("titleI18nKey")
    if "menuType" in payload:
        payload["menu_type"] = payload.pop("menuType")
    if "permissionCode" in payload:
        payload["permission_code"] = payload.pop("permissionCode")
    if "hidden" in payload:
        hidden_value = payload.get("hidden")
        payload["hidden"] = 1 if hidden_value in (1, True, "1", "true", "TRUE") else 0
    if payload.get("parent_id") is None:
        payload["parent_id"] = 0
    if payload.get("menu_type"):
        payload["menu_type"] = str(payload["menu_type"]).upper()
    return payload


def _build_permission_maps(permissions: List[Permission]):
    id_map = {item.id: item for item in permissions}
    code_map = {item.code: item for item in permissions}
    return id_map, code_map


def _build_role_maps(roles: List[Role]):
    id_map = {item.id: item for item in roles}
    code_map = {item.code: item for item in roles if item.code}
    return id_map, code_map


def _merge_role_limits(roles: List[Role]) -> Dict[str, object]:
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


def _get_admin_role_id() -> Optional[int]:
    admin_role = Role.query.filter(Role.code == "ADMIN", Role.valid == 1).first()
    return admin_role.id if admin_role else None


def _is_admin_user(user: User) -> bool:
    return bool(user.email) and user.email.lower() == ADMIN_EMAIL


def _ensure_admin_role_for_user(user: User) -> bool:
    if not _is_admin_user(user):
        return False
    admin_id = _get_admin_role_id()
    if not admin_id:
        return False
    role_ids = list(user.role_ids or [])
    if admin_id in role_ids:
        return False
    role_ids.append(admin_id)
    user.role_ids = sorted(set(role_ids))
    return True


def _user_to_dict(user: User, roles: List[Role], permissions: List[Permission]) -> Dict:
    role_ids = user.role_ids or []
    role_map, _ = _build_role_maps(roles)
    permission_map, _ = _build_permission_maps(permissions)

    user_roles = [role_map[role_id] for role_id in role_ids if role_id in role_map]
    is_admin = any(role.code == "ADMIN" for role in user_roles if role.code)
    if is_admin:
        permission_ids = [item.id for item in permissions]
        permission_codes = [item.code for item in permissions]
    else:
        permission_ids: List[int] = []
        for role in user_roles:
            permission_ids.extend(role.permission_ids or [])
        permission_ids = sorted(set(permission_ids))
        permission_codes = [
            permission_map[permission_id].code
            for permission_id in permission_ids
            if permission_id in permission_map
        ]

    role_limits = _merge_role_limits(user_roles)
    effective_daily_limit = (
        int(user.daily_round_limit)
        if isinstance(user.daily_round_limit, int) and user.daily_round_limit > 0
        else int(role_limits["dailyRoundLimitDefault"])
    )

    return {
        "id": user.domain_account,
        "domainAccount": user.domain_account,
        "lcUserId": getattr(user, "lc_user_id", None),
        "userName": user.user_name,
        "realName": user.real_name,
        "email": user.email,
        "avatar": user.avatar,
        "phone": user.phone,
        "departmentId": user.department_id,
        "department": user.department_name,
        "roleIds": role_ids,
        "roleIdList": role_ids,
        "roleNames": [role.name for role in user_roles],
        "roleCodes": [role.code for role in user_roles if role.code],
        "permissionIds": permission_ids,
        "permissionCodes": permission_codes,
        "maxCpuCores": role_limits["maxCpuCores"],
        "maxBatchSize": role_limits["maxBatchSize"],
        "dailyRoundLimitDefault": role_limits["dailyRoundLimitDefault"],
        "nodeList": role_limits["nodeList"],
        "dailyRoundLimit": effective_daily_limit,
        "valid": user.valid,
        "createdAt": user.created_at,
        "updatedAt": user.updated_at,
    }


def _role_to_dict(role: Role, permissions: List[Permission]) -> Dict:
    permission_map, _ = _build_permission_maps(permissions)
    permission_ids = role.permission_ids or []
    permission_codes = [
        permission_map[permission_id].code
        for permission_id in permission_ids
        if permission_id in permission_map
    ]
    data = role.to_dict()
    data.update(
        {
            "permissionIds": permission_ids,
            "permissionCodes": permission_codes,
            "maxCpuCores": role.max_cpu_cores,
            "maxBatchSize": role.max_batch_size,
            "nodeList": role.node_list or [],
            "dailyRoundLimitDefault": role.daily_round_limit_default,
            "createdAt": getattr(role, "created_at", None),
            "updatedAt": getattr(role, "updated_at", None),
        }
    )
    return data


def _menu_to_dict(menu: Menu) -> Dict:
    return {
        "id": menu.id,
        "parentId": menu.parent_id or 0,
        "name": menu.name,
        "titleI18nKey": menu.title_i18n_key,
        "icon": menu.icon,
        "path": menu.path,
        "component": menu.component,
        "menuType": menu.menu_type,
        "hidden": menu.hidden == 1,
        "permissionCode": menu.permission_code,
        "sort": menu.sort,
        "valid": menu.valid,
        "createdAt": getattr(menu, "created_at", None),
        "updatedAt": getattr(menu, "updated_at", None),
    }


class RbacService:
    @staticmethod
    def _commit_users(users: List[User]) -> None:
        for user in users:
            db.session.add(user)
        db.session.commit()

    def _ensure_role_ids_valid(self, role_ids: Optional[List[int]]) -> List[int]:
        normalized = sorted(set(int(role_id) for role_id in (role_ids or [])))
        if not normalized:
            return []
        roles = role_repository.find_by_ids(normalized)
        valid_ids = {role.id for role in roles if role.valid == 1}
        return [role_id for role_id in normalized if role_id in valid_ids]

    def _ensure_permission_ids_valid(self, permission_ids: Optional[List[int]]) -> List[int]:
        normalized = sorted(set(int(permission_id) for permission_id in (permission_ids or [])))
        if not normalized:
            return []
        permissions = permission_repository.find_by_ids(normalized)
        valid_ids = {permission.id for permission in permissions if permission.valid == 1}
        return [permission_id for permission_id in normalized if permission_id in valid_ids]

    def _validate_role_uniqueness(self, code: Optional[str], role_id: Optional[int] = None) -> None:
        if not code:
            return
        existing = role_repository.find_by_code(code)
        if existing and existing.id != role_id:
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "角色编码已存在")

    def _validate_permission_uniqueness(
        self, code: Optional[str], permission_id: Optional[int] = None
    ) -> None:
        if not code:
            return
        existing = permission_repository.find_by_code(code)
        if existing and existing.id != permission_id:
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "权限编码已存在")

    def _validate_menu_payload(self, payload: dict, menu_id: Optional[int] = None) -> dict:
        parent_id = int(payload.get("parent_id") or 0)
        if parent_id > 0:
            parent_menu = menu_repository.find_by_id_valid(parent_id)
            if not parent_menu:
                raise BusinessError(ErrorCode.VALIDATION_ERROR, "父级菜单不存在")
            if menu_id and parent_id == menu_id:
                raise BusinessError(ErrorCode.VALIDATION_ERROR, "菜单不能挂在自己下面")
        if payload.get("permission_code"):
            permission = permission_repository.find_by_code(payload["permission_code"])
            if not permission:
                raise BusinessError(ErrorCode.VALIDATION_ERROR, "关联的权限编码不存在")
        return payload

    def list_users(self) -> List[Dict]:
        users = user_repository.find_all_valid(order_by="domain_account")
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        updated_users: List[User] = []
        for user in users:
            if _ensure_admin_role_for_user(user):
                updated_users.append(user)
        if updated_users:
            self._commit_users(updated_users)
        return [_user_to_dict(user, roles, permissions) for user in users]

    def create_user(self, data: dict) -> Dict:
        payload = _resolve_department_id(_normalize_user_payload(data))
        if user_repository.find_by_email(payload.get("email")):
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "邮箱已存在")
        if payload.get("domain_account") and user_repository.find_by_domain_account(
            payload.get("domain_account")
        ):
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "域账号已存在")
        if payload.get("lc_user_id") and user_repository.find_by_lc_user_id(
            payload.get("lc_user_id")
        ):
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "外部用户 ID 已存在")
        payload["role_ids"] = self._ensure_role_ids_valid(payload.get("role_ids"))
        user = user_repository.create(payload)
        if _ensure_admin_role_for_user(user):
            self._commit_users([user])
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        return _user_to_dict(user, roles, permissions)

    def update_user(self, domain_account: str, data: dict) -> Dict:
        normalized_identity = str(domain_account).strip().lower()
        payload = _resolve_department_id(_normalize_user_payload(data))
        target_user = user_repository.find_by_domain_account(normalized_identity)
        if not target_user:
            raise NotFoundError("用户", normalized_identity)

        if "email" in payload:
            existing = user_repository.find_by_email(payload["email"])
            if existing and existing.domain_account != normalized_identity:
                raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "邮箱已存在")
        if "domain_account" in payload and payload.get("domain_account"):
            existing = user_repository.find_by_domain_account(payload["domain_account"])
            if existing and existing.domain_account != normalized_identity:
                raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "域账号已存在")
        if "lc_user_id" in payload and payload.get("lc_user_id"):
            existing = user_repository.find_by_lc_user_id(payload["lc_user_id"])
            if existing and existing.domain_account != normalized_identity:
                raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, "外部用户 ID 已存在")
        if "role_ids" in payload:
            payload["role_ids"] = self._ensure_role_ids_valid(payload.get("role_ids"))

        user = user_repository.update_by_domain_account(normalized_identity, payload)
        if not user:
            raise NotFoundError("用户", normalized_identity)
        if _ensure_admin_role_for_user(user):
            self._commit_users([user])
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        return _user_to_dict(user, roles, permissions)

    def delete_user(self, domain_account: str) -> bool:
        normalized_identity = str(domain_account).strip().lower()
        if not user_repository.soft_delete_by_domain_account(normalized_identity):
            raise NotFoundError("用户", normalized_identity)
        return True

    def list_roles(self) -> List[Dict]:
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        return [_role_to_dict(role, permissions) for role in roles]

    def create_role(self, data: dict) -> Dict:
        payload = _normalize_role_payload(data)
        self._validate_role_uniqueness(payload.get("code"))
        payload["permission_ids"] = self._ensure_permission_ids_valid(payload.get("permission_ids"))
        role = role_repository.create(payload)
        permissions = permission_repository.find_all_valid()
        return _role_to_dict(role, permissions)

    def update_role(self, role_id: int, data: dict) -> Dict:
        payload = _normalize_role_payload(data)
        if "code" in payload:
            self._validate_role_uniqueness(payload.get("code"), role_id)
        if "permission_ids" in payload:
            payload["permission_ids"] = self._ensure_permission_ids_valid(payload.get("permission_ids"))
        role = role_repository.update(role_id, payload)
        if not role:
            raise NotFoundError("角色", role_id)
        permissions = permission_repository.find_all_valid()
        return _role_to_dict(role, permissions)

    def delete_role(self, role_id: int) -> bool:
        if not role_repository.soft_delete(role_id):
            raise NotFoundError("角色", role_id)
        return True

    def list_permissions(self) -> List[Dict]:
        permissions = permission_repository.find_all_valid()
        return [item.to_dict() for item in permissions]

    def create_permission(self, data: dict) -> Dict:
        self._validate_permission_uniqueness(data.get("code"))
        permission = permission_repository.create(data)
        return permission.to_dict()

    def update_permission(self, permission_id: int, data: dict) -> Dict:
        if "code" in data:
            self._validate_permission_uniqueness(data.get("code"), permission_id)
        permission = permission_repository.update(permission_id, data)
        if not permission:
            raise NotFoundError("权限", permission_id)
        return permission.to_dict()

    def delete_permission(self, permission_id: int) -> bool:
        if not permission_repository.soft_delete(permission_id):
            raise NotFoundError("权限", permission_id)
        return True

    def list_menus(self) -> List[Dict]:
        menus = menu_repository.find_all_valid()
        return [_menu_to_dict(menu) for menu in menus]

    def create_menu(self, data: dict) -> Dict:
        payload = self._validate_menu_payload(_normalize_menu_payload(data))
        menu = menu_repository.create(payload)
        return _menu_to_dict(menu)

    def update_menu(self, menu_id: int, data: dict) -> Dict:
        payload = self._validate_menu_payload(_normalize_menu_payload(data), menu_id=menu_id)
        menu = menu_repository.update(menu_id, payload)
        if not menu:
            raise NotFoundError("菜单", menu_id)
        return _menu_to_dict(menu)

    def delete_menu(self, menu_id: int) -> bool:
        children = menu_repository.find_by_parent_id(menu_id)
        if children:
            raise BusinessError(ErrorCode.BUSINESS_ERROR, "请先删除子菜单")
        if not menu_repository.soft_delete(menu_id):
            raise NotFoundError("菜单", menu_id)
        return True


rbac_service = RbacService()
