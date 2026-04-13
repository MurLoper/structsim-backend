"""
Results module routes.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.common import error, success
from app.common.errors import NotFoundError
from app.common.serializers import get_snake_json
from app.constants import ErrorCode
from .schemas import RoundsQueryParams, UpdateStatusRequest
from .service import results_service

results_bp = Blueprint("results", __name__, url_prefix="/results")


@results_bp.route("/order/<int:order_id>/sim-types", methods=["GET"])
@jwt_required()
def get_order_sim_type_results(order_id: int):
    try:
        return success(results_service.get_order_sim_type_results(order_id))
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(exc), http_status=404)


@results_bp.route("/sim-type/<int:result_id>", methods=["GET"])
@jwt_required()
def get_sim_type_result(result_id: int):
    try:
        return success(results_service.get_sim_type_result(result_id))
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(exc), http_status=404)


@results_bp.route("/sim-type/<int:sim_type_result_id>/rounds", methods=["GET"])
@jwt_required()
def get_rounds(sim_type_result_id: int):
    try:
        validated = RoundsQueryParams(
            page=request.args.get("page", 1, type=int),
            page_size=int(request.args.get("page_size") or request.args.get("pageSize") or 100),
            status=request.args.get("status", type=int),
        )
        return success(
            results_service.get_rounds(
                sim_type_result_id=sim_type_result_id,
                page=validated.page,
                page_size=validated.page_size,
                status=validated.status,
            )
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(exc), http_status=404)


@results_bp.route("/order/<int:order_id>/cases", methods=["GET"])
@jwt_required()
def get_order_case_results(order_id: int):
    return success(results_service.get_order_case_results(order_id))


@results_bp.route("/sim-type/<int:result_id>/status", methods=["PATCH"])
@jwt_required()
def update_sim_type_result_status(result_id: int):
    try:
        data = get_snake_json() or {}
        validated = UpdateStatusRequest(**data)
        return success(
            results_service.update_sim_type_result_status(
                result_id=result_id,
                status=validated.status,
                progress=validated.progress,
            )
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(exc), http_status=404)


@results_bp.route("/round/<int:round_id>/status", methods=["PATCH"])
@jwt_required()
def update_round_status(round_id: int):
    try:
        data = get_snake_json() or {}
        validated = UpdateStatusRequest(**data)
        return success(
            results_service.update_round_status(
                round_id=round_id,
                status=validated.status,
                progress=validated.progress,
                error_msg=validated.error_msg,
            )
        )
    except ValidationError as exc:
        return error(ErrorCode.VALIDATION_ERROR, str(exc), http_status=400)
    except NotFoundError as exc:
        return error(ErrorCode.RESOURCE_NOT_FOUND, str(exc), http_status=404)
