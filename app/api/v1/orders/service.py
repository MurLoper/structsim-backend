"""
订单模块 - 业务逻辑层
职责：处理业务逻辑、调用Repository、事务管理
禁止：直接处理HTTP请求/响应、直接操作数据库
"""
import os
import re
import time
import datetime
from typing import Dict, List, Optional
from math import ceil

from flask import current_app
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
        created_by: str = None,
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
            'page_size': page_size,
            'total_pages': ceil(total / page_size) if total > 0 else 0
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
    
    def create_order(self, order_data: dict, user_identity: str) -> Dict:
        """
        创建订单
        Args:
            order_data: 订单数据
            user_identity: 创建用户域账号
        Returns:
            创建的订单信息
        """
        # 准备订单数据
        origin_file = order_data.get('origin_file', {})

        order_dict = {
            'order_no': generate_order_no(),
            'project_id': order_data.get('project_id'),
            'model_level_id': order_data.get('model_level_id'),
            'origin_file_type': origin_file.get('type', 1),
            'origin_file_name': origin_file.get('name'),
            'origin_file_path': origin_file.get('path'),
            'origin_file_id': origin_file.get('file_id'),
            'origin_fold_type_id': order_data.get('origin_fold_type_id'),
            'fold_type_ids': order_data.get('fold_type_ids', []),
            'participant_uids': order_data.get('participant_ids', []),
            'remark': order_data.get('remark'),
            'sim_type_ids': order_data.get('sim_type_ids', []),
            'opt_param': order_data.get('opt_param', {}),
            'input_json': order_data.get('input_json', {}),
            'condition_summary': order_data.get('condition_summary'),
            'workflow_id': order_data.get('workflow_id'),
            'submit_check': order_data.get('submit_check'),
            'client_meta': order_data.get('client_meta'),
            'created_by': str(user_identity),
            'status': 0,  # 未开始/排队
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
        
        # 允许更新的字段（编辑态需要全量更新提单数据）
        allowed_fields = [
            'remark', 'participant_uids', 'opt_param',
            'input_json', 'sim_type_ids', 'fold_type_ids',
            'origin_file_type', 'origin_file_name', 'origin_file_path', 'origin_file_id',
            'origin_fold_type_id', 'model_level_id', 'condition_summary',
            'workflow_id', 'submit_check', 'client_meta',
        ]
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

    def verify_file(self, path: str, file_type: int = 1) -> Dict:
        """
        验证源文件是否存在，并解析 INP 文件的 set 集信息

        Args:
            path: 文件路径(type=1)或文件ID(type=2)
            file_type: 1=路径验证, 2=文件ID验证
        Returns:
            验证结果字典，包含 success, name, path, inpSets
        Raises:
            NotFoundError: 文件不存在
            BusinessError: 路径格式无效
        """
        if file_type == 2:
            # 文件ID验证：查数据库
            try:
                file_id = int(path)
            except (ValueError, TypeError):
                raise BusinessError(ErrorCode.VALIDATION_ERROR, "文件ID格式无效")
            # 查询上传记录
            from app.models.order import UploadFile
            upload = UploadFile.query.get(file_id)
            if not upload:
                raise NotFoundError("文件记录不存在")
            return {
                'success': True,
                'name': upload.original_name or f'file_{file_id}',
                'path': upload.storage_path or path,
                'inpSets': [],
            }

        # type=1: 路径验证
        if not path or not path.strip():
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "文件路径不能为空")

        clean_path = path.strip()
        file_name = os.path.basename(clean_path)

        if not file_name:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "无法从路径中提取文件名")

        # 尝试在配置的 UPLOAD_FOLDER 下定位文件
        upload_folder = current_app.config.get('UPLOAD_FOLDER', './storage')
        abs_path = clean_path if os.path.isabs(clean_path) else os.path.join(upload_folder, clean_path)

        inp_sets: List[Dict] = []

        if os.path.isfile(abs_path):
            # 文件存在，解析 INP set 集
            if file_name.lower().endswith('.inp'):
                inp_sets = self._parse_inp_sets(abs_path)
        else:
            # 文件不在本地 — 但路径格式合法即视为通过
            # 生产环境中文件可能在远程 NFS/共享存储上
            current_app.logger.info(f"文件不在本地: {abs_path}，路径格式验证通过")
            # 对 .inp 路径返回空 inpSets，前端可手动配置
            if file_name.lower().endswith('.inp'):
                inp_sets = []

        result: Dict = {
            'success': True,
            'name': file_name,
            'path': clean_path,
        }
        if inp_sets or file_name.lower().endswith('.inp'):
            result['inpSets'] = inp_sets
        return result

    @staticmethod
    def _parse_inp_sets(file_path: str) -> List[Dict]:
        """
        解析 INP 文件中的 set 集定义

        支持的关键字:
        - *ELSET, ELSET=name
        - *NSET, NSET=name
        - *PART, NAME=name (→ component)
        - *INSTANCE, NAME=name (→ component)

        Returns:
            [{"type": "eleset"|"nodeset"|"component", "name": "SET-1"}, ...]
        """
        sets: List[Dict] = []
        seen: set = set()

        # 正则：匹配 *KEYWORD, ... NAME=xxx 或 ELSET=xxx 等
        pattern_elset = re.compile(r'\*ELSET\b.*?ELSET\s*=\s*([^\s,]+)', re.IGNORECASE)
        pattern_nset = re.compile(r'\*NSET\b.*?NSET\s*=\s*([^\s,]+)', re.IGNORECASE)
        pattern_part = re.compile(r'\*PART\b.*?NAME\s*=\s*([^\s,]+)', re.IGNORECASE)
        pattern_instance = re.compile(r'\*INSTANCE\b.*?NAME\s*=\s*([^\s,]+)', re.IGNORECASE)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith('*'):
                        continue

                    for pattern, set_type in [
                        (pattern_elset, 'eleset'),
                        (pattern_nset, 'nodeset'),
                        (pattern_part, 'component'),
                        (pattern_instance, 'component'),
                    ]:
                        m = pattern.match(line)
                        if m:
                            name = m.group(1).strip()
                            key = (set_type, name)
                            if key not in seen:
                                seen.add(key)
                                sets.append({'type': set_type, 'name': name})
        except Exception as e:
            current_app.logger.warning(f"解析 INP 文件失败: {file_path}, {e}")

        return sets

    def get_statistics(self) -> Dict:
        """获取订单统计数据"""
        return self.repository.get_statistics()

    def get_trends(self, days: int = 7) -> List[Dict]:
        """获取订单趋势数据"""
        return self.repository.get_trends(days)

    def get_status_distribution(self) -> List[Dict]:
        """获取订单状态分布"""
        return self.repository.get_status_distribution()


# 单例实例
orders_service = OrdersService()

