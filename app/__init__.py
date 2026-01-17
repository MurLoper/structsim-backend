import os
import uuid
import logging
from flask import Flask, g, request
from flask_cors import CORS

from config import config
from app.extensions import db, migrate, jwt, init_extensions
from app.common import error
from app.common.errors import BusinessError
from app.constants import ErrorCode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    init_extensions(app)

    # 请求前处理：生成trace_id
    @app.before_request
    def before_request():
        g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])

    # 全局异常处理
    @app.errorhandler(BusinessError)
    def handle_business_error(e):
        logger.warning(f"[{getattr(g, 'trace_id', 'unknown')}] BusinessError: {e.msg}")
        return error(e.code, e.msg, e.data)

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"[{getattr(g, 'trace_id', 'unknown')}] Unhandled error: {e}", exc_info=True)
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)

    # 注册蓝图 - 旧版API (兼容)
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 注册蓝图 - 新版API v1
    from app.api.v1 import v1_bp
    app.register_blueprint(v1_bp, url_prefix='/api/v1')

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'trace_id': getattr(g, 'trace_id', None)}

    logger.info(f"App created with config: {config_name}")
    return app

