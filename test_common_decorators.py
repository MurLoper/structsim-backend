import pytest
from pydantic import BaseModel
from flask_jwt_extended import create_access_token

from app.common.decorators import require_permission, log_request, validate_json
from app.common.response import success
from app.constants import ErrorCode


def test_require_permission_allows(client, app):
    @app.route('/test-permission-allow')
    @require_permission('VIEW_DASHBOARD')
    def _permission_allow():
        return success({'ok': True})

    with app.app_context():
        token = create_access_token(identity='1', additional_claims={'permissions': ['VIEW_DASHBOARD']})
    response = client.get('/test-permission-allow', headers={'Authorization': f'Bearer {token}'})
    data = response.get_json()

    assert response.status_code == 200
    assert data['code'] == ErrorCode.SUCCESS
    assert data['data']['ok'] is True


def test_require_permission_denied(client, app):
    @app.route('/test-permission-denied')
    @require_permission('ADMIN_ONLY')
    def _permission_denied():
        return success({'ok': True})

    with app.app_context():
        token = create_access_token(identity='1', additional_claims={'permissions': ['VIEW_DASHBOARD']})
    response = client.get('/test-permission-denied', headers={'Authorization': f'Bearer {token}'})
    data = response.get_json()

    assert response.status_code == 403
    assert data['code'] == ErrorCode.PERMISSION_DENIED


def test_require_permission_missing_token(client, app):
    @app.route('/test-permission-missing')
    @require_permission('VIEW_DASHBOARD')
    def _permission_missing():
        return success({'ok': True})

    response = client.get('/test-permission-missing')
    data = response.get_json()

    assert response.status_code == 401
    assert data['code'] == ErrorCode.TOKEN_INVALID


def test_log_request_decorator(client, app):
    @app.route('/test-log')
    @log_request
    def _log_request():
        return success({'logged': True})

    response = client.get('/test-log')
    data = response.get_json()

    assert response.status_code == 200
    assert data['data']['logged'] is True


def test_validate_json_decorator(client, app):
    class Payload(BaseModel):
        name: str
        age: int

    @app.route('/test-validate', methods=['POST'])
    @validate_json(Payload)
    def _validate_json():
        return success({'ok': True})

    response = client.post('/test-validate', json={'name': 'test', 'age': 20})
    data = response.get_json()

    assert response.status_code == 200
    assert data['code'] == ErrorCode.SUCCESS

    invalid_response = client.post('/test-validate', json={'name': 'test'})
    invalid_data = invalid_response.get_json()

    assert invalid_response.status_code == 400
    assert invalid_data['code'] == ErrorCode.VALIDATION_ERROR
