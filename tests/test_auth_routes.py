from flask_jwt_extended import create_access_token


def test_auth_me(client, app, user):
    with app.app_context():
        token = create_access_token(identity=str(user.id))

    me_resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_resp.status_code == 200
    me_payload = me_resp.get_json()
    assert me_payload['data']['email'] == user.email


def test_auth_users_list(client, user):
    resp = client.get('/api/v1/auth/users')
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload['data'][0]['email'] == user.email
