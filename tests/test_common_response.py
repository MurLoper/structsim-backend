from app.common.response import success, error, paginated
from app.constants import ErrorCode


def test_success_response(app):
    with app.test_request_context():
        resp = success({'ok': True}, 'done')
        payload = resp.get_json()
        assert payload['code'] == ErrorCode.SUCCESS
        assert payload['msg'] == 'done'
        assert payload['data'] == {'ok': True}
        assert 'trace_id' in payload


def test_error_response(app):
    with app.test_request_context():
        resp, status = error(ErrorCode.VALIDATION_ERROR, 'bad', {'field': 'x'}, http_status=400)
        payload = resp.get_json()
        assert status == 400
        assert payload['code'] == ErrorCode.VALIDATION_ERROR
        assert payload['msg'] == 'bad'
        assert payload['data'] == {'field': 'x'}
        assert 'trace_id' in payload


def test_paginated_response(app):
    with app.test_request_context():
        resp = paginated([{'id': 1}], total=10, page=1, page_size=5)
        payload = resp.get_json()
        assert payload['code'] == ErrorCode.SUCCESS
        assert payload['data']['total_pages'] == 2
        assert payload['data']['items'] == [{'id': 1}]
