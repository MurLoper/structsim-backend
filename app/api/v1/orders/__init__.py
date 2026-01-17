"""
订单模块
包含：routes(路由层), service(服务层), repository(仓储层), schemas(数据校验)
"""
from .routes import orders_bp
from .service import orders_service

__all__ = ['orders_bp', 'orders_service']

