from app.models.order import Order


def test_results_cases_fallback_to_order_input_json(client, auth_headers, db_session, project):
    order = Order(
        order_no='ORD_MOCK_FALLBACK_001',
        project_id=project.id,
        sim_type_ids=[21],
        fold_type_ids=[11],
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

    cases_resp = client.get(f'/api/v1/results/order/{order.id}/cases', headers=auth_headers)
    assert cases_resp.status_code == 200
    cases_payload = cases_resp.get_json()['data']
    assert len(cases_payload['cases']) == 1
    assert len(cases_payload['conditions']) == 1
    case_payload = cases_payload['cases'][0]
    assert len(case_payload['conditions']) == 1
    condition_payload = case_payload['conditions'][0]
    assert condition_payload['conditionId'] == 101
    assert condition_payload['foldTypeName'] == '半折叠态'
    assert condition_payload['simTypeName'] == '跌落'
    assert condition_payload['roundTotal'] == 4
    assert condition_payload['resultSource'] == 'mock'
    assert condition_payload['rounds']['total'] == 4
    assert condition_payload['rounds']['orderCondition']['conditionId'] == 101
    assert len(condition_payload['rounds']['items']) == 4


def test_results_cases_mock_payload_follows_order_status(client, auth_headers, db_session, project):
    order = Order(
        order_no='ORD_MOCK_STATUS_001',
        project_id=project.id,
        sim_type_ids=[21, 22, 23],
        fold_type_ids=[11],
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

    cases_resp = client.get(f'/api/v1/results/order/{order.id}/cases', headers=auth_headers)
    assert cases_resp.status_code == 200
    cases_payload = cases_resp.get_json()['data']
    condition_payloads = [
        condition
        for case_payload in cases_payload['cases']
        for condition in case_payload['conditions']
    ]
    assert [item['status'] for item in condition_payloads] == [2, 1, 0]
    running_payload = next(item for item in condition_payloads if item['conditionId'] == 202)
    assert running_payload['rounds']['statistics']['runningRounds'] == 1
    assert running_payload['rounds']['items'][-1]['status'] == 1

    order.status = 3
    order.progress = 100
    db_session.commit()

    failed_cases_resp = client.get(f'/api/v1/results/order/{order.id}/cases', headers=auth_headers)
    failed_payload = failed_cases_resp.get_json()['data']
    failed_conditions = [
        condition
        for case_payload in failed_payload['cases']
        for condition in case_payload['conditions']
    ]
    assert [item['status'] for item in failed_conditions] == [2, 3, 0]
