"""
订单模块 - 数据访问层
职责：封装所有数据库操作，提供数据访问接口
禁止：业务逻辑、HTTP相关代码
"""
from typing import Optional, List, Tuple
from sqlalchemy import desc
from app.models.order import Order, OrderResult
from app.extensions import db


class OrdersRepository:
    """订单相关数据访问"""
    
    @staticmethod
    def get_orders_paginated(
        page: int,
        page_size: int,
        status: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Tuple[List[Order], int]:
        """
        分页获取订单列表
        Returns:
            (订单列表, 总数)
        """
        query = Order.query
        
        if status is not None:
            query = query.filter_by(status=status)
        if project_id is not None:
            query = query.filter_by(project_id=project_id)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        orders = query.order_by(desc(Order.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return orders, total
    
    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Order]:
        """根据ID获取订单"""
        return Order.query.get(order_id)
    
    @staticmethod
    def create_order(order_data: dict) -> Order:
        """创建订单"""
        order = Order(**order_data)
        db.session.add(order)
        db.session.commit()
        return order
    
    @staticmethod
    def update_order(order: Order, update_data: dict) -> Order:
        """更新订单"""
        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        db.session.commit()
        return order
    
    @staticmethod
    def delete_order(order: Order) -> None:
        """删除订单"""
        db.session.delete(order)
        db.session.commit()
    
    @staticmethod
    def get_order_result(order_id: int) -> Optional[OrderResult]:
        """获取订单结果"""
        return OrderResult.query.filter_by(order_id=order_id).first()


# 单例实例
orders_repository = OrdersRepository()

