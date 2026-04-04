"""
平台内容与埋点路由。
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.common import error, success
from app.common.decorators import require_permission
from app.common.errors import BusinessError, NotFoundError
from app.common.serializers import get_snake_json
from app.constants import ErrorCode
from .schemas import (
    AnalyticsQueryRequest,
    AnnouncementUpsertRequest,
    PlatformSettingsUpdateRequest,
    PrivacyAcceptRequest,
    TrackingEventBatchRequest,
)
from .service import platform_service

platform_bp = Blueprint("platform", __name__, url_prefix="/platform")


def _get_identity_value():
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity.get("domain_account") or identity.get("domainAccount")
    return identity


@platform_bp.route("/bootstrap", methods=["GET"])
@jwt_required()
def get_platform_bootstrap():
    return success(platform_service.get_bootstrap(_get_identity_value()))


@platform_bp.route("/privacy-policy", methods=["GET"])
@jwt_required()
def get_privacy_policy():
    return success(platform_service.get_privacy_policy(_get_identity_value()))


@platform_bp.route("/privacy-policy/accept", methods=["POST"])
@jwt_required()
def accept_privacy_policy():
    try:
        validated = PrivacyAcceptRequest(**(get_snake_json() or {}))
        result = platform_service.accept_privacy_policy(
            _get_identity_value(),
            accepted_ip=request.headers.get("X-Forwarded-For", request.remote_addr),
            policy_version=validated.policy_version,
        )
        return success(result, "隐私协议已确认")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/events", methods=["POST"])
@jwt_required()
def track_platform_events():
    try:
        validated = TrackingEventBatchRequest(**(get_snake_json() or {}))
        result = platform_service.track_events(_get_identity_value(), validated.model_dump()["events"])
        return success(result, "埋点已接收")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


def _get_days_query() -> int:
    validated = AnalyticsQueryRequest(days=int(request.args.get("days") or 7))
    return validated.days


@platform_bp.route("/analytics/summary", methods=["GET"])
@jwt_required()
@require_permission("VIEW_DASHBOARD")
def get_platform_analytics_summary():
    try:
        return success(platform_service.get_analytics_summary(_get_identity_value(), _get_days_query()))
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/analytics/features", methods=["GET"])
@jwt_required()
@require_permission("VIEW_DASHBOARD")
def get_platform_analytics_features():
    try:
        return success(platform_service.get_analytics_features(_get_identity_value(), _get_days_query()))
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/analytics/funnels", methods=["GET"])
@jwt_required()
@require_permission("VIEW_DASHBOARD")
def get_platform_analytics_funnels():
    try:
        return success(platform_service.get_analytics_funnels(_get_identity_value(), _get_days_query()))
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/analytics/failures", methods=["GET"])
@jwt_required()
@require_permission("VIEW_DASHBOARD")
def get_platform_analytics_failures():
    try:
        return success(platform_service.get_analytics_failures(_get_identity_value(), _get_days_query()))
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/admin/content", methods=["GET"])
@jwt_required()
@require_permission("MANAGE_CONFIG")
def get_admin_platform_content():
    try:
        return success(platform_service.get_admin_content(_get_identity_value()))
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/admin/content", methods=["PUT"])
@jwt_required()
@require_permission("MANAGE_CONFIG")
def update_admin_platform_content():
    try:
        validated = PlatformSettingsUpdateRequest(**(get_snake_json() or {}))
        payload = validated.model_dump(exclude_none=True)
        return success(platform_service.update_settings(_get_identity_value(), payload), "配置已更新")
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/admin/announcements", methods=["POST"])
@jwt_required()
@require_permission("MANAGE_CONFIG")
def create_admin_announcement():
    try:
        validated = AnnouncementUpsertRequest(**(get_snake_json() or {}))
        return success(
            platform_service.create_announcement(_get_identity_value(), validated.model_dump()),
            "公告已创建",
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/admin/announcements/<int:announcement_id>", methods=["PUT"])
@jwt_required()
@require_permission("MANAGE_CONFIG")
def update_admin_announcement(announcement_id: int):
    try:
        validated = AnnouncementUpsertRequest(**(get_snake_json() or {}))
        return success(
            platform_service.update_announcement(
                _get_identity_value(), announcement_id, validated.model_dump()
            ),
            "公告已更新",
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)


@platform_bp.route("/admin/announcements/<int:announcement_id>", methods=["DELETE"])
@jwt_required()
@require_permission("MANAGE_CONFIG")
def delete_admin_announcement(announcement_id: int):
    try:
        platform_service.delete_announcement(_get_identity_value(), announcement_id)
        return success(msg="公告已删除")
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, exc.msg, http_status=404)
    except BusinessError as exc:
        return error(exc.code, exc.msg, http_status=400)
