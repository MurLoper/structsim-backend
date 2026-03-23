from app.models.order import Order


def test_results_conditions_fallback_to_order_input_json(client, auth_headers, db_session, project):
    order = Order(
        order_no='ORD_MOCK_FALLBACK_001',
        project_id=project.id,
        sim_type_ids=[21],
        fold_type_ids=[11],
        opt_param={},
        input_json={
            'conditions': [
                {
                    'conditionId': 101,
                    'foldTypeId': 11,
                    'foldTypeName': '半折叠态',
                    'simTypeId': 21,
                    'simTypeName': '跌落',
                    'params': {
                        'paramDetails': [{'paramName': '厚度'}, {'paramName': '角度'}],
                        'optParams': {'algType': 1, 'batchSize': [2, 2], 'maxIter': 2},
                    },
                    'output': {
                        'respDetails': [{'respName': '位移'}, {'respName': '应力'}],
                    },
                    'solver': {'solverId': 'abaqus', 'solverVersion': '2024'},
                }
            ]
        },
        created_by='tester',
    )
    db_session.add(order)
    db_session.commit()

    summary_resp = client.get(f'/api/results/order/{order.id}/conditions', headers=auth_headers)
    assert summary_resp.status_code == 200
    summary_payload = summary_resp.get_json()['data']
    assert len(summary_payload) == 1
    assert summary_payload[0]['conditionId'] == 101
    assert summary_payload[0]['foldTypeName'] == '半折叠态'
    assert summary_payload[0]['simTypeName'] == '跌落'
    assert summary_payload[0]['roundTotal'] == 4
    assert summary_payload[0]['resultSource'] == 'mock'

    mock_condition_id = summary_payload[0]['id']
    detail_resp = client.get(f'/api/results/order-condition/{mock_condition_id}', headers=auth_headers)
    assert detail_resp.status_code == 200
    detail_payload = detail_resp.get_json()['data']
    assert detail_payload['conditionId'] == 101
    assert detail_payload['roundSchema']['paramKeys'] == ['厚度', '角度']

    rounds_resp = client.get(
        f'/api/results/order-condition/{mock_condition_id}/rounds?page=1&pageSize=20',
        headers=auth_headers,
    )
    assert rounds_resp.status_code == 200
    rounds_payload = rounds_resp.get_json()['data']
    assert rounds_payload['total'] == 4
    assert rounds_payload['orderCondition']['conditionId'] == 101
    assert len(rounds_payload['items']) == 4


def test_results_mock_payload_follows_order_status(client, auth_headers, db_session, project):
    order = Order(
        order_no='ORD_MOCK_STATUS_001',
        project_id=project.id,
        sim_type_ids=[21, 22, 23],
        fold_type_ids=[11],
        opt_param={},
        status=1,
        progress=52,
        input_json={
            'conditions': [
                {
                    'conditionId': 201,
                    'foldTypeId': 11,
                    'foldTypeName': '半折叠态',
                    'simTypeId': 21,
                    'simTypeName': '跌落',
                    'params': {'optParams': {'algType': 1, 'batchSize': [2, 2], 'maxIter': 2}},
                    'output': {'respDetails': [{'respName': '位移'}]},
                },
                {
                    'conditionId': 202,
                    'foldTypeId': 11,
                    'foldTypeName': '半折叠态',
                    'simTypeId': 22,
                    'simTypeName': '落球',
                    'params': {'optParams': {'algType': 1, 'batchSize': [2, 2], 'maxIter': 2}},
                    'output': {'respDetails': [{'respName': '应力'}]},
                },
                {
                    'conditionId': 203,
                    'foldTypeId': 11,
                    'foldTypeName': '半折叠态',
                    'simTypeId': 23,
                    'simTypeName': '冲击',
                    'params': {'optParams': {'algType': 1, 'batchSize': [2, 2], 'maxIter': 2}},
                    'output': {'respDetails': [{'respName': '加速度'}]},
                },
            ]
        },
        created_by='tester',
    )
    db_session.add(order)
    db_session.commit()

    summary_resp = client.get(f'/api/results/order/{order.id}/conditions', headers=auth_headers)
    assert summary_resp.status_code == 200
    summary_payload = summary_resp.get_json()['data']
    assert [item['status'] for item in summary_payload] == [2, 1, 0]

    running_condition_id = summary_payload[1]['id']
    rounds_resp = client.get(
        f'/api/results/order-condition/{running_condition_id}/rounds?page=1&pageSize=20',
        headers=auth_headers,
    )
    assert rounds_resp.status_code == 200
    rounds_payload = rounds_resp.get_json()['data']
    assert rounds_payload['statistics']['runningRounds'] == 1
    assert rounds_payload['items'][-1]['status'] == 1

    order.status = 3
    order.progress = 100
    db_session.commit()

    failed_summary_resp = client.get(f'/api/results/order/{order.id}/conditions', headers=auth_headers)
    failed_summary_payload = failed_summary_resp.get_json()['data']
    assert [item['status'] for item in failed_summary_payload] == [2, 3, 0]
