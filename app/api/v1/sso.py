"""
SSO 模拟服务 - 用于内网单点登录
"""
from flask import Blueprint, request, jsonify, redirect
from app.models.auth import User
from app import db
import jwt
import datetime
from functools import wraps

sso_bp = Blueprint('sso', __name__, url_prefix='/api/v1/sso')

# SSO配置
SSO_SECRET = 'sso-secret-key-change-in-production'
SSO_TOKEN_EXPIRE = 24 * 3600  # 24小时

def generate_sso_token(user_id, username):
    """生成SSO token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=SSO_TOKEN_EXPIRE),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SSO_SECRET, algorithm='HS256')

def verify_sso_token(token):
    """验证SSO token"""
    try:
        payload = jwt.decode(token, SSO_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@sso_bp.route('/login', methods=['POST'])
def sso_login():
    """
    SSO登录接口

    请求体:
    {
        "username": "admin",
        "password": "password"
    }

    返回:
    {
        "access_token": "eyJ...",
        "user": {...}
    }
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    # 验证用户
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401

    # 生成SSO token
    access_token = generate_sso_token(user.id, user.username)

    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.name if user.role else None
        }
    })

@sso_bp.route('/verify', methods=['GET'])
def sso_verify():
    """
    验证SSO token

    请求头: Authorization: Bearer <token>

    返回:
    {
        "valid": true,
        "user": {...}
    }
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'valid': False, 'error': '缺少token'}), 401

    token = auth_header.split(' ')[1]
    payload = verify_sso_token(token)

    if not payload:
        return jsonify({'valid': False, 'error': 'token无效或已过期'}), 401

    # 获取用户信息
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'valid': False, 'error': '用户不存在'}), 401

    return jsonify({
        'valid': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.name if user.role else None
        }
    })

@sso_bp.route('/logout', methods=['POST'])
def sso_logout():
    """
    SSO登出接口

    返回:
    {
        "message": "登出成功"
    }
    """
    # SSO登出通常在客户端删除token即可
    # 如需服务端黑名单，可在此实现
    return jsonify({'message': '登出成功'})
