"""
参数组合管理 - Repository层
职责：纯数据访问、CRUD操作封装
禁止：业务逻辑、HTTP相关逻辑
"""
from typing import Optional, List
from sqlalchemy import select, and_
from app.extensions import db
from app.models import ParamGroup, ParamGroupParamRel, ParamDef


class ParamGroupRepository:
    """参数组合仓储"""
    
    @staticmethod
    def find_all(valid: Optional[int] = None) -> List[ParamGroup]:
        """查询所有参数组合"""
        query = select(ParamGroup)
        if valid is not None:
            query = query.where(ParamGroup.valid == valid)
        query = query.order_by(ParamGroup.sort.asc(), ParamGroup.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_id(group_id: int) -> Optional[ParamGroup]:
        """根据ID查询参数组合"""
        return db.session.get(ParamGroup, group_id)
    
    @staticmethod
    def create(data: dict) -> ParamGroup:
        """创建参数组合"""
        group = ParamGroup(**data)
        db.session.add(group)
        db.session.flush()
        return group
    
    @staticmethod
    def update(group: ParamGroup, data: dict) -> ParamGroup:
        """更新参数组合"""
        for key, value in data.items():
            if hasattr(group, key) and value is not None:
                setattr(group, key, value)
        db.session.flush()
        return group
    
    @staticmethod
    def delete(group: ParamGroup) -> None:
        """删除参数组合"""
        db.session.delete(group)
        db.session.flush()


class ParamGroupParamRelRepository:
    """参数组合-参数关联仓储"""
    
    @staticmethod
    def find_by_group_id(group_id: int) -> List[ParamGroupParamRel]:
        """查询组合包含的所有参数"""
        query = select(ParamGroupParamRel).where(
            ParamGroupParamRel.param_group_id == group_id
        ).order_by(ParamGroupParamRel.sort.asc(), ParamGroupParamRel.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_group_and_param(group_id: int, param_def_id: int) -> Optional[ParamGroupParamRel]:
        """查询特定的参数关联"""
        query = select(ParamGroupParamRel).where(
            and_(
                ParamGroupParamRel.param_group_id == group_id,
                ParamGroupParamRel.param_def_id == param_def_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def create(data: dict) -> ParamGroupParamRel:
        """创建参数关联"""
        rel = ParamGroupParamRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel
    
    @staticmethod
    def delete(rel: ParamGroupParamRel) -> None:
        """删除参数关联"""
        db.session.delete(rel)
        db.session.flush()
    
    @staticmethod
    def find_param_def_by_id(param_def_id: int) -> Optional[ParamDef]:
        """查询参数定义"""
        return db.session.get(ParamDef, param_def_id)

