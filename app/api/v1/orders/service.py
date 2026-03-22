"""
订单模块 - 业务逻辑层
职责：处理业务逻辑、调用Repository、事务管理
禁止：直接处理HTTP请求/响应、直接操作数据库
"""
import os
import re
import time
import datetime
from typing import Any, Dict, List, Optional
from math import ceil

from flask import current_app
from app.common.errors import NotFoundError, BusinessError
from app.constants import ErrorCode
from app.models.auth import User, Role
from .repository import orders_repository


def generate_order_no() -> str:
    """生成订单编号"""
    now = datetime.datetime.now()
    return f"ORD-{now.strftime('%Y%m%d')}-{int(time.time() * 1000) % 100000:05d}"


class OrdersService:
    """订单服务"""
    
    def __init__(self):
        self.repository = orders_repository

    @staticmethod
    def _to_int(value: object, default: int = 0) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default

    def _estimate_rounds_from_opt_params(self, opt_params: Optional[dict]) -> int:
        if not isinstance(opt_params, dict):
            return 0

        alg_type = self._to_int(opt_params.get('alg_type', opt_params.get('algType', 2)), 2)

        if alg_type in (2, 5):
            doe_data = opt_params.get('doe_param_data', opt_params.get('doeParamData'))
            return len(doe_data) if isinstance(doe_data, list) else 0

        if alg_type != 1:
            return 0

        batch_size_type = self._to_int(opt_params.get('batch_size_type', opt_params.get('batchSizeType', 1)), 1)
        batch_size = opt_params.get('batch_size', opt_params.get('batchSize')) or []
        max_iter = self._to_int(opt_params.get('max_iter', opt_params.get('maxIter', len(batch_size) or 1)), 1)
        max_iter = max(max_iter, 0)

        if batch_size_type == 2:
            custom = opt_params.get('custom_batch_size', opt_params.get('customBatchSize')) or []
            total = 0
            for idx in range(1, max_iter + 1):
                value = 0
                for item in custom:
                    if not isinstance(item, dict):
                        continue
                    start = self._to_int(item.get('start_index', item.get('startIndex')), 0)
                    end = self._to_int(item.get('end_index', item.get('endIndex')), 0)
                    if start <= idx <= end:
                        value = self._to_int(item.get('value'), 0)
                        break
                total += max(value, 0)
            return total

        values = []
        for item in batch_size:
            if isinstance(item, dict):
                values.append(max(self._to_int(item.get('value'), 0), 0))
            else:
                values.append(max(self._to_int(item, 0), 0))

        if max_iter <= 0:
            return 0
        if not values:
            return 0
        if len(values) >= max_iter:
            return sum(values[:max_iter])
        if len(values) == 1:
            return values[0] * max_iter
        return sum(values) + values[-1] * (max_iter - len(values))

    def _estimate_order_rounds(self, input_json: Optional[dict], opt_param: Optional[dict]) -> int:
        total = 0
        if isinstance(input_json, dict):
            conditions = input_json.get('conditions')
            if isinstance(conditions, list):
                for cond in conditions:
                    if not isinstance(cond, dict):
                        continue
                    params = cond.get('params')
                    if not isinstance(params, dict):
                        continue
                    total += self._estimate_rounds_from_opt_params(
                        params.get('opt_params', params.get('optParams'))
                    )
                return total

        if isinstance(opt_param, dict):
            for cfg in opt_param.values():
                if not isinstance(cfg, dict):
                    continue
                params = cfg.get('params')
                if not isinstance(params, dict):
                    continue
                total += self._estimate_rounds_from_opt_params(
                    params.get('opt_params', params.get('optParams'))
                )
        return total

    @staticmethod
    def _normalize_json_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_json_list(value: Any) -> List[Dict[str, Any]]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _extract_algorithm_type(condition: Dict[str, Any]) -> Optional[str]:
        params = condition.get('params')
        if not isinstance(params, dict):
            return None
        opt_params = params.get('optParams', params.get('opt_params'))
        if not isinstance(opt_params, dict):
            return None
        raw_alg = opt_params.get('algType', opt_params.get('alg_type'))
        if raw_alg in (1, '1', 'bayesian', 'BAYESIAN'):
            return 'BAYESIAN'
        if raw_alg in (5, '5'):
            return 'DOE_FILE'
        if raw_alg in (2, '2', 'doe', 'DOE'):
            return 'DOE'
        return str(raw_alg) if raw_alg is not None else None

    @staticmethod
    def _extract_solver_id(condition: Dict[str, Any]) -> Optional[str]:
        solver = condition.get('solver')
        if not isinstance(solver, dict):
            return None
        solver_id = solver.get('solverId', solver.get('solver_id'))
        if solver_id is None:
            return None
        version = solver.get('solverVersion', solver.get('solver_version'))
        return f"{solver_id}_{version}" if version else str(solver_id)

    @staticmethod
    def _extract_output_count(condition: Dict[str, Any]) -> int:
        output = condition.get('output')
        if not isinstance(output, dict):
            return 0
        resp_details = output.get('respDetails', output.get('resp_details'))
        if isinstance(resp_details, list):
            return len(resp_details)
        selected_output_ids = output.get('selectedOutputIds', output.get('selected_output_ids'))
        if isinstance(selected_output_ids, list):
            return len(selected_output_ids)
        return 0

    def _build_order_condition_rows(self, order_dict: dict, order_id: int, order_no: str) -> List[dict]:
        input_json = self._normalize_json_dict(order_dict.get('input_json'))
        conditions = self._normalize_json_list(input_json.get('conditions'))
        if not conditions:
            return []

        opt_issue_id = self._to_int(order_dict.get('opt_issue_id'), 0)
        now_ts = int(datetime.datetime.utcnow().timestamp())
        rows: List[dict] = []
        for condition in conditions:
            output = self._normalize_json_dict(condition.get('output'))
            params = self._normalize_json_dict(condition.get('params'))
            solver = self._normalize_json_dict(condition.get('solver'))
            care_device_ids = condition.get('careDeviceIds', condition.get('care_device_ids'))
            round_total = self._estimate_rounds_from_opt_params(
                params.get('optParams', params.get('opt_params'))
            )
            condition_remark = condition.get('remark', condition.get('conditionRemark', condition.get('condition_remark')))
            rows.append(
                {
                    'order_id': order_id,
                    'order_no': order_no,
                    'opt_issue_id': opt_issue_id,
                    'opt_job_id': None,
                    'condition_id': self._to_int(
                        condition.get('conditionId', condition.get('condition_id'))
                    ),
                    'fold_type_id': self._to_int(
                        condition.get('foldTypeId', condition.get('fold_type_id'))
                    ),
                    'fold_type_name': condition.get('foldTypeName', condition.get('fold_type_name')),
                    'sim_type_id': self._to_int(
                        condition.get('simTypeId', condition.get('sim_type_id'))
                    ),
                    'sim_type_name': condition.get('simTypeName', condition.get('sim_type_name')),
                    'algorithm_type': self._extract_algorithm_type(condition),
                    'round_total': round_total,
                    'output_count': self._extract_output_count(condition),
                    'solver_id': self._extract_solver_id(condition),
                    'care_device_ids': care_device_ids if isinstance(care_device_ids, list) else [],
                    'remark': condition_remark if isinstance(condition_remark, str) else order_dict.get('remark'),
                    'running_module': None,
                    'process': 0,
                    'status': 0,
                    'statistics_json': None,
                    'result_summary_json': None,
                    'condition_snapshot': {
                        'conditionId': condition.get('conditionId', condition.get('condition_id')),
                        'foldTypeId': condition.get('foldTypeId', condition.get('fold_type_id')),
                        'foldTypeName': condition.get('foldTypeName', condition.get('fold_type_name')),
                        'simTypeId': condition.get('simTypeId', condition.get('sim_type_id')),
                        'simTypeName': condition.get('simTypeName', condition.get('sim_type_name')),
                        'remark': condition_remark if isinstance(condition_remark, str) else None,
                        'params': params,
                        'output': output,
                        'solver': solver,
                        'careDeviceIds': care_device_ids if isinstance(care_device_ids, list) else [],
                    },
                    'external_meta': None,
                    'created_at': now_ts,
                    'updated_at': now_ts,
                }
            )
        return rows

    @staticmethod
    def _merge_role_limits(roles: List[Role]) -> Dict[str, int]:
        max_batch_size: Optional[int] = None
        max_cpu_cores: Optional[int] = None
        daily_round_limit_default: Optional[int] = None
        for role in roles:
            if isinstance(role.max_batch_size, int) and role.max_batch_size > 0:
                max_batch_size = max(max_batch_size or 0, role.max_batch_size)
            if isinstance(role.max_cpu_cores, int) and role.max_cpu_cores > 0:
                max_cpu_cores = max(max_cpu_cores or 0, role.max_cpu_cores)
            if isinstance(role.daily_round_limit_default, int) and role.daily_round_limit_default > 0:
                daily_round_limit_default = max(
                    daily_round_limit_default or 0, role.daily_round_limit_default
                )
        return {
            'max_batch_size': max_batch_size or 200,
            'max_cpu_cores': max_cpu_cores or 192,
            'daily_round_limit_default': daily_round_limit_default or 500,
        }

    def _get_user_submit_limits(self, user_identity: str) -> Dict[str, int]:
        user = User.query.filter(User.domain_account == str(user_identity), User.valid == 1).first()
        if not user:
            return {
                'max_batch_size': 200,
                'max_cpu_cores': 192,
                'daily_round_limit_default': 500,
                'daily_round_limit': 500,
            }
        role_ids = list(user.role_ids or [])
        roles = Role.query.filter(Role.id.in_(role_ids), Role.valid == 1).all() if role_ids else []
        merged = self._merge_role_limits(roles)
        user_daily_limit = user.daily_round_limit
        merged['daily_round_limit'] = int(user_daily_limit) if isinstance(user_daily_limit, int) and user_daily_limit > 0 else int(merged['daily_round_limit_default'])
        return merged

    def _sum_today_rounds(self, user_identity: str) -> int:
        now = datetime.datetime.now()
        start_ts = int(datetime.datetime(now.year, now.month, now.day, 0, 0, 0).timestamp())
        end_ts = int(datetime.datetime(now.year, now.month, now.day, 23, 59, 59).timestamp())
        orders = self.repository.get_orders_by_creator_between(str(user_identity), start_ts, end_ts)
        return sum(
            self._estimate_order_rounds(getattr(order, 'input_json', None), getattr(order, 'opt_param', None))
            for order in orders
        )

    def get_submit_limits(self, user_identity: str) -> Dict[str, int]:
        limits = self._get_user_submit_limits(user_identity)
        today_used_rounds = self._sum_today_rounds(user_identity)
        return {
            'max_batch_size': limits['max_batch_size'],
            'max_cpu_cores': limits['max_cpu_cores'],
            'daily_round_limit_default': limits['daily_round_limit_default'],
            'daily_round_limit': limits['daily_round_limit'],
            'today_used_rounds': today_used_rounds,
            'today_remaining_rounds': max(limits['daily_round_limit'] - today_used_rounds, 0),
        }
    
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
        
        payload = order.to_dict()
        payload['conditions'] = [
            item.to_list_dict() for item in self.repository.get_order_condition_optis(order_id)
        ]
        return payload
    
    def create_order(self, order_data: dict, user_identity: str) -> Dict:
        """
        创建订单
        Args:
            order_data: 订单数据
            user_identity: 创建用户域账号
        Returns:
            创建的订单信息
        """
        order_rounds = self._estimate_order_rounds(
            order_data.get('input_json'),
            order_data.get('opt_param'),
        )
        limits = self._get_user_submit_limits(str(user_identity))
        if order_rounds > int(limits['max_batch_size']):
            raise BusinessError(
                ErrorCode.VALIDATION_ERROR,
                f'本次提单轮次 {order_rounds} 超过上限 {limits["max_batch_size"]}，请减少轮次后再提交'
            )

        today_used_rounds = self._sum_today_rounds(str(user_identity))
        daily_round_limit = int(limits['daily_round_limit'])
        if today_used_rounds + order_rounds > daily_round_limit:
            raise BusinessError(
                ErrorCode.VALIDATION_ERROR,
                f'今日累计轮次上限为 {daily_round_limit}，当前已使用 {today_used_rounds}，本次需 {order_rounds}'
            )

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
            'opt_issue_id': order_data.get('opt_issue_id'),
            'condition_summary': order_data.get('condition_summary'),
            'workflow_id': order_data.get('workflow_id'),
            'submit_check': order_data.get('submit_check'),
            'client_meta': order_data.get('client_meta'),
            'created_by': str(user_identity),
            'status': 0,  # 未开始/排队
            'progress': 0
        }
        
        try:
            order = self.repository.create_order(order_dict)
            condition_rows = self._build_order_condition_rows(order_dict, order.id, order.order_no)
            self.repository.replace_order_condition_optis(order.id, condition_rows)
            self.repository.commit()
            payload = order.to_dict()
            payload['conditions'] = [row.to_list_dict() for row in self.repository.get_order_condition_optis(order.id)]
            return payload
        except Exception:
            self.repository.rollback()
            raise
    
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
            'workflow_id', 'submit_check', 'client_meta', 'opt_issue_id',
        ]
        filtered_data = {
            k: v for k, v in update_data.items()
            if k in allowed_fields and v is not None
        }
        if 'participant_ids' in update_data and update_data['participant_ids'] is not None:
            filtered_data['participant_uids'] = update_data['participant_ids']

        try:
            order = self.repository.update_order(order, filtered_data)
            rebuilt_source = {
                'input_json': filtered_data.get('input_json', order.input_json),
                'opt_issue_id': filtered_data.get('opt_issue_id', order.opt_issue_id),
                'remark': filtered_data.get('remark', order.remark),
            }
            condition_rows = self._build_order_condition_rows(rebuilt_source, order.id, order.order_no)
            self.repository.replace_order_condition_optis(order.id, condition_rows)
            self.repository.commit()
            payload = order.to_dict()
            payload['conditions'] = [
                item.to_list_dict() for item in self.repository.get_order_condition_optis(order.id)
            ]
            return payload
        except Exception:
            self.repository.rollback()
            raise

    def get_order_conditions(self, order_id: int) -> List[Dict]:
        order = self.repository.get_order_by_id(order_id)
        if not order:
            raise NotFoundError("订单不存在")
        return [item.to_list_dict() for item in self.repository.get_order_condition_optis(order_id)]
    
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
        
        # 只有未开始/排队状态可以删除
        if order.status != 0:
            raise BusinessError(
                ErrorCode.VALIDATION_ERROR,
                "只有未开始（排队中）状态的订单可以删除"
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
