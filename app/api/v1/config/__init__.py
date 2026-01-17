"""
配置中心模块
包含：routes(路由层), service(服务层), repository(仓储层), schemas(数据校验)
"""
from .routes import config_bp
from .service import config_service

__all__ = ['config_bp', 'config_service']

