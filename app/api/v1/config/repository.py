"""
配置中心 - 仓储层
职责：纯数据访问、CRUD操作封装、查询组合
禁止：业务逻辑、HTTP相关逻辑
"""
import time
from typing import Optional, List, TypeVar, Generic, Type
from app.extensions import db
from app.models import (
    Project, SimType, ParamDef, ParamTplSet, ParamTplItem,
    ConditionDef, OutputDef, CondOutSet, Solver,
    Workflow, StatusDef, AutomationModule, FoldType
)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """基础仓储类 - 封装通用CRUD操作"""
    
    model_class: Type[T] = None
    
    def __init__(self):
        self.session = db.session
    
    def find_by_id(self, id: int) -> Optional[T]:
        """根据ID查找"""
        return self.session.get(self.model_class, id)
    
    def find_by_id_valid(self, id: int) -> Optional[T]:
        """根据ID查找有效记录"""
        return self.session.query(self.model_class).filter_by(id=id, valid=1).first()
    
    def find_all_valid(self, order_by: str = 'sort') -> List[T]:
        """查找所有有效记录"""
        query = self.session.query(self.model_class).filter_by(valid=1)
        if hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).asc())
        return query.all()
    
    def create(self, data: dict) -> T:
        """创建记录"""
        now = int(time.time())
        data.setdefault('valid', 1)
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.commit()
        return instance
    
    def update(self, id: int, data: dict) -> Optional[T]:
        """更新记录"""
        instance = self.find_by_id(id)
        if not instance:
            return None
        
        data['updated_at'] = int(time.time())
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        self.session.commit()
        return instance
    
    def soft_delete(self, id: int) -> bool:
        """软删除"""
        instance = self.find_by_id(id)
        if not instance:
            return False
        
        instance.valid = 0
        instance.updated_at = int(time.time())
        self.session.commit()
        return True
    
    def exists(self, id: int) -> bool:
        """检查是否存在"""
        return self.session.query(
            self.session.query(self.model_class).filter_by(id=id, valid=1).exists()
        ).scalar()


# ============ 具体仓储类 ============
class ProjectRepository(BaseRepository[Project]):
    model_class = Project

    def find_by_user(self, user_id: int) -> List[Project]:
        """查找用户有权限的项目"""
        # TODO: 关联 user_project_permissions 表查询
        # 暂时返回所有有效项目
        return self.find_all_valid()


class SimTypeRepository(BaseRepository[SimType]):
    model_class = SimType


class ParamDefRepository(BaseRepository[ParamDef]):
    model_class = ParamDef


class SolverRepository(BaseRepository[Solver]):
    model_class = Solver


class ConditionDefRepository(BaseRepository[ConditionDef]):
    model_class = ConditionDef


class OutputDefRepository(BaseRepository[OutputDef]):
    model_class = OutputDef


class FoldTypeRepository(BaseRepository[FoldType]):
    model_class = FoldType


class ParamTplSetRepository(BaseRepository[ParamTplSet]):
    model_class = ParamTplSet
    
    def find_by_sim_type(self, sim_type_id: int) -> List[ParamTplSet]:
        return self.session.query(self.model_class).filter_by(
            sim_type_id=sim_type_id, valid=1
        ).order_by(self.model_class.sort.asc()).all()


class ParamTplItemRepository(BaseRepository[ParamTplItem]):
    model_class = ParamTplItem
    
    def find_by_tpl_set(self, tpl_set_id: int) -> List[ParamTplItem]:
        return self.session.query(self.model_class).filter_by(
            tpl_set_id=tpl_set_id, valid=1
        ).order_by(self.model_class.sort.asc()).all()


class CondOutSetRepository(BaseRepository[CondOutSet]):
    model_class = CondOutSet
    
    def find_by_sim_type(self, sim_type_id: int) -> List[CondOutSet]:
        return self.session.query(self.model_class).filter_by(
            sim_type_id=sim_type_id, valid=1
        ).order_by(self.model_class.sort.asc()).all()


class WorkflowRepository(BaseRepository[Workflow]):
    model_class = Workflow
    
    def find_by_type(self, workflow_type: str) -> List[Workflow]:
        return self.session.query(self.model_class).filter_by(
            type=workflow_type, valid=1
        ).order_by(self.model_class.sort.asc()).all()


class StatusDefRepository(BaseRepository[StatusDef]):
    model_class = StatusDef


class AutomationModuleRepository(BaseRepository[AutomationModule]):
    model_class = AutomationModule
    
    def find_by_category(self, category: str) -> List[AutomationModule]:
        return self.session.query(self.model_class).filter_by(
            category=category, valid=1
        ).order_by(self.model_class.sort.asc()).all()

