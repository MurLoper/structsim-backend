"""
订单模块 - 业务逻辑层
职责：处理业务逻辑、调用Repository、事务管理
禁止：直接处理HTTP请求/响应、直接操作数据库
"""
import time
import datetime
from typing import Dict, List
from math import ceil

from app.common.errors import NotFoundError, BusinessError
from app.constants import ErrorCode
from .repository import orders_repository


def generate_order_no() -> str:
    """生成订单编号"""
    now = datetime.datetime.now()
    return f"ORD-{now.strftime('%Y%m%d')}-{int(time.time() * 1000) % 100000:05d}"


class OrdersService:
    """订单服务"""
    
    def __init__(self):
        self.repository = orders_repository
    
    def get_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: int = None,
        project_id: int = None,
        sim_type_id: int = None,
        order_no: str = None,
        created_by: int = None,
        start_date: int = None,
        end_date: int = None
    ) -> Dict:
        """
        获取订单列表（分页）
        Args:
            page: 页码
            page_size: 每页数量
            status: 订单状态筛选
            project_id: 项目ID筛选
            sim_type_id: 仿真类型ID筛选
            order_no: 订单编号模糊搜索
            created_by: 创建人ID筛选
            start_date: 开始日期时间戳
            end_date: 结束日期时间戳
        Returns:
            包含订单列表和分页信息的字典
        """
        orders, total = self.repository.get_orders_paginated(
            page=page,
            page_size=page_size,
            status=status,
            project_id=project_id,
            sim_type_id=sim_type_id,
            order_no=order_no,
            created_by=created_by,
            start_date=start_date,
            end_date=end_date
        )

        return {
            'items': [order.to_list_dict() for order in orders],
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': ceil(total / page_size) if total > 0 else 0
        }
    
    def get_order(self, order_id: int) -> Dict:
        """
        获取订单详情
        Args:
            order_id: 订单ID
        Returns:
            订单详情字典
        Raises:
            NotFoundError: 订单不存在
        """
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise NotFoundError("订单不存在")
        
        return order.to_dict()
    
    def create_order(self, order_data: dict, user_id: int) -> Dict:
        """
        创建订单
        Args:
            order_data: 订单数据
            user_id: 创建用户ID
        Returns:
            创建的订单信息
        """
        # 准备订单数据
        origin_file = order_data.get('originFile', {})
        
        order_dict = {
            'order_no': generate_order_no(),
            'project_id': order_data.get('projectId'),
            'origin_file_type': origin_file.get('type', 1),
            'origin_file_name': origin_file.get('name'),
            'origin_file_path': origin_file.get('path'),
            'origin_file_id': origin_file.get('fileId'),
            'fold_type_id': order_data.get('foldTypeId'),
            'participant_uids': order_data.get('participantUids', []),
            'remark': order_data.get('remark'),
            'sim_type_ids': order_data.get('simTypeIds', []),
            'opt_param': order_data.get('optParam', {}),
            'workflow_id': order_data.get('workflowId'),
            'submit_check': order_data.get('submitCheck'),
            'client_meta': order_data.get('clientMeta'),
            'created_by': user_id,
            'status': 1,  # 待处理
            'progress': 0
        }
        
        order = self.repository.create_order(order_dict)
        return order.to_dict()
    
    def update_order(self, order_id: int, update_data: dict) -> Dict:
        """
        更新订单
        Args:
            order_id: 订单ID
            update_data: 更新数据
        Returns:
            更新后的订单信息
        Raises:
            NotFoundError: 订单不存在
        """
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise NotFoundError("订单不存在")
        
        # 只允许更新特定字段
        allowed_fields = ['remark', 'participant_uids', 'opt_param']
        filtered_data = {
            k: v for k, v in update_data.items() 
            if k in allowed_fields and v is not None
        }
        
        order = self.repository.update_order(order, filtered_data)
        return order.to_dict()
    
    def delete_order(self, order_id: int) -> None:
        """
        删除订单
        Args:
            order_id: 订单ID
        Raises:
            NotFoundError: 订单不存在
            BusinessError: 订单状态不允许删除
        """
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise NotFoundError("订单不存在")
        
        # 只有待处理状态可以删除
        if order.status != 1:
            raise BusinessError(
                ErrorCode.VALIDATION_ERROR,
                "只有待处理状态的订单可以删除"
            )
        
        self.repository.delete_order(order)


# 单例实例
orders_service = OrdersService()

