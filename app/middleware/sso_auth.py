"""
SSO认证中间件
"""
from functools import wraps
from flask import request, jsonify, g
from app.api.v1.sso import verify_sso_token
from app.models.auth import User

def sso_required(f):
    """SSO认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权访问'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_sso_token(token)

        if not payload:
            return jsonify({'error': 'token无效或已过期'}), 401

        # 将用户信息存入g对象
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': '用户不存在'}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated
