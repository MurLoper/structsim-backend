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
    Workflow, StatusDef, AutomationModule, FoldType,
    ModelLevel, CareDevice, SolverResource, Department
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
        print(f"🟢 [BaseRepository.update] ID: {id}")
        print(f"🟢 [BaseRepository.update] 更新数据: {data}")

        instance = self.find_by_id(id)
        if not instance:
            print(f"🔴 [BaseRepository.update] 未找到记录 ID: {id}")
            return None

        print(f"🟢 [BaseRepository.update] 更新前的实例: {instance.to_dict() if hasattr(instance, 'to_dict') else instance}")

        data['updated_at'] = int(time.time())
        for key, value in data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key)
                setattr(instance, key, value)
                print(f"🟡 [BaseRepository.update] 字段 {key}: {old_value} -> {value}")
            else:
                print(f"🔴 [BaseRepository.update] 实例没有字段: {key}")

        self.session.commit()

        print(f"🟢 [BaseRepository.update] 更新后的实例: {instance.to_dict() if hasattr(instance, 'to_dict') else instance}")
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
        # 注意：后续需要关联 user_project_permissions 表实现项目级权限过滤
        # 暂时返回所有有效项目
        return self.find_all_valid()


class SimTypeRepository(BaseRepository[SimType]):
    model_class = SimType


class ParamDefRepository(BaseRepository[ParamDef]):
    model_class = ParamDef

    def find_paginated(self, page: int = 1, page_size: int = 20, keyword: str = None):
        """分页查询参数定义"""
        query = self.session.query(self.model_class).filter_by(valid=1)

        if keyword:
            keyword_filter = f'%{keyword}%'
            query = query.filter(
                (self.model_class.name.ilike(keyword_filter)) |
                (self.model_class.key.ilike(keyword_filter))
            )

        total = query.count()
        items = query.order_by(self.model_class.sort.asc(), self.model_class.id.asc()) \
            .offset((page - 1) * page_size).limit(page_size).all()

        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

    def find_by_key(self, key: str) -> Optional[ParamDef]:
        """根据key查找参数定义"""
        return self.session.query(self.model_class).filter_by(key=key, valid=1).first()

    def batch_create(self, data_list: List[dict]) -> List[ParamDef]:
        """批量创建参数定义"""
        now = int(time.time())
        instances = []
        for data in data_list:
            data.setdefault('valid', 1)
            data.setdefault('created_at', now)
            data.setdefault('updated_at', now)
            instance = self.model_class(**data)
            self.session.add(instance)
            instances.append(instance)
        self.session.commit()
        return instances


class SolverRepository(BaseRepository[Solver]):
    model_class = Solver


class ConditionDefRepository(BaseRepository[ConditionDef]):
    model_class = ConditionDef


class OutputDefRepository(BaseRepository[OutputDef]):
    model_class = OutputDef

    def find_paginated(self, page: int = 1, page_size: int = 20, keyword: str = None):
        """分页查询输出定义"""
        query = self.session.query(self.model_class).filter_by(valid=1)

        if keyword:
            keyword_filter = f'%{keyword}%'
            query = query.filter(
                (self.model_class.name.ilike(keyword_filter)) |
                (self.model_class.code.ilike(keyword_filter))
            )

        total = query.count()
        items = query.order_by(self.model_class.sort.asc(), self.model_class.id.asc()) \
            .offset((page - 1) * page_size).limit(page_size).all()

        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

    def find_by_code(self, code: str) -> Optional[OutputDef]:
        """根据code查找输出定义"""
        return self.session.query(self.model_class).filter_by(code=code, valid=1).first()

    def batch_create(self, data_list: List[dict]) -> List[OutputDef]:
        """批量创建输出定义"""
        now = int(time.time())
        instances = []
        for data in data_list:
            data.setdefault('valid', 1)
            data.setdefault('created_at', now)
            data.setdefault('updated_at', now)
            instance = self.model_class(**data)
            self.session.add(instance)
            instances.append(instance)
        self.session.commit()
        return instances


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


class ModelLevelRepository(BaseRepository[ModelLevel]):
    """模型层级仓储"""
    model_class = ModelLevel


class CareDeviceRepository(BaseRepository[CareDevice]):
    """关注器件仓储"""
    model_class = CareDevice

    def find_by_category(self, category: str) -> List[CareDevice]:
        return self.session.query(self.model_class).filter_by(
            category=category, valid=1
        ).order_by(self.model_class.sort.asc()).all()


class SolverResourceRepository(BaseRepository[SolverResource]):
    """求解器资源池仓储"""
    model_class = SolverResource


class DepartmentRepository(BaseRepository[Department]):
    """部门仓储"""
    model_class = Department

    def find_by_parent_id(self, parent_id: int) -> List[Department]:
        """根据父部门ID查找子部门"""
        return self.session.query(self.model_class).filter_by(
            parent_id=parent_id, valid=1
        ).order_by(self.model_class.sort.asc()).all()

