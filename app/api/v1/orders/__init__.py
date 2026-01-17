"""
订单模块
包含：routes(路由层), service(服务层), repository(仓储层), schemas(数据校验)
"""
from .routes import orders_bp
from .service import orders_service
from .init_config_routes import init_config_bp

__all__ = ['orders_bp', 'orders_service', 'init_config_bp']

