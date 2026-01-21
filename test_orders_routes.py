def test_orders_crud_flow(client, auth_headers, project, fold_type, sim_type):
    payload = {
        'projectId': project.id,
        'originFile': {'type': 1, 'name': 'demo.stp', 'path': '/data/demo.stp'},
        'foldTypeId': fold_type.id,
        'remark': 'first order',
        'simTypeIds': [sim_type.id],
        'optParam': {'config': 'value'},
    }
    create_resp = client.post('/api/v1/orders', json=payload, headers=auth_headers)
    assert create_resp.status_code == 200
    create_payload = create_resp.get_json()
    order_id = create_payload['data']['id']
    assert create_payload['data']['projectId'] == project.id

    list_resp = client.get('/api/v1/orders?page=1&pageSize=10', headers=auth_headers)
    assert list_resp.status_code == 200
    list_payload = list_resp.get_json()
    assert list_payload['data']['total'] >= 1

    update_resp = client.put(
        f'/api/v1/orders/{order_id}',
        json={'remark': 'updated'},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    update_payload = update_resp.get_json()
    assert update_payload['data']['remark'] == 'updated'

    delete_resp = client.delete(f'/api/v1/orders/{order_id}', headers=auth_headers)
    assert delete_resp.status_code == 200
