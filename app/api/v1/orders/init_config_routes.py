"""
提单项目上下文初始化路由。
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.common.errors import BusinessError, NotFoundError
from app.common.response import error, success
from app.constants.error_codes import ErrorCode
from .init_config_service import OrderInitConfigService

init_config_bp = Blueprint("init_config", __name__)
service = OrderInitConfigService()


def _resolve_user_identity() -> str:
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return str(
            identity.get("domain_account")
            or identity.get("domainAccount")
            or identity.get("id")
            or ""
        )
    return str(identity or "")


def _get_project_init_config_response():
    try:
        project_id = request.args.get("projectId", type=int)
        sim_type_id = request.args.get("simTypeId", type=int)

        if not project_id:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="projectId 参数必填")

        config = service.get_init_config(project_id, sim_type_id, _resolve_user_identity())
        return success(data=config)
    except NotFoundError as exc:
        return error(code=ErrorCode.NOT_FOUND, msg=str(exc))
    except BusinessError as exc:
        return error(code=exc.code, msg=exc.msg)
    except Exception as exc:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(exc))


@init_config_bp.route("/orders/init-project-config", methods=["GET"])
@jwt_required()
def get_project_init_config():
    """获取提单项目上下文。"""

    return _get_project_init_config_response()


@init_config_bp.route("/orders/init-config", methods=["GET"])
@jwt_required()
def get_init_config_compat():
    """兼容旧路由，内部转发到新的项目上下文实现。"""

    return _get_project_init_config_response()
