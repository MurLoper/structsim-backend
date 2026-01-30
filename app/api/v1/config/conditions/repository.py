"""
工况配置管理 - Repository层
职责：数据访问
"""
from typing import List, Optional
from app import db
from app.models.config import ConditionConfig


class ConditionConfigRepository:
    """工况配置数据访问"""

    def get_all(self, valid_only: bool = True) -> List[ConditionConfig]:
        """获取所有工况配置"""
        query = ConditionConfig.query
        if valid_only:
            query = query.filter(ConditionConfig.valid == 1)
        return query.order_by(ConditionConfig.sort).all()

    def get_by_id(self, condition_id: int) -> Optional[ConditionConfig]:
        """根据ID获取工况配置"""
        return ConditionConfig.query.get(condition_id)

    def get_by_fold_sim(self, fold_type_id: int, sim_type_id: int) -> Optional[ConditionConfig]:
        """根据姿态+仿真类型获取工况配置"""
        return ConditionConfig.query.filter(
            ConditionConfig.fold_type_id == fold_type_id,
            ConditionConfig.sim_type_id == sim_type_id,
            ConditionConfig.valid == 1
        ).first()

    def get_by_fold_type(self, fold_type_id: int) -> List[ConditionConfig]:
        """根据姿态ID获取工况配置列表"""
        return ConditionConfig.query.filter(
            ConditionConfig.fold_type_id == fold_type_id,
            ConditionConfig.valid == 1
        ).order_by(ConditionConfig.sort).all()

    def get_by_sim_type(self, sim_type_id: int) -> List[ConditionConfig]:
        """根据仿真类型ID获取工况配置列表"""
        return ConditionConfig.query.filter(
            ConditionConfig.sim_type_id == sim_type_id,
            ConditionConfig.valid == 1
        ).order_by(ConditionConfig.sort).all()

    def create(self, data: dict) -> ConditionConfig:
        """创建工况配置"""
        condition = ConditionConfig(**data)
        db.session.add(condition)
        db.session.commit()
        return condition

    def update(self, condition_id: int, data: dict) -> Optional[ConditionConfig]:
        """更新工况配置"""
        condition = self.get_by_id(condition_id)
        if not condition:
            return None
        for key, value in data.items():
            if value is not None and hasattr(condition, key):
                setattr(condition, key, value)
        db.session.commit()
        return condition

    def delete(self, condition_id: int) -> bool:
        """删除工况配置（软删除）"""
        condition = self.get_by_id(condition_id)
        if not condition:
            return False
        condition.valid = 0
        db.session.commit()
        return True
