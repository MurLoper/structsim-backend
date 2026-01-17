"""
Flask扩展初始化
集中管理所有扩展，便于维护和测试
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 数据库
db = SQLAlchemy()
migrate = Migrate()

# JWT认证
jwt = JWTManager()

# CORS
cors = CORS()

# Redis缓存 (预留)
# from flask_caching import Cache
# cache = Cache()

# 限流器 (预留)
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# limiter = Limiter(key_func=get_remote_address)


def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', ['*']), supports_credentials=True)
    
    # 预留: Redis缓存初始化
    # if app.config.get('CACHE_TYPE'):
    #     cache.init_app(app)
    
    # 预留: 限流器初始化
    # if app.config.get('RATELIMIT_ENABLED'):
    #     limiter.init_app(app)

