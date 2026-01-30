"""
工况配置管理 - Service层
职责：业务逻辑 + Redis缓存
"""
from typing import List, Optional
from flask import current_app
from app.common.errors import NotFoundError, BusinessError
from app.common.cache_service import CacheKeys, ConfigCache
from .repository import ConditionConfigRepository


class ConditionConfigService:
    """工况配置业务服务（带缓存）"""

    def __init__(self):
        self.repo = ConditionConfigRepository()

    def get_all(self) -> List[dict]:
        """获取所有工况配置（优先从缓存读取）"""
        def fetch_from_db():
            conditions = self.repo.get_all()
            return [c.to_dict() for c in conditions]

        return ConfigCache.get_or_set(
            CacheKeys.CONDITIONS_ALL,
            fetch_from_db,
            ConfigCache.TTL_CONDITIONS
        )

    def get_by_id(self, condition_id: int) -> dict:
        """根据ID获取工况配置（优先从缓存读取）"""
        def fetch_from_db():
            condition = self.repo.get_by_id(condition_id)
            if not condition:
                return None
            return condition.to_dict()

        result = ConfigCache.get_or_set(
            CacheKeys.condition(condition_id),
            fetch_from_db,
            ConfigCache.TTL_CONDITIONS
        )
        if not result:
            raise NotFoundError(f"工况配置不存在: {condition_id}")
        return result

    def get_by_fold_sim(self, fold_type_id: int, sim_type_id: int) -> Optional[dict]:
        """根据姿态+仿真类型获取工况配置（优先从缓存读取）"""
        def fetch_from_db():
            condition = self.repo.get_by_fold_sim(fold_type_id, sim_type_id)
            return condition.to_dict() if condition else None

        return ConfigCache.get_or_set(
            CacheKeys.condition_by_fold_sim(fold_type_id, sim_type_id),
            fetch_from_db,
            ConfigCache.TTL_CONDITIONS
        )

    def get_by_fold_type(self, fold_type_id: int) -> List[dict]:
        """根据姿态ID获取工况配置列表"""
        conditions = self.repo.get_by_fold_type(fold_type_id)
        return [c.to_dict() for c in conditions]

    def create(self, data: dict) -> dict:
        """创建工况配置"""
        # 检查是否已存在
        existing = self.repo.get_by_fold_sim(
            data['fold_type_id'],
            data['sim_type_id']
        )
        if existing:
            raise BusinessError("该姿态+仿真类型组合已存在工况配置")

        condition = self.repo.create(data)
        result = condition.to_dict()

        # 失效相关缓存
        ConfigCache.invalidate_condition(
            fold_type_id=data['fold_type_id'],
            sim_type_id=data['sim_type_id']
        )
        return result

    def update(self, condition_id: int, data: dict) -> dict:
        """更新工况配置"""
        # 先获取原数据用于失效缓存
        old_condition = self.repo.get_by_id(condition_id)
        if not old_condition:
            raise NotFoundError(f"工况配置不存在: {condition_id}")

        condition = self.repo.update(condition_id, data)
        result = condition.to_dict()

        # 失效相关缓存
        ConfigCache.invalidate_condition(
            condition_id=condition_id,
            fold_type_id=old_condition.fold_type_id,
            sim_type_id=old_condition.sim_type_id
        )
        return result

    def delete(self, condition_id: int) -> bool:
        """删除工况配置"""
        # 先获取原数据用于失效缓存
        old_condition = self.repo.get_by_id(condition_id)
        if not old_condition:
            raise NotFoundError(f"工况配置不存在: {condition_id}")

        fold_type_id = old_condition.fold_type_id
        sim_type_id = old_condition.sim_type_id

        if not self.repo.delete(condition_id):
            raise NotFoundError(f"工况配置不存在: {condition_id}")

        # 失效相关缓存
        ConfigCache.invalidate_condition(
            condition_id=condition_id,
            fold_type_id=fold_type_id,
            sim_type_id=sim_type_id
        )
        return True
