"""
认证模块 - 路由层
职责：路由定义 + 参数校验 + 调用Service + 返回Response
禁止：复杂业务逻辑、直接SQL操作
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
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


@auth_bp.route('/menus', methods=['GET'])
@jwt_required()
def get_user_menus():
    """获取当前用户的菜单列表（树形结构）"""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str) and identity.isdigit():
            user_id = int(identity)
        else:
            user_id = identity
        result = auth_service.get_user_menus(user_id)
        return success(result)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    验证Token并返回完整用户信息（SSO回调使用）
    返回用户信息、权限列表、菜单树
    """
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str) and identity.isdigit():
            user_id = int(identity)
        else:
            user_id = identity

        # 获取用户信息和权限
        user_data = auth_service.get_current_user(user_id)
        # 获取用户菜单
        menus = auth_service.get_user_menus(user_id)

        return success({
            'user': user_data,
            'menus': menus
        })
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """刷新访问令牌"""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str) and identity.isdigit():
            user_id = int(identity)
        else:
            user_id = identity

        # 获取用户权限
        user_data = auth_service.get_current_user(user_id)
        permission_codes = user_data.get('permission_codes', [])

        # 生成新token
        new_token = create_access_token(
            identity=str(user_id),
            additional_claims={'permissions': permission_codes}
        )
        return success({'token': new_token}, "令牌刷新成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@auth_bp.route('/heartbeat', methods=['GET'])
@jwt_required()
def heartbeat():
    """
    心跳检查接口
    用于前端定时检查登录状态，轻量级验证
    返回: valid(是否有效), expiresIn(剩余有效时间秒数)
    """
    from flask_jwt_extended import get_jwt
    import time

    try:
        jwt_data = get_jwt()
        exp = jwt_data.get('exp', 0)
        now = int(time.time())
        expires_in = max(0, exp - now)

        # 如果剩余时间小于30分钟，建议刷新
        should_refresh = expires_in < 1800

        return success({
            'valid': True,
            'expiresIn': expires_in,
            'shouldRefresh': should_refresh
        })
    except Exception:
        return error(ErrorCode.UNAUTHORIZED, "登录已过期", http_status=401)

