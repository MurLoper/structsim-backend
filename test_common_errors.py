from app.common.errors import BusinessError, ValidationError, NotFoundError, PermissionError, AuthenticationError
from app.constants import ErrorCode


def test_business_error_to_dict():
    error = BusinessError(ErrorCode.PARAM_INVALID, msg='参数错误', data={'field': 'name'})
    data = error.to_dict()

    assert data['code'] == ErrorCode.PARAM_INVALID
    assert data['msg'] == '参数错误'
    assert data['data']['field'] == 'name'


def test_validation_error():
    error = ValidationError('校验失败', errors=['field missing'])
    data = error.to_dict()

    assert data['code'] == ErrorCode.VALIDATION_ERROR
    assert 'errors' in data['data']


def test_not_found_error_message():
    error = NotFoundError('项目', 99)
    assert error.msg == '项目 (ID: 99) 不存在'


def test_permission_error():
    error = PermissionError()
    assert error.code == ErrorCode.PERMISSION_DENIED


def test_authentication_error_default():
    error = AuthenticationError()
    assert error.code == ErrorCode.TOKEN_INVALID
