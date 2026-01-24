import pytest
from app.api.v1.rbac import service as rbac_service_module
from app.api.v1.rbac.service import (
    _normalize_user_payload,
    _normalize_role_payload,
    _build_permission_maps,
    _build_role_maps,
    _user_to_dict,
    rbac_service,
)
from app.common.errors import BusinessError, NotFoundError
from app.constants import ErrorCode


class FakePermission:
    def __init__(self, id, code):
        self.id = id
        self.code = code

    def to_dict(self):
        return {'id': self.id, 'code': self.code}


class FakeRole:
    def __init__(self, id, name, code=None, permission_ids=None):
        self.id = id
        self.name = name
        self.code = code
        self.permission_ids = permission_ids or []

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'code': self.code}


class FakeUser:
    def __init__(self, id, username, email, role_ids=None, valid=1):
        self.id = id
        self.username = username
        self.email = email
        self.role_ids = role_ids or []
        self.valid = valid

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email}


def test_normalize_user_payload():
    payload = _normalize_user_payload({'roleIds': [1], 'password': 'secret', 'email': 'a@b.com'})
    assert 'role_ids' in payload
    assert 'password' not in payload
    assert 'password_hash' in payload


def test_normalize_role_payload():
    payload = _normalize_role_payload({'permissionIds': [1, 2], 'name': 'Admin'})
    assert payload['permission_ids'] == [1, 2]
    assert 'permissionIds' not in payload


def test_build_maps():
    permissions = [FakePermission(1, 'READ'), FakePermission(2, 'WRITE')]
    roles = [FakeRole(1, 'Admin', 'ADMIN')]

    id_map, code_map = _build_permission_maps(permissions)
    assert id_map[1].code == 'READ'
    assert code_map['WRITE'].id == 2

    role_id_map, role_code_map = _build_role_maps(roles)
    assert role_id_map[1].name == 'Admin'
    assert role_code_map['ADMIN'].id == 1


def test_user_to_dict_admin_permissions():
    permissions = [FakePermission(1, 'READ'), FakePermission(2, 'WRITE')]
    roles = [FakeRole(1, 'Admin', 'ADMIN')]
    user = FakeUser(1, 'alice', 'alice@sim.com', role_ids=[1])

    data = _user_to_dict(user, roles, permissions)
    assert data['permissionIds'] == [1, 2]
    assert 'READ' in data['permissionCodes']


def test_list_users_assign_admin_role(monkeypatch):
    admin_role = FakeRole(1, 'Admin', 'ADMIN')
    permissions = [FakePermission(1, 'READ'), FakePermission(2, 'WRITE')]
    user = FakeUser(1, 'alice', 'alice@sim.com', role_ids=[])

    monkeypatch.setattr(rbac_service_module, '_get_admin_role_id', lambda: 1)
    monkeypatch.setattr(rbac_service_module.user_repository, 'find_all_valid', lambda order_by='id': [user])
    monkeypatch.setattr(rbac_service_module.role_repository, 'find_all_valid', lambda: [admin_role])
    monkeypatch.setattr(rbac_service_module.permission_repository, 'find_all_valid', lambda: permissions)
    monkeypatch.setattr(rbac_service, '_commit_users', lambda users: None)

    result = rbac_service.list_users()
    assert result[0]['roleIds'] == [1]
    assert result[0]['permissionIds'] == [1, 2]


def test_create_user_duplicate_email(monkeypatch):
    monkeypatch.setattr(rbac_service_module.user_repository, 'find_by_email', lambda email: FakeUser(1, 'u', email))
    monkeypatch.setattr(rbac_service_module.user_repository, 'find_by_username', lambda username: None)

    with pytest.raises(BusinessError) as exc:
        rbac_service.create_user({'email': 'a@b.com', 'username': 'u1', 'password': 'x'})

    assert exc.value.code == ErrorCode.DUPLICATE_RESOURCE


def test_update_user_not_found(monkeypatch):
    monkeypatch.setattr(rbac_service_module.user_repository, 'find_by_email', lambda email: None)
    monkeypatch.setattr(rbac_service_module.user_repository, 'find_by_username', lambda username: None)
    monkeypatch.setattr(rbac_service_module.user_repository, 'update', lambda user_id, data: None)

    with pytest.raises(NotFoundError):
        rbac_service.update_user(999, {'email': 'a@b.com'})
