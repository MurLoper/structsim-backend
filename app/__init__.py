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
from app.common.serializers import dict_keys_to_snake, dict_keys_to_camel
from app.common.redis_client import redis_client
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

    # 初始化 Redis（可选，如果配置了 Redis）
    try:
        redis_client.init_app(app)
        logger.info("Redis 初始化成功")
    except Exception as e:
        logger.warning(f"Redis 初始化失败，将使用数据库直接查询: {e}")

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

    # 请求前处理：生成trace_id，转换请求参数为snake_case
    @app.before_request
    def before_request():
        g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])
        g.request_start = time.time()

        # 将请求JSON body中的camelCase转换为snake_case
        if request.is_json and request.data:
            try:
                original_json = request.get_json(silent=True)
                if original_json:
                    g.original_json = original_json
                    g.snake_json = dict_keys_to_snake(original_json)
            except Exception:
                pass

    @app.after_request
    def after_request(response):
        duration_ms = (time.time() - getattr(g, 'request_start', time.time())) * 1000
        context = build_request_context()
        context.update({'status': response.status_code, 'duration_ms': round(duration_ms, 2)})
        logger.info(json.dumps({'event': 'request', **context}, ensure_ascii=False))

        # 将响应JSON中的snake_case转换为camelCase
        if response.content_type and 'application/json' in response.content_type:
            try:
                data = response.get_json()
                if data and isinstance(data, dict):
                    # 转换data字段内容为camelCase
                    if 'data' in data and data['data'] is not None:
                        data['data'] = dict_keys_to_camel(data['data'])
                    response.set_data(json.dumps(data, ensure_ascii=False))
            except Exception:
                pass

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

