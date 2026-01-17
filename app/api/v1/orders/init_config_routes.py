"""
提单初始化 - Routes层
职责：路由定义、参数校验、HTTP响应
"""
from flask import Blueprint, request
from pydantic import ValidationError
from app.common.response import success, error
from app.common.errors import NotFoundError, BusinessError
from app.constants.error_codes import ErrorCode
from .init_config_schemas import OrderInitConfigRequest
from .init_config_service import OrderInitConfigService

init_config_bp = Blueprint('init_config', __name__)
service = OrderInitConfigService()


@init_config_bp.route('/orders/init-config', methods=['GET'])
def get_init_config():
    """
    获取提单初始化配置
    
    Query参数:
        projectId: 项目ID (必填)
        simTypeId: 仿真类型ID (可选，不传则使用项目默认)
    """
    try:
        project_id = request.args.get('projectId', type=int)
        sim_type_id = request.args.get('simTypeId', type=int)
        
        if not project_id:
            return error(code=ErrorCode.VALIDATION_ERROR, msg="projectId 参数必填")
        
        config = service.get_init_config(project_id, sim_type_id)
        return success(data=config)
    except NotFoundError as e:
        return error(code=ErrorCode.NOT_FOUND, msg=str(e))
    except BusinessError as e:
        return error(code=ErrorCode.BUSINESS_ERROR, msg=str(e))
    except Exception as e:
        return error(code=ErrorCode.INTERNAL_ERROR, msg=str(e))

