"""
认证模块 - 路由层
职责：路由定义 + 参数校验 + 调用Service + 返回Response
禁止：复杂业务逻辑、直接SQL操作
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.common import success, error
from app.constants import ErrorCode
from app.common.errors import NotFoundError, BusinessError
from .schemas import LoginRequest
from .service import auth_service

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        validated = LoginRequest(**request.get_json())
        result = auth_service.login(validated.email, validated.password)
        return success(result, "登录成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前登录用户信息"""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str) and identity.isdigit():
            user_id = int(identity)
        else:
            user_id = identity
        result = auth_service.get_current_user(user_id)
        return success(result)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@auth_bp.route('/users', methods=['GET'])
def get_all_users():
    """获取所有用户列表（用于演示登录选择）"""
    result = auth_service.get_all_users()
    return success(result)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        user_id = identity.get('id')
    elif isinstance(identity, str) and identity.isdigit():
        user_id = int(identity)
    else:
        user_id = identity
    result = auth_service.logout(user_id)
    return success(result)

