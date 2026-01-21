import os
import uuid
import time
import json
import logging
from flask import Flask, g, request
from flask_cors import CORS
from flasgger import Swagger

from config import config
from app.extensions import db, migrate, jwt, init_extensions
from app.common import error
from app.common.errors import BusinessError
from app.constants import ErrorCode
from app.openapi import OPENAPI_SPEC

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

    def build_request_context():
        payload = {
            'trace_id': getattr(g, 'trace_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'query': request.args.to_dict(flat=True),
            'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
            'user_agent': request.headers.get('User-Agent'),
        }
        try:
            body = request.get_json(silent=True) or None
            if isinstance(body, dict):
                payload['body_keys'] = list(body.keys())
            elif body is not None:
                payload['body_type'] = type(body).__name__
        except Exception:
            payload['body_keys'] = []
        return payload

    # 请求前处理：生成trace_id
    @app.before_request
    def before_request():
        g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])
        g.request_start = time.time()

    @app.after_request
    def after_request(response):
        duration_ms = (time.time() - getattr(g, 'request_start', time.time())) * 1000
        context = build_request_context()
        context.update({'status': response.status_code, 'duration_ms': round(duration_ms, 2)})
        logger.info(json.dumps({'event': 'request', **context}, ensure_ascii=False))
        return response

    # 全局异常处理
    @app.errorhandler(BusinessError)
    def handle_business_error(e):
        context = build_request_context()
        context.update({'error_code': e.code, 'error_msg': e.msg})
        logger.warning(json.dumps({'event': 'business_error', **context}, ensure_ascii=False))
        return error(e.code, e.msg, e.data)

    @app.errorhandler(Exception)
    def handle_exception(e):
        context = build_request_context()
        context.update({'error_msg': str(e)})
        logger.error(json.dumps({'event': 'unhandled_error', **context}, ensure_ascii=False), exc_info=True)
        return error(ErrorCode.INTERNAL_ERROR, str(e), http_status=500)

    # 注册蓝图 - 旧版API (兼容)
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 注册蓝图 - 新版API v1
    from app.api.v1 import v1_bp
    app.register_blueprint(v1_bp, url_prefix='/api/v1')

    # Swagger / OpenAPI
    swagger_config = {
        'headers': [],  # 必须提供，否则 flasgger 会报错
        'specs': [
            {
                'endpoint': 'openapi',
                'route': '/api/docs.json',
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True,
            }
        ],
        'specs_route': '/api/docs',
    }
    Swagger(app, template=OPENAPI_SPEC, config=swagger_config)

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'trace_id': getattr(g, 'trace_id', None)}

    logger.info(f"App created with config: {config_name}")
    return app

