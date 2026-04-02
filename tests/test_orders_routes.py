def test_orders_crud_flow(client, auth_headers, project, fold_type, sim_type):
    payload = {
        'projectId': project.id,
        'modelLevelId': 1,
        'originFile': {'type': 1, 'name': 'demo.stp', 'path': '/data/demo.stp'},
        'originFoldTypeId': fold_type.id,
        'foldTypeIds': [fold_type.id],
        'remark': 'first order',
        'inputJson': {
            'version': 2,
            'projectInfo': {
                'projectId': project.id,
                'participantIds': [],
                'originFile': {'type': 1, 'name': 'demo.stp', 'path': '/data/demo.stp'},
                'originFoldTypeId': fold_type.id,
                'modelLevelId': 1,
                'remark': 'first order',
            },
            'conditions': [
                {
                    'conditionId': 1,
                    'foldTypeId': fold_type.id,
                    'foldTypeName': fold_type.name,
                    'simTypeId': sim_type.id,
                    'simTypeName': sim_type.name,
                    'params': {'optParams': {'algType': 1, 'batchSize': [1], 'maxIter': 1}},
                    'output': {'respDetails': []},
                    'solver': {'solverId': 1, 'cpuType': 1, 'cpuCores': 1, 'double': 0, 'useGlobalConfig': 1},
                    'careDeviceIds': [],
                    'remark': 'condition-1',
                }
            ],
            'globalSolver': {'solverId': 1, 'cpuType': 1, 'cpuCores': 1, 'double': 0, 'useGlobalConfig': 1, 'applyToAll': True},
        },
    }
    create_resp = client.post('/api/v1/orders', json=payload, headers=auth_headers)
    assert create_resp.status_code == 200
    create_payload = create_resp.get_json()
    order_id = create_payload['data']['id']
    assert create_payload['data']['projectId'] == project.id
    assert create_payload['data']['domainAccount'] == 'tester'

    list_resp = client.get('/api/v1/orders?page=1&pageSize=10', headers=auth_headers)
    assert list_resp.status_code == 200
    list_payload = list_resp.get_json()
    assert list_payload['data']['total'] >= 1
    assert list_payload['data']['items'][0]['domainAccount'] == 'tester'

    creator_query_resp = client.get('/api/v1/orders?page=1&pageSize=10&domainAccount=tester', headers=auth_headers)
    assert creator_query_resp.status_code == 200
    assert creator_query_resp.get_json()['data']['total'] >= 1

    remark_query_resp = client.get('/api/v1/orders?page=1&pageSize=10&remark=first', headers=auth_headers)
    assert remark_query_resp.status_code == 200
    assert remark_query_resp.get_json()['data']['total'] >= 1

    update_resp = client.put(
        f'/api/v1/orders/{order_id}',
        json={'remark': 'updated', 'baseDir': '/data/orders/ord-1'},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    update_payload = update_resp.get_json()
    assert update_payload['data']['remark'] == 'updated'
    assert update_payload['data']['baseDir'] == '/data/orders/ord-1'

    delete_resp = client.delete(f'/api/v1/orders/{order_id}', headers=auth_headers)
    assert delete_resp.status_code == 200
