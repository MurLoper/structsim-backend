from flask_jwt_extended import create_access_token

from app.constants import ErrorCode


def _auth_headers(app):
    with app.app_context():
        token = create_access_token(identity='1')
    return {'Authorization': f'Bearer {token}'}


def test_projects_crud(client, app):
    headers = _auth_headers(app)

    create_resp = client.post(
        '/api/v1/config/projects',
        json={'name': 'ProjectCompat', 'code': 'PROJECT_COMPAT_1'},
        headers=headers,
    )
    assert create_resp.status_code == 200
    create_payload = create_resp.get_json()
    assert create_payload['code'] == ErrorCode.SUCCESS
    project_id = create_payload['data']['id']

    list_resp = client.get('/api/v1/config/projects')
    assert list_resp.status_code == 200

    get_resp = client.get(f'/api/v1/config/projects/{project_id}')
    assert get_resp.status_code == 200

    update_resp = client.put(
        f'/api/v1/config/projects/{project_id}',
        json={'name': 'ProjectCompatUpdated'},
        headers=headers,
    )
    assert update_resp.status_code == 200

    delete_resp = client.delete(f'/api/v1/config/projects/{project_id}', headers=headers)
    assert delete_resp.status_code == 200

    missing_resp = client.get(f'/api/v1/config/projects/{project_id}')
    assert missing_resp.status_code == 404
