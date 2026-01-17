"""
工况输出组合管理 - Repository层
职责：纯数据访问、CRUD操作封装
禁止：业务逻辑、HTTP相关逻辑
"""
from typing import Optional, List
from sqlalchemy import select, and_
from app.extensions import db
from app.models import (
    ConditionOutputGroup,
    CondOutGroupConditionRel,
    CondOutGroupOutputRel,
    ConditionDef,
    OutputDef
)


class CondOutGroupRepository:
    """工况输出组合仓储"""
    
    @staticmethod
    def find_all(valid: Optional[int] = None) -> List[ConditionOutputGroup]:
        """查询所有工况输出组合"""
        query = select(ConditionOutputGroup)
        if valid is not None:
            query = query.where(ConditionOutputGroup.valid == valid)
        query = query.order_by(ConditionOutputGroup.sort.asc(), ConditionOutputGroup.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_id(group_id: int) -> Optional[ConditionOutputGroup]:
        """根据ID查询工况输出组合"""
        return db.session.get(ConditionOutputGroup, group_id)
    
    @staticmethod
    def create(data: dict) -> ConditionOutputGroup:
        """创建工况输出组合"""
        group = ConditionOutputGroup(**data)
        db.session.add(group)
        db.session.flush()
        return group
    
    @staticmethod
    def update(group: ConditionOutputGroup, data: dict) -> ConditionOutputGroup:
        """更新工况输出组合"""
        for key, value in data.items():
            if hasattr(group, key) and value is not None:
                setattr(group, key, value)
        db.session.flush()
        return group
    
    @staticmethod
    def delete(group: ConditionOutputGroup) -> None:
        """删除工况输出组合"""
        db.session.delete(group)
        db.session.flush()


class CondOutGroupConditionRelRepository:
    """工况输出组合-工况关联仓储"""
    
    @staticmethod
    def find_by_group_id(group_id: int) -> List[CondOutGroupConditionRel]:
        """查询组合包含的所有工况"""
        query = select(CondOutGroupConditionRel).where(
            CondOutGroupConditionRel.cond_out_group_id == group_id
        ).order_by(CondOutGroupConditionRel.sort.asc(), CondOutGroupConditionRel.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_group_and_condition(group_id: int, condition_def_id: int) -> Optional[CondOutGroupConditionRel]:
        """查询特定的工况关联"""
        query = select(CondOutGroupConditionRel).where(
            and_(
                CondOutGroupConditionRel.cond_out_group_id == group_id,
                CondOutGroupConditionRel.condition_def_id == condition_def_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def create(data: dict) -> CondOutGroupConditionRel:
        """创建工况关联"""
        rel = CondOutGroupConditionRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel
    
    @staticmethod
    def delete(rel: CondOutGroupConditionRel) -> None:
        """删除工况关联"""
        db.session.delete(rel)
        db.session.flush()
    
    @staticmethod
    def find_condition_def_by_id(condition_def_id: int) -> Optional[ConditionDef]:
        """查询工况定义"""
        return db.session.get(ConditionDef, condition_def_id)


class CondOutGroupOutputRelRepository:
    """工况输出组合-输出关联仓储"""
    
    @staticmethod
    def find_by_group_id(group_id: int) -> List[CondOutGroupOutputRel]:
        """查询组合包含的所有输出"""
        query = select(CondOutGroupOutputRel).where(
            CondOutGroupOutputRel.cond_out_group_id == group_id
        ).order_by(CondOutGroupOutputRel.sort.asc(), CondOutGroupOutputRel.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_group_and_output(group_id: int, output_def_id: int) -> Optional[CondOutGroupOutputRel]:
        """查询特定的输出关联"""
        query = select(CondOutGroupOutputRel).where(
            and_(
                CondOutGroupOutputRel.cond_out_group_id == group_id,
                CondOutGroupOutputRel.output_def_id == output_def_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def create(data: dict) -> CondOutGroupOutputRel:
        """创建输出关联"""
        rel = CondOutGroupOutputRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel
    
    @staticmethod
    def delete(rel: CondOutGroupOutputRel) -> None:
        """删除输出关联"""
        db.session.delete(rel)
        db.session.flush()
    
    @staticmethod
    def find_output_def_by_id(output_def_id: int) -> Optional[OutputDef]:
        """查询输出定义"""
        return db.session.get(OutputDef, output_def_id)

