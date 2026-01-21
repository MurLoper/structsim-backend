from app.constants import ErrorCode


def test_param_group_flow(client):
    group_resp = client.post('/api/v1/param-groups', json={'name': '参数组合A', 'description': 'demo'})
    group_data = group_resp.get_json()
    assert group_data['code'] == ErrorCode.SUCCESS
    group_id = group_data['data']['id']

    list_resp = client.get('/api/v1/param-groups')
    assert list_resp.get_json()['code'] == ErrorCode.SUCCESS

    param_resp = client.post(
        '/api/v1/config/param-defs',
        json={'name': '参数A', 'key': 'param_group_a', 'min_val': 1, 'max_val': 10}
    )
    param_id = param_resp.get_json()['data']['id']

    add_resp = client.post(
        f'/api/v1/param-groups/{group_id}/params',
        json={'paramDefId': param_id, 'defaultValue': '5'}
    )
    assert add_resp.get_json()['code'] == ErrorCode.SUCCESS

    params_resp = client.get(f'/api/v1/param-groups/{group_id}/params')
    assert params_resp.get_json()['code'] == ErrorCode.SUCCESS

    remove_resp = client.delete(f'/api/v1/param-groups/{group_id}/params/{param_id}')
    assert remove_resp.get_json()['code'] == ErrorCode.SUCCESS

    delete_resp = client.delete(f'/api/v1/param-groups/{group_id}')
    assert delete_resp.get_json()['code'] == ErrorCode.SUCCESS


def test_cond_out_group_flow(client):
    group_resp = client.post('/api/v1/cond-out-groups', json={'name': '工况输出组合A'})
    group_data = group_resp.get_json()
    assert group_data['code'] == ErrorCode.SUCCESS
    group_id = group_data['data']['id']

    condition_resp = client.post('/api/v1/config/condition-defs', json={'name': '工况A', 'code': 'COND_GROUP'})
    condition_id = condition_resp.get_json()['data']['id']

    output_resp = client.post('/api/v1/config/output-defs', json={'name': '输出A', 'code': 'OUT_GROUP'})
    output_id = output_resp.get_json()['data']['id']

    add_condition = client.post(
        f'/api/v1/cond-out-groups/{group_id}/conditions',
        json={'conditionDefId': condition_id, 'configData': {'k': 'v'}}
    )
    assert add_condition.get_json()['code'] == ErrorCode.SUCCESS

    add_output = client.post(
        f'/api/v1/cond-out-groups/{group_id}/outputs',
        json={'outputDefId': output_id}
    )
    assert add_output.get_json()['code'] == ErrorCode.SUCCESS

    detail_resp = client.get(f'/api/v1/cond-out-groups/{group_id}')
    assert detail_resp.get_json()['code'] == ErrorCode.SUCCESS

    remove_condition = client.delete(f'/api/v1/cond-out-groups/{group_id}/conditions/{condition_id}')
    assert remove_condition.get_json()['code'] == ErrorCode.SUCCESS

    remove_output = client.delete(f'/api/v1/cond-out-groups/{group_id}/outputs/{output_id}')
    assert remove_output.get_json()['code'] == ErrorCode.SUCCESS

    delete_resp = client.delete(f'/api/v1/cond-out-groups/{group_id}')
    assert delete_resp.get_json()['code'] == ErrorCode.SUCCESS
