"""
配置关联关系管理 - Repository层
职责：纯数据访问、CRUD操作封装
禁止：业务逻辑、HTTP相关逻辑
"""
from typing import Optional, List
from sqlalchemy import select, and_
from app.extensions import db
from app.models import (
    Project,
    SimType,
    ParamGroup,
    ConditionOutputGroup,
    Solver,
    ProjectSimTypeRel,
    SimTypeParamGroupRel,
    SimTypeCondOutGroupRel,
    SimTypeSolverRel
)


class ProjectSimTypeRelRepository:
    """项目-仿真类型关联仓储"""
    
    @staticmethod
    def find_by_project_id(project_id: int) -> List[ProjectSimTypeRel]:
        """查询项目关联的所有仿真类型"""
        query = select(ProjectSimTypeRel).where(
            ProjectSimTypeRel.project_id == project_id
        ).order_by(ProjectSimTypeRel.sort.asc(), ProjectSimTypeRel.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_project_and_sim_type(project_id: int, sim_type_id: int) -> Optional[ProjectSimTypeRel]:
        """查询特定的项目-仿真类型关联"""
        query = select(ProjectSimTypeRel).where(
            and_(
                ProjectSimTypeRel.project_id == project_id,
                ProjectSimTypeRel.sim_type_id == sim_type_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def find_default_by_project(project_id: int) -> Optional[ProjectSimTypeRel]:
        """查询项目的默认仿真类型"""
        query = select(ProjectSimTypeRel).where(
            and_(
                ProjectSimTypeRel.project_id == project_id,
                ProjectSimTypeRel.is_default == 1
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def create(data: dict) -> ProjectSimTypeRel:
        """创建关联"""
        rel = ProjectSimTypeRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel
    
    @staticmethod
    def update(rel: ProjectSimTypeRel, data: dict) -> ProjectSimTypeRel:
        """更新关联"""
        for key, value in data.items():
            if hasattr(rel, key):
                setattr(rel, key, value)
        db.session.flush()
        return rel
    
    @staticmethod
    def delete(rel: ProjectSimTypeRel) -> None:
        """删除关联"""
        db.session.delete(rel)
        db.session.flush()
    
    @staticmethod
    def find_project_by_id(project_id: int) -> Optional[Project]:
        """查询项目"""
        return db.session.get(Project, project_id)
    
    @staticmethod
    def find_sim_type_by_id(sim_type_id: int) -> Optional[SimType]:
        """查询仿真类型"""
        return db.session.get(SimType, sim_type_id)


class SimTypeParamGroupRelRepository:
    """仿真类型-参数组合关联仓储"""
    
    @staticmethod
    def find_by_sim_type_id(sim_type_id: int) -> List[SimTypeParamGroupRel]:
        """查询仿真类型关联的所有参数组合"""
        query = select(SimTypeParamGroupRel).where(
            SimTypeParamGroupRel.sim_type_id == sim_type_id
        ).order_by(SimTypeParamGroupRel.sort.asc(), SimTypeParamGroupRel.id.asc())
        return db.session.execute(query).scalars().all()
    
    @staticmethod
    def find_by_sim_type_and_param_group(sim_type_id: int, param_group_id: int) -> Optional[SimTypeParamGroupRel]:
        """查询特定的仿真类型-参数组合关联"""
        query = select(SimTypeParamGroupRel).where(
            and_(
                SimTypeParamGroupRel.sim_type_id == sim_type_id,
                SimTypeParamGroupRel.param_group_id == param_group_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def find_default_by_sim_type(sim_type_id: int) -> Optional[SimTypeParamGroupRel]:
        """查询仿真类型的默认参数组合"""
        query = select(SimTypeParamGroupRel).where(
            and_(
                SimTypeParamGroupRel.sim_type_id == sim_type_id,
                SimTypeParamGroupRel.is_default == 1
            )
        )
        return db.session.execute(query).scalar_one_or_none()
    
    @staticmethod
    def create(data: dict) -> SimTypeParamGroupRel:
        """创建关联"""
        rel = SimTypeParamGroupRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel
    
    @staticmethod
    def update(rel: SimTypeParamGroupRel, data: dict) -> SimTypeParamGroupRel:
        """更新关联"""
        for key, value in data.items():
            if hasattr(rel, key):
                setattr(rel, key, value)
        db.session.flush()
        return rel
    
    @staticmethod
    def delete(rel: SimTypeParamGroupRel) -> None:
        """删除关联"""
        db.session.delete(rel)
        db.session.flush()
    
    @staticmethod
    def find_sim_type_by_id(sim_type_id: int) -> Optional[SimType]:
        """查询仿真类型"""
        return db.session.get(SimType, sim_type_id)
    
    @staticmethod
    def find_param_group_by_id(param_group_id: int) -> Optional[ParamGroup]:
        """查询参数组合"""
        return db.session.get(ParamGroup, param_group_id)


class SimTypeCondOutGroupRelRepository:
    """仿真类型-工况输出组合关联仓储"""

    @staticmethod
    def find_by_sim_type_id(sim_type_id: int) -> List[SimTypeCondOutGroupRel]:
        """查询仿真类型关联的所有工况输出组合"""
        query = select(SimTypeCondOutGroupRel).where(
            SimTypeCondOutGroupRel.sim_type_id == sim_type_id
        ).order_by(SimTypeCondOutGroupRel.sort.asc(), SimTypeCondOutGroupRel.id.asc())
        return db.session.execute(query).scalars().all()

    @staticmethod
    def find_by_sim_type_and_cond_out_group(sim_type_id: int, cond_out_group_id: int) -> Optional[SimTypeCondOutGroupRel]:
        """查询特定的仿真类型-工况输出组合关联"""
        query = select(SimTypeCondOutGroupRel).where(
            and_(
                SimTypeCondOutGroupRel.sim_type_id == sim_type_id,
                SimTypeCondOutGroupRel.cond_out_group_id == cond_out_group_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()

    @staticmethod
    def find_default_by_sim_type(sim_type_id: int) -> Optional[SimTypeCondOutGroupRel]:
        """查询仿真类型的默认工况输出组合"""
        query = select(SimTypeCondOutGroupRel).where(
            and_(
                SimTypeCondOutGroupRel.sim_type_id == sim_type_id,
                SimTypeCondOutGroupRel.is_default == 1
            )
        )
        return db.session.execute(query).scalar_one_or_none()

    @staticmethod
    def create(data: dict) -> SimTypeCondOutGroupRel:
        """创建关联"""
        rel = SimTypeCondOutGroupRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel

    @staticmethod
    def update(rel: SimTypeCondOutGroupRel, data: dict) -> SimTypeCondOutGroupRel:
        """更新关联"""
        for key, value in data.items():
            if hasattr(rel, key):
                setattr(rel, key, value)
        db.session.flush()
        return rel

    @staticmethod
    def delete(rel: SimTypeCondOutGroupRel) -> None:
        """删除关联"""
        db.session.delete(rel)
        db.session.flush()

    @staticmethod
    def find_sim_type_by_id(sim_type_id: int) -> Optional[SimType]:
        """查询仿真类型"""
        return db.session.get(SimType, sim_type_id)

    @staticmethod
    def find_cond_out_group_by_id(cond_out_group_id: int) -> Optional[ConditionOutputGroup]:
        """查询工况输出组合"""
        return db.session.get(ConditionOutputGroup, cond_out_group_id)


class SimTypeSolverRelRepository:
    """仿真类型-求解器关联仓储"""

    @staticmethod
    def find_by_sim_type_id(sim_type_id: int) -> List[SimTypeSolverRel]:
        """查询仿真类型关联的所有求解器"""
        query = select(SimTypeSolverRel).where(
            SimTypeSolverRel.sim_type_id == sim_type_id
        ).order_by(SimTypeSolverRel.sort.asc(), SimTypeSolverRel.id.asc())
        return db.session.execute(query).scalars().all()

    @staticmethod
    def find_by_sim_type_and_solver(sim_type_id: int, solver_id: int) -> Optional[SimTypeSolverRel]:
        """查询特定的仿真类型-求解器关联"""
        query = select(SimTypeSolverRel).where(
            and_(
                SimTypeSolverRel.sim_type_id == sim_type_id,
                SimTypeSolverRel.solver_id == solver_id
            )
        )
        return db.session.execute(query).scalar_one_or_none()

    @staticmethod
    def find_default_by_sim_type(sim_type_id: int) -> Optional[SimTypeSolverRel]:
        """查询仿真类型的默认求解器"""
        query = select(SimTypeSolverRel).where(
            and_(
                SimTypeSolverRel.sim_type_id == sim_type_id,
                SimTypeSolverRel.is_default == 1
            )
        )
        return db.session.execute(query).scalar_one_or_none()

    @staticmethod
    def create(data: dict) -> SimTypeSolverRel:
        """创建关联"""
        rel = SimTypeSolverRel(**data)
        db.session.add(rel)
        db.session.flush()
        return rel

    @staticmethod
    def update(rel: SimTypeSolverRel, data: dict) -> SimTypeSolverRel:
        """更新关联"""
        for key, value in data.items():
            if hasattr(rel, key):
                setattr(rel, key, value)
        db.session.flush()
        return rel

    @staticmethod
    def delete(rel: SimTypeSolverRel) -> None:
        """删除关联"""
        db.session.delete(rel)
        db.session.flush()

    @staticmethod
    def find_sim_type_by_id(sim_type_id: int) -> Optional[SimType]:
        """查询仿真类型"""
        return db.session.get(SimType, sim_type_id)

    @staticmethod
    def find_solver_by_id(solver_id: int) -> Optional[Solver]:
        """查询求解器"""
        return db.session.get(Solver, solver_id)

