def test_auth_login_and_me(client, user):
    resp = client.post('/api/v1/auth/login', json={'email': user.email, 'password': 'demo'})
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload['data']['user']['email'] == user.email
    token = payload['data']['token']

    me_resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_resp.status_code == 200
    me_payload = me_resp.get_json()
    assert me_payload['data']['email'] == user.email


def test_auth_users_list(client, user):
    resp = client.get('/api/v1/auth/users')
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload['data'][0]['email'] == user.email
