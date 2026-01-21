from app.constants import ErrorCode


def test_project_crud(client):
    create_resp = client.post('/api/v1/config/projects', json={'name': '项目A', 'code': 'P001'})
    create_data = create_resp.get_json()
    assert create_resp.status_code == 200
    assert create_data['code'] == ErrorCode.SUCCESS

    project_id = create_data['data']['id']

    get_resp = client.get(f'/api/v1/config/projects/{project_id}')
    get_data = get_resp.get_json()
    assert get_data['code'] == ErrorCode.SUCCESS

    update_resp = client.put(f'/api/v1/config/projects/{project_id}', json={'name': '项目A-更新'})
    update_data = update_resp.get_json()
    assert update_data['code'] == ErrorCode.SUCCESS

    delete_resp = client.delete(f'/api/v1/config/projects/{project_id}')
    delete_data = delete_resp.get_json()
    assert delete_data['code'] == ErrorCode.SUCCESS

    missing_resp = client.get(f'/api/v1/config/projects/{project_id}')
    assert missing_resp.status_code == 404


def test_sim_type_and_fold_type_crud(client):
    sim_resp = client.post('/api/v1/config/sim-types', json={'name': '结构仿真', 'code': 'SIM_A'})
    sim_data = sim_resp.get_json()
    assert sim_data['code'] == ErrorCode.SUCCESS
    sim_id = sim_data['data']['id']

    update_sim = client.put(f'/api/v1/config/sim-types/{sim_id}', json={'name': '结构仿真-更新'})
    assert update_sim.get_json()['code'] == ErrorCode.SUCCESS

    delete_sim = client.delete(f'/api/v1/config/sim-types/{sim_id}')
    assert delete_sim.get_json()['code'] == ErrorCode.SUCCESS

    fold_resp = client.post('/api/v1/config/fold-types', json={'name': '折叠', 'code': 'F01', 'angle': 45})
    fold_data = fold_resp.get_json()
    assert fold_data['code'] == ErrorCode.SUCCESS
    fold_id = fold_data['data']['id']

    update_fold = client.put(f'/api/v1/config/fold-types/{fold_id}', json={'angle': 90})
    assert update_fold.get_json()['code'] == ErrorCode.SUCCESS

    delete_fold = client.delete(f'/api/v1/config/fold-types/{fold_id}')
    assert delete_fold.get_json()['code'] == ErrorCode.SUCCESS


def test_param_def_validation_and_update(client):
    invalid_resp = client.post(
        '/api/v1/config/param-defs',
        json={'name': '参数', 'key': 'p1', 'min_val': 10, 'max_val': 5}
    )
    assert invalid_resp.status_code == 400
    assert invalid_resp.get_json()['code'] == ErrorCode.VALIDATION_ERROR

    create_resp = client.post(
        '/api/v1/config/param-defs',
        json={'name': '参数A', 'key': 'param_a', 'min_val': 1, 'max_val': 10}
    )
    data = create_resp.get_json()
    assert data['code'] == ErrorCode.SUCCESS
    param_id = data['data']['id']

    update_resp = client.put(
        f'/api/v1/config/param-defs/{param_id}',
        json={'minVal': 2, 'maxVal': 20, 'valType': 2}
    )
    update_data = update_resp.get_json()
    assert update_data['code'] == ErrorCode.SUCCESS


def test_solver_condition_output_crud(client):
    solver_resp = client.post('/api/v1/config/solvers', json={'name': 'SolverA', 'code': 'SOL_A'})
    solver_data = solver_resp.get_json()
    assert solver_data['code'] == ErrorCode.SUCCESS
    solver_id = solver_data['data']['id']

    solver_update = client.put(f'/api/v1/config/solvers/{solver_id}', json={'version': '2.0'})
    assert solver_update.get_json()['code'] == ErrorCode.SUCCESS

    condition_resp = client.post('/api/v1/config/condition-defs', json={'name': '工况A', 'code': 'COND_A'})
    condition_data = condition_resp.get_json()
    assert condition_data['code'] == ErrorCode.SUCCESS
    condition_id = condition_data['data']['id']

    condition_update = client.put(
        f'/api/v1/config/condition-defs/{condition_id}',
        json={'unit': 'kN'}
    )
    assert condition_update.get_json()['code'] == ErrorCode.SUCCESS

    output_resp = client.post('/api/v1/config/output-defs', json={'name': '输出A', 'code': 'OUT_A'})
    output_data = output_resp.get_json()
    assert output_data['code'] == ErrorCode.SUCCESS
    output_id = output_data['data']['id']

    output_update = client.put(
        f'/api/v1/config/output-defs/{output_id}',
        json={'unit': 'mm'}
    )
    assert output_update.get_json()['code'] == ErrorCode.SUCCESS

    delete_output = client.delete(f'/api/v1/config/output-defs/{output_id}')
    assert delete_output.get_json()['code'] == ErrorCode.SUCCESS

    delete_condition = client.delete(f'/api/v1/config/condition-defs/{condition_id}')
    assert delete_condition.get_json()['code'] == ErrorCode.SUCCESS

    delete_solver = client.delete(f'/api/v1/config/solvers/{solver_id}')
    assert delete_solver.get_json()['code'] == ErrorCode.SUCCESS
