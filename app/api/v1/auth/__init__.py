"""
认证模块
包含：routes(路由层), service(服务层), repository(仓储层), schemas(数据校验)
"""
from .routes import auth_bp
from .service import auth_service

__all__ = ['auth_bp', 'auth_service']

