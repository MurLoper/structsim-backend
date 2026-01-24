from flask_jwt_extended import create_access_token

from app import db
from app.models.config import Project, SimType
from app.models.order import Order
from app.models.result import SimTypeResult, Round


def _auth_headers(app):
    with app.app_context():
        token = create_access_token(identity='1')
    return {'Authorization': f'Bearer {token}'}


def test_results_endpoints(client, app, db_session):
    headers = _auth_headers(app)

    project = Project(name='项目A', code='PROJ_A', valid=1, sort=1)
    sim_type = SimType(name='结构', code='SIM_A', category='STRUCT', valid=1, sort=1)
    db_session.add(project)
    db_session.add(sim_type)
    db_session.commit()

    order = Order(order_no='ORD_001', project_id=project.id, sim_type_ids=[sim_type.id], opt_param={})
    db_session.add(order)
    db_session.commit()

    sim_result = SimTypeResult(order_id=order.id, sim_type_id=sim_type.id)
    db_session.add(sim_result)
    db_session.commit()

    round_item = Round(
        sim_type_result_id=sim_result.id,
        order_id=order.id,
        sim_type_id=sim_type.id,
        round_index=1,
        params={'x': 10},
        outputs={'y': 20},
        status=1,
    )
    db_session.add(round_item)
    db_session.commit()

    sim_resp = client.get(f'/api/results/sim-type/{sim_result.id}', headers=headers)
    assert sim_resp.status_code == 200

    list_resp = client.get(f'/api/results/order/{order.id}/sim-types', headers=headers)
    assert list_resp.status_code == 200

    rounds_resp = client.get(
        f'/api/results/sim-type/{sim_result.id}/rounds?page=1&pageSize=10',
        headers=headers
    )
    assert rounds_resp.status_code == 200

    round_detail = client.get(f'/api/results/rounds/{round_item.id}', headers=headers)
    assert round_detail.status_code == 200

    analysis_resp = client.post(
        '/api/results/analysis',
        json={
            'orderId': order.id,
            'simTypeId': sim_type.id,
            'chartType': 'SCATTER',
            'xField': 'x',
            'yField': 'y',
        },
        headers=headers
    )
    assert analysis_resp.status_code == 200
    assert analysis_resp.get_json()['totalPoints'] == 1
