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
from app.common.serializers import get_snake_json
from .schemas import LoginRequest
from .service import auth_service

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _get_identity_value():
    """读取JWT身份标识（优先域账号，兼容老token）"""
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity.get('domain_account') or identity.get('domainAccount') or identity.get('id')
    return identity


@auth_bp.route('/login-mode', methods=['GET'])
def get_login_mode():
    """获取登录模式配置（前端据此决定跳SSO还是本地登录页）"""
    result = auth_service.get_login_mode()
    return success(result)


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户密码登录（域账号 + 密码）"""
    try:
        validated = LoginRequest(**(get_snake_json() or {}))
        result = auth_service.login(validated.domain_account, validated.password)
        return success(result, "登录成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@auth_bp.route('/sso/callback', methods=['POST'])
def sso_callback_login():
    """SSO回调登录：前端携带uid，后端查询公司信息后签发本站token"""
    try:
        payload = get_snake_json() or {}
        uid = str(payload.get('uid') or '').strip()
        result = auth_service.login_by_uid(uid, request.cookies.to_dict())
        return success(result, "SSO登录成功")
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
        user_identity = _get_identity_value()
        result = auth_service.get_current_user(user_identity)
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
    user_identity = _get_identity_value()
    result = auth_service.logout(user_identity)
    return success(result)


@auth_bp.route('/menus', methods=['GET'])
@jwt_required()
def get_user_menus():
    """获取当前用户的菜单列表（树形结构）"""
    try:
        user_identity = _get_identity_value()
        result = auth_service.get_user_menus(user_identity)
        return success(result)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """验证Token并返回完整用户信息"""
    try:
        user_identity = _get_identity_value()

        user_data = auth_service.get_current_user(user_identity)
        menus = auth_service.get_user_menus(user_identity)

        return success({'user': user_data, 'menus': menus})
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """刷新访问令牌"""
    try:
        user_identity = _get_identity_value()

        user_data = auth_service.get_current_user(user_identity)
        permission_codes = user_data.get('permissionCodes', []) or user_data.get('permission_codes', [])

        new_token = create_access_token(
            identity=str(user_data.get('domain_account') or user_data.get('id') or user_identity),
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

        should_refresh = expires_in < 1800

        return success({
            'valid': True,
            'expiresIn': expires_in,
            'shouldRefresh': should_refresh
        })
    except Exception:
        return error(ErrorCode.UNAUTHORIZED, "登录已过期", http_status=401)
