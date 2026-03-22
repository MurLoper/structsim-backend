"""
SSO 模拟服务。

这里也统一改成以 `domain_account` 作为登录标识。
"""
import datetime
import os

import jwt
from flask import Blueprint, jsonify, request

from app.models.auth import User

sso_bp = Blueprint("sso", __name__, url_prefix="/api/v1/sso")

SSO_SECRET = os.getenv("SSO_SECRET_KEY", "sso-secret-key-change-in-production")
SSO_TOKEN_EXPIRE = int(os.getenv("SSO_TOKEN_EXPIRE", 86400))


def generate_sso_token(domain_account: str):
    payload = {
        "domain_account": domain_account,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=SSO_TOKEN_EXPIRE),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SSO_SECRET, algorithm="HS256")


def verify_sso_token(token):
    try:
        return jwt.decode(token, SSO_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@sso_bp.route("/login", methods=["POST"])
def sso_login():
    data = request.get_json() or {}
    domain_account = str(
        data.get("domain_account") or data.get("domainAccount") or data.get("username") or ""
    ).strip().lower()
    password = data.get("password")

    if not domain_account or not password:
        return jsonify({"error": "域账号和密码不能为空"}), 400

    user = User.query.filter_by(domain_account=domain_account).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "域账号或密码错误"}), 401

    access_token = generate_sso_token(user.domain_account)
    return jsonify(
        {
            "access_token": access_token,
            "user": {
                "id": user.domain_account,
                "domainAccount": user.domain_account,
                "userName": user.user_name,
                "realName": user.real_name,
                "email": user.email,
            },
        }
    )


@sso_bp.route("/verify", methods=["GET"])
def sso_verify():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"valid": False, "error": "缺少 token"}), 401

    token = auth_header.split(" ")[1]
    payload = verify_sso_token(token)
    if not payload:
        return jsonify({"valid": False, "error": "token 无效或已过期"}), 401

    domain_account = str(payload.get("domain_account") or "").strip().lower()
    user = User.query.filter_by(domain_account=domain_account).first()
    if not user:
        return jsonify({"valid": False, "error": "用户不存在"}), 401

    return jsonify(
        {
            "valid": True,
            "user": {
                "id": user.domain_account,
                "domainAccount": user.domain_account,
                "userName": user.user_name,
                "realName": user.real_name,
                "email": user.email,
            },
        }
    )


@sso_bp.route("/logout", methods=["POST"])
def sso_logout():
    return jsonify({"message": "登出成功"})
