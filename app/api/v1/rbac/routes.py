"""
RBAC - 路由层
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.common import success, error
from app.common.errors import NotFoundError, BusinessError
from app.common.serializers import get_snake_json
from app.constants import ErrorCode
from .schemas import (
    UserCreate, UserUpdate,
    RoleCreate, RoleUpdate,
    PermissionCreate, PermissionUpdate
)
from .service import rbac_service

rbac_bp = Blueprint('rbac', __name__, url_prefix='/rbac')


# ============ 用户管理 ============
@rbac_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    data = rbac_service.list_users()
    return success(data)


@rbac_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    try:
        validated = UserCreate(**(get_snake_json() or {}))
        result = rbac_service.create_user(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@rbac_bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id: int):
    try:
        validated = UserUpdate(**(get_snake_json() or {}))
        result = rbac_service.update_user(id, validated.model_dump(exclude_unset=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
    except BusinessError as e:
        return error(e.code, e.msg, http_status=400)


@rbac_bp.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id: int):
    try:
        rbac_service.delete_user(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 角色管理 ============
@rbac_bp.route('/roles', methods=['GET'])
@jwt_required()
def list_roles():
    data = rbac_service.list_roles()
    return success(data)


@rbac_bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    try:
        validated = RoleCreate(**(get_snake_json() or {}))
        result = rbac_service.create_role(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@rbac_bp.route('/roles/<int:id>', methods=['PUT'])
@jwt_required()
def update_role(id: int):
    try:
        validated = RoleUpdate(**(get_snake_json() or {}))
        result = rbac_service.update_role(id, validated.model_dump(exclude_unset=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@rbac_bp.route('/roles/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_role(id: int):
    try:
        rbac_service.delete_role(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


# ============ 权限管理 ============
@rbac_bp.route('/permissions', methods=['GET'])
@jwt_required()
def list_permissions():
    data = rbac_service.list_permissions()
    return success(data)


@rbac_bp.route('/permissions', methods=['POST'])
@jwt_required()
def create_permission():
    try:
        validated = PermissionCreate(**(get_snake_json() or {}))
        result = rbac_service.create_permission(validated.model_dump())
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)


@rbac_bp.route('/permissions/<int:id>', methods=['PUT'])
@jwt_required()
def update_permission(id: int):
    try:
        validated = PermissionUpdate(**(get_snake_json() or {}))
        result = rbac_service.update_permission(id, validated.model_dump(exclude_unset=True))
        return success(result, "更新成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)


@rbac_bp.route('/permissions/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_permission(id: int):
    try:
        rbac_service.delete_permission(id)
        return success(msg="删除成功")
    except NotFoundError as e:
        return error(ErrorCode.RESOURCE_NOT_FOUND, e.msg, http_status=404)
