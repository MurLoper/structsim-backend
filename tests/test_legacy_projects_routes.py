from flask_jwt_extended import create_access_token


def _auth_headers(app):
    with app.app_context():
        token = create_access_token(identity='1')
    return {'Authorization': f'Bearer {token}'}


def test_legacy_projects_crud(client, app):
    headers = _auth_headers(app)

    create_resp = client.post(
        '/api/projects',
        json={'name': 'LegacyProject', 'code': 'LEGACY_1'},
        headers=headers
    )
    assert create_resp.status_code == 201
    project_id = create_resp.get_json()['id']

    list_resp = client.get('/api/projects')
    assert list_resp.status_code == 200

    get_resp = client.get(f'/api/projects/{project_id}')
    assert get_resp.status_code == 200

    update_resp = client.put(
        f'/api/projects/{project_id}',
        json={'name': 'LegacyProjectUpdated'},
        headers=headers
    )
    assert update_resp.status_code == 200

    delete_resp = client.delete(f'/api/projects/{project_id}', headers=headers)
    assert delete_resp.status_code == 200

    missing_resp = client.get(f'/api/projects/{project_id}')
    assert missing_resp.status_code == 404
