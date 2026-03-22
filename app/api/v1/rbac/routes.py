"""
RBAC 路由层。
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.common import error, success
from app.common.errors import BusinessError, NotFoundError
from app.common.serializers import get_snake_json
from app.constants import ErrorCode
from .schemas import (
    MenuCreate,
    MenuUpdate,
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from .service import rbac_service

rbac_bp = Blueprint("rbac", __name__, url_prefix="/rbac")


@rbac_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    return success(rbac_service.list_users())


@rbac_bp.route("/users", methods=["POST"])
@jwt_required()
def create_user():
    try:
        validated = UserCreate(**(get_snake_json() or {}))
        return success(rbac_service.create_user(validated.model_dump()), "创建成功")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/users/<string:domain_account>", methods=["PUT"])
@jwt_required()
def update_user(domain_account: str):
    try:
        validated = UserUpdate(**(get_snake_json() or {}))
        return success(
            rbac_service.update_user(domain_account, validated.model_dump(exclude_unset=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/users/<string:domain_account>", methods=["DELETE"])
@jwt_required()
def delete_user(domain_account: str):
    try:
        rbac_service.delete_user(domain_account)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)


@rbac_bp.route("/roles", methods=["GET"])
@jwt_required()
def list_roles():
    return success(rbac_service.list_roles())


@rbac_bp.route("/roles", methods=["POST"])
@jwt_required()
def create_role():
    try:
        validated = RoleCreate(**(get_snake_json() or {}))
        return success(rbac_service.create_role(validated.model_dump()), "创建成功")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/roles/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_role(item_id: int):
    try:
        validated = RoleUpdate(**(get_snake_json() or {}))
        return success(
            rbac_service.update_role(item_id, validated.model_dump(exclude_unset=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/roles/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_role(item_id: int):
    try:
        rbac_service.delete_role(item_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)


@rbac_bp.route("/permissions", methods=["GET"])
@jwt_required()
def list_permissions():
    return success(rbac_service.list_permissions())


@rbac_bp.route("/permissions", methods=["POST"])
@jwt_required()
def create_permission():
    try:
        validated = PermissionCreate(**(get_snake_json() or {}))
        return success(rbac_service.create_permission(validated.model_dump()), "创建成功")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/permissions/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_permission(item_id: int):
    try:
        validated = PermissionUpdate(**(get_snake_json() or {}))
        return success(
            rbac_service.update_permission(item_id, validated.model_dump(exclude_unset=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/permissions/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_permission(item_id: int):
    try:
        rbac_service.delete_permission(item_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)


@rbac_bp.route("/menus", methods=["GET"])
@jwt_required()
def list_menus():
    return success(rbac_service.list_menus())


@rbac_bp.route("/menus", methods=["POST"])
@jwt_required()
def create_menu():
    try:
        validated = MenuCreate(**(get_snake_json() or {}))
        return success(rbac_service.create_menu(validated.model_dump()), "创建成功")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/menus/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_menu(item_id: int):
    try:
        validated = MenuUpdate(**(get_snake_json() or {}))
        return success(
            rbac_service.update_menu(item_id, validated.model_dump(exclude_unset=True)),
            "更新成功",
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@rbac_bp.route("/menus/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_menu(item_id: int):
    try:
        rbac_service.delete_menu(item_id)
        return success(msg="删除成功")
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)
