from flask_jwt_extended import create_access_token

from app.constants import ErrorCode


def _auth_headers(app):
    with app.app_context():
        token = create_access_token(identity='1')
    return {'Authorization': f'Bearer {token}'}


def test_rbac_routes_crud(client, app):
    headers = _auth_headers(app)

    perm_resp = client.post(
        '/api/v1/rbac/permissions',
        json={'name': '查看权限', 'code': 'VIEW_DASH', 'type': 'PAGE'},
        headers=headers
    )
    perm_data = perm_resp.get_json()
    assert perm_data['code'] == ErrorCode.SUCCESS
    perm_id = perm_data['data']['id']

    role_resp = client.post(
        '/api/v1/rbac/roles',
        json={'name': '管理员', 'code': 'ADMIN_TEST', 'permissionIds': [perm_id]},
        headers=headers
    )
    role_data = role_resp.get_json()
    assert role_data['code'] == ErrorCode.SUCCESS
    role_id = role_data['data']['id']

    user_resp = client.post(
        '/api/v1/rbac/users',
        json={
            'username': 'user_test',
            'email': 'user_test@example.com',
            'password': 'secret123',
            'roleIds': [role_id],
        },
        headers=headers
    )
    user_data = user_resp.get_json()
    assert user_data['code'] == ErrorCode.SUCCESS
    user_id = user_data['data']['id']

    list_users = client.get('/api/v1/rbac/users', headers=headers)
    assert list_users.get_json()['code'] == ErrorCode.SUCCESS

    update_user = client.put(
        f'/api/v1/rbac/users/{user_id}',
        json={'name': '新名称'},
        headers=headers
    )
    assert update_user.get_json()['code'] == ErrorCode.SUCCESS

    update_role = client.put(
        f'/api/v1/rbac/roles/{role_id}',
        json={'description': 'updated'},
        headers=headers
    )
    assert update_role.get_json()['code'] == ErrorCode.SUCCESS

    update_perm = client.put(
        f'/api/v1/rbac/permissions/{perm_id}',
        json={'description': 'updated'},
        headers=headers
    )
    assert update_perm.get_json()['code'] == ErrorCode.SUCCESS

    delete_user = client.delete(f'/api/v1/rbac/users/{user_id}', headers=headers)
    assert delete_user.get_json()['code'] == ErrorCode.SUCCESS

    delete_role = client.delete(f'/api/v1/rbac/roles/{role_id}', headers=headers)
    assert delete_role.get_json()['code'] == ErrorCode.SUCCESS

    delete_perm = client.delete(f'/api/v1/rbac/permissions/{perm_id}', headers=headers)
    assert delete_perm.get_json()['code'] == ErrorCode.SUCCESS
