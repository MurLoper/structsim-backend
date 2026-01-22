"""
配置关联关系管理 - Service层
职责：业务逻辑、事务管理
禁止：HTTP相关逻辑
"""
import time
from typing import List, Dict, Any
from app.extensions import db
from app.common.errors import NotFoundError, BusinessError
from .repository import (
    ProjectSimTypeRelRepository,
    SimTypeParamGroupRelRepository,
    SimTypeCondOutGroupRelRepository,
    SimTypeSolverRelRepository
)


class ConfigRelationsService:
    """配置关联关系服务"""
    
    def __init__(self):
        self.project_sim_type_repo = ProjectSimTypeRelRepository()
        self.sim_type_param_group_repo = SimTypeParamGroupRelRepository()
        self.sim_type_cond_out_group_repo = SimTypeCondOutGroupRelRepository()
        self.sim_type_solver_repo = SimTypeSolverRelRepository()
    
    # ============ 项目-仿真类型关联 ============
    
    def get_project_sim_types(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目关联的仿真类型"""
        project = self.project_sim_type_repo.find_project_by_id(project_id)
        if not project:
            raise NotFoundError(f"项目 {project_id} 不存在")
        
        rels = self.project_sim_type_repo.find_by_project_id(project_id)
        results = []
        for rel in rels:
            sim_type = self.project_sim_type_repo.find_sim_type_by_id(rel.sim_type_id)
            data = rel.to_dict()
            if sim_type:
                data['simTypeName'] = sim_type.name
                data['simTypeCode'] = sim_type.code
            results.append(data)
        return results
    
    def add_sim_type_to_project(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加仿真类型到项目"""
        project = self.project_sim_type_repo.find_project_by_id(project_id)
        if not project:
            raise NotFoundError(f"项目 {project_id} 不存在")
        
        sim_type_id = data['simTypeId']
        sim_type = self.project_sim_type_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")
        
        existing = self.project_sim_type_repo.find_by_project_and_sim_type(project_id, sim_type_id)
        if existing:
            raise BusinessError(f"仿真类型 {sim_type_id} 已关联到项目")
        
        # 如果设置为默认，先取消其他默认
        if data.get('isDefault', 0) == 1:
            default_rel = self.project_sim_type_repo.find_default_by_project(project_id)
            if default_rel:
                self.project_sim_type_repo.update(default_rel, {'is_default': 0})
        
        rel_data = {
            'project_id': project_id,
            'sim_type_id': sim_type_id,
            'is_default': data.get('isDefault', 0),
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }
        
        try:
            rel = self.project_sim_type_repo.create(rel_data)
            db.session.commit()
            result = rel.to_dict()
            result['simTypeName'] = sim_type.name
            result['simTypeCode'] = sim_type.code
            return result
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"添加仿真类型到项目失败: {str(e)}")
    
    def set_default_sim_type_for_project(self, project_id: int, sim_type_id: int) -> None:
        """设置项目的默认仿真类型"""
        rel = self.project_sim_type_repo.find_by_project_and_sim_type(project_id, sim_type_id)
        if not rel:
            raise NotFoundError(f"项目 {project_id} 未关联仿真类型 {sim_type_id}")
        
        try:
            # 先取消其他默认
            default_rel = self.project_sim_type_repo.find_default_by_project(project_id)
            if default_rel and default_rel.id != rel.id:
                self.project_sim_type_repo.update(default_rel, {'is_default': 0})
            
            # 设置当前为默认
            self.project_sim_type_repo.update(rel, {'is_default': 1})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"设置默认仿真类型失败: {str(e)}")
    
    def remove_sim_type_from_project(self, project_id: int, sim_type_id: int) -> None:
        """从项目移除仿真类型"""
        rel = self.project_sim_type_repo.find_by_project_and_sim_type(project_id, sim_type_id)
        if not rel:
            raise NotFoundError(f"项目 {project_id} 未关联仿真类型 {sim_type_id}")
        
        try:
            self.project_sim_type_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"移除仿真类型失败: {str(e)}")
    
    # ============ 仿真类型-参数组合关联 ============
    
    def get_sim_type_param_groups(self, sim_type_id: int) -> List[Dict[str, Any]]:
        """获取仿真类型关联的参数组合"""
        sim_type = self.sim_type_param_group_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")
        
        rels = self.sim_type_param_group_repo.find_by_sim_type_id(sim_type_id)
        results = []
        for rel in rels:
            param_group = self.sim_type_param_group_repo.find_param_group_by_id(rel.param_group_id)
            data = rel.to_dict()
            if param_group:
                data['paramGroupName'] = param_group.name
                data['paramGroupDescription'] = param_group.description
            results.append(data)
        return results
    
    def add_param_group_to_sim_type(self, sim_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加参数组合到仿真类型"""
        sim_type = self.sim_type_param_group_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")
        
        param_group_id = data['paramGroupId']
        param_group = self.sim_type_param_group_repo.find_param_group_by_id(param_group_id)
        if not param_group:
            raise NotFoundError(f"参数组合 {param_group_id} 不存在")
        
        existing = self.sim_type_param_group_repo.find_by_sim_type_and_param_group(sim_type_id, param_group_id)
        if existing:
            raise BusinessError(f"参数组合 {param_group_id} 已关联到仿真类型")

        # 如果设置为默认，先取消其他默认
        if data.get('isDefault', 0) == 1:
            default_rel = self.sim_type_param_group_repo.find_default_by_sim_type(sim_type_id)
            if default_rel:
                self.sim_type_param_group_repo.update(default_rel, {'is_default': 0})

        rel_data = {
            'sim_type_id': sim_type_id,
            'param_group_id': param_group_id,
            'is_default': data.get('isDefault', 0),
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }

        try:
            rel = self.sim_type_param_group_repo.create(rel_data)
            db.session.commit()
            result = rel.to_dict()
            result['paramGroupName'] = param_group.name
            result['paramGroupDescription'] = param_group.description
            return result
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"添加参数组合到仿真类型失败: {str(e)}")

    def set_default_param_group_for_sim_type(self, sim_type_id: int, param_group_id: int) -> None:
        """设置仿真类型的默认参数组合"""
        rel = self.sim_type_param_group_repo.find_by_sim_type_and_param_group(sim_type_id, param_group_id)
        if not rel:
            raise NotFoundError(f"仿真类型 {sim_type_id} 未关联参数组合 {param_group_id}")

        try:
            # 先取消其他默认
            default_rel = self.sim_type_param_group_repo.find_default_by_sim_type(sim_type_id)
            if default_rel and default_rel.id != rel.id:
                self.sim_type_param_group_repo.update(default_rel, {'is_default': 0})

            # 设置当前为默认
            self.sim_type_param_group_repo.update(rel, {'is_default': 1})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"设置默认参数组合失败: {str(e)}")

    def remove_param_group_from_sim_type(self, sim_type_id: int, param_group_id: int) -> None:
        """从仿真类型移除参数组合"""
        rel = self.sim_type_param_group_repo.find_by_sim_type_and_param_group(sim_type_id, param_group_id)
        if not rel:
            raise NotFoundError(f"仿真类型 {sim_type_id} 未关联参数组合 {param_group_id}")

        try:
            self.sim_type_param_group_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"移除参数组合失败: {str(e)}")

    # ============ 仿真类型-工况输出组合关联 ============

    def get_sim_type_cond_out_groups(self, sim_type_id: int) -> List[Dict[str, Any]]:
        """获取仿真类型关联的工况输出组合"""
        sim_type = self.sim_type_cond_out_group_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")

        rels = self.sim_type_cond_out_group_repo.find_by_sim_type_id(sim_type_id)
        results = []
        for rel in rels:
            cond_out_group = self.sim_type_cond_out_group_repo.find_cond_out_group_by_id(rel.cond_out_group_id)
            data = rel.to_dict()
            if cond_out_group:
                data['condOutGroupName'] = cond_out_group.name
                data['condOutGroupDescription'] = cond_out_group.description
            results.append(data)
        return results

    def add_cond_out_group_to_sim_type(self, sim_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加工况输出组合到仿真类型"""
        sim_type = self.sim_type_cond_out_group_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")

        cond_out_group_id = data['condOutGroupId']
        cond_out_group = self.sim_type_cond_out_group_repo.find_cond_out_group_by_id(cond_out_group_id)
        if not cond_out_group:
            raise NotFoundError(f"工况输出组合 {cond_out_group_id} 不存在")

        existing = self.sim_type_cond_out_group_repo.find_by_sim_type_and_cond_out_group(sim_type_id, cond_out_group_id)
        if existing:
            raise BusinessError(f"工况输出组合 {cond_out_group_id} 已关联到仿真类型")

        # 如果设置为默认，先取消其他默认
        if data.get('isDefault', 0) == 1:
            default_rel = self.sim_type_cond_out_group_repo.find_default_by_sim_type(sim_type_id)
            if default_rel:
                self.sim_type_cond_out_group_repo.update(default_rel, {'is_default': 0})

        rel_data = {
            'sim_type_id': sim_type_id,
            'cond_out_group_id': cond_out_group_id,
            'is_default': data.get('isDefault', 0),
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }

        try:
            rel = self.sim_type_cond_out_group_repo.create(rel_data)
            db.session.commit()
            result = rel.to_dict()
            result['condOutGroupName'] = cond_out_group.name
            result['condOutGroupDescription'] = cond_out_group.description
            return result
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"添加工况输出组合到仿真类型失败: {str(e)}")

    def set_default_cond_out_group_for_sim_type(self, sim_type_id: int, cond_out_group_id: int) -> None:
        """设置仿真类型的默认工况输出组合"""
        rel = self.sim_type_cond_out_group_repo.find_by_sim_type_and_cond_out_group(sim_type_id, cond_out_group_id)
        if not rel:
            raise NotFoundError(f"仿真类型 {sim_type_id} 未关联工况输出组合 {cond_out_group_id}")

        try:
            # 先取消其他默认
            default_rel = self.sim_type_cond_out_group_repo.find_default_by_sim_type(sim_type_id)
            if default_rel and default_rel.id != rel.id:
                self.sim_type_cond_out_group_repo.update(default_rel, {'is_default': 0})

            # 设置当前为默认
            self.sim_type_cond_out_group_repo.update(rel, {'is_default': 1})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"设置默认工况输出组合失败: {str(e)}")

    def remove_cond_out_group_from_sim_type(self, sim_type_id: int, cond_out_group_id: int) -> None:
        """从仿真类型移除工况输出组合"""
        rel = self.sim_type_cond_out_group_repo.find_by_sim_type_and_cond_out_group(sim_type_id, cond_out_group_id)
        if not rel:
            raise NotFoundError(f"仿真类型 {sim_type_id} 未关联工况输出组合 {cond_out_group_id}")

        try:
            self.sim_type_cond_out_group_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"移除工况输出组合失败: {str(e)}")

    # ============ 仿真类型-求解器关联 ============

    def get_sim_type_solvers(self, sim_type_id: int) -> List[Dict[str, Any]]:
        """获取仿真类型关联的求解器"""
        sim_type = self.sim_type_solver_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")

        rels = self.sim_type_solver_repo.find_by_sim_type_id(sim_type_id)
        results = []
        for rel in rels:
            solver = self.sim_type_solver_repo.find_solver_by_id(rel.solver_id)
            data = rel.to_dict()
            if solver:
                data['solverName'] = solver.name
                data['solverCode'] = solver.code
                data['solverVersion'] = solver.version
            results.append(data)
        return results

    def add_solver_to_sim_type(self, sim_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加求解器到仿真类型"""
        sim_type = self.sim_type_solver_repo.find_sim_type_by_id(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")

        solver_id = data['solverId']
        solver = self.sim_type_solver_repo.find_solver_by_id(solver_id)
        if not solver:
            raise NotFoundError(f"求解器 {solver_id} 不存在")

        existing = self.sim_type_solver_repo.find_by_sim_type_and_solver(sim_type_id, solver_id)
        if existing:
            raise BusinessError(f"求解器 {solver_id} 已关联到仿真类型")

        # 如果设置为默认，先取消其他默认
        if data.get('isDefault', 0) == 1:
            default_rel = self.sim_type_solver_repo.find_default_by_sim_type(sim_type_id)
            if default_rel:
                self.sim_type_solver_repo.update(default_rel, {'is_default': 0})

        rel_data = {
            'sim_type_id': sim_type_id,
            'solver_id': solver_id,
            'is_default': data.get('isDefault', 0),
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }

        try:
            rel = self.sim_type_solver_repo.create(rel_data)
            db.session.commit()
            result = rel.to_dict()
            result['solverName'] = solver.name
            result['solverCode'] = solver.code
            result['solverVersion'] = solver.version
            return result
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"添加求解器到仿真类型失败: {str(e)}")

    def set_default_solver_for_sim_type(self, sim_type_id: int, solver_id: int) -> None:
        """设置仿真类型的默认求解器"""
        rel = self.sim_type_solver_repo.find_by_sim_type_and_solver(sim_type_id, solver_id)
        if not rel:
            raise NotFoundError(f"仿真类型 {sim_type_id} 未关联求解器 {solver_id}")

        try:
            # 先取消其他默认
            default_rel = self.sim_type_solver_repo.find_default_by_sim_type(sim_type_id)
            if default_rel and default_rel.id != rel.id:
                self.sim_type_solver_repo.update(default_rel, {'is_default': 0})

            # 设置当前为默认
            self.sim_type_solver_repo.update(rel, {'is_default': 1})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"设置默认求解器失败: {str(e)}")

    def remove_solver_from_sim_type(self, sim_type_id: int, solver_id: int) -> None:
        """从仿真类型移除求解器"""
        rel = self.sim_type_solver_repo.find_by_sim_type_and_solver(sim_type_id, solver_id)
        if not rel:
            raise NotFoundError(f"仿真类型 {sim_type_id} 未关联求解器 {solver_id}")

        try:
            self.sim_type_solver_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"移除求解器失败: {str(e)}")

    # ============ 配置级联查询接口（新增）============

    def get_project_sim_types_with_full_config(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目支持的仿真类型（带完整配置）
        用于前端级联加载：项目 → 仿真类型 → 参数组/求解器

        返回格式:
        [
            {
                "id": 1,
                "name": "跌落",
                "code": "SIM_1",
                "isDefault": true,
                "paramGroups": [...],
                "solvers": [...]
            }
        ]
        """
        from app.common.serializers import serialize_model, serialize_models
        from app.api.v1.config.repository import (
            ProjectRepository, SimTypeRepository, SolverRepository,
            ModelLevelRepository, FoldTypeRepository, SolverResourceRepository
        )
        from app.models.config_relations import ParamGroup, ParamGroupParamRel

        # 验证项目存在
        project_repo = ProjectRepository()
        project = project_repo.find_by_id_valid(project_id)
        if not project:
            raise NotFoundError(f"项目 {project_id} 不存在")

        # 获取项目关联的仿真类型
        rels = self.project_sim_type_repo.find_by_project_id(project_id)

        result = []
        sim_type_repo = SimTypeRepository()

        for rel in rels:
            sim_type = sim_type_repo.find_by_id_valid(rel.sim_type_id)
            if not sim_type:
                continue

            sim_type_dict = serialize_model(sim_type)
            sim_type_dict['isDefault'] = bool(rel.is_default)

            # 获取参数组合（带参数详情）
            param_groups = self._get_param_groups_with_params()
            sim_type_dict['paramGroups'] = param_groups

            # 获取可用求解器
            solver_repo = SolverRepository()
            solvers = solver_repo.find_all_valid()
            sim_type_dict['solvers'] = serialize_models(solvers)

            result.append(sim_type_dict)

        return result

    def _get_param_groups_with_params(self) -> List[Dict[str, Any]]:
        """获取参数组合（带参数详情）- 内部方法"""
        from app.common.serializers import serialize_model
        from app.api.v1.config.repository import ParamDefRepository
        from app.models.config_relations import ParamGroup, ParamGroupParamRel

        param_groups = db.session.query(ParamGroup).filter_by(valid=1).order_by(ParamGroup.sort.asc()).all()

        result = []
        param_def_repo = ParamDefRepository()

        for group in param_groups:
            group_dict = serialize_model(group)

            # 获取参数组包含的参数
            param_rels = db.session.query(ParamGroupParamRel).filter_by(
                param_group_id=group.id
            ).order_by(ParamGroupParamRel.sort.asc()).all()

            params = []
            for rel in param_rels:
                param = param_def_repo.find_by_id_valid(rel.param_def_id)
                if param:
                    param_dict = serialize_model(param)
                    if rel.default_value:
                        param_dict['defaultValue'] = rel.default_value
                    params.append(param_dict)

            group_dict['params'] = params
            result.append(group_dict)

        return result

    def get_sim_type_full_config(self, sim_type_id: int, fold_type: int = 0) -> Dict[str, Any]:
        """
        获取仿真类型的完整配置
        用于提单页面初始化，一次性获取所有需要的配置

        Args:
            sim_type_id: 仿真类型ID
            fold_type: 折叠态类型 (0=展开态, 1=折叠态)

        Returns:
            完整配置字典
        """
        from app.common.serializers import serialize_model, serialize_models
        from app.api.v1.config.repository import (
            SimTypeRepository, SolverRepository, ModelLevelRepository,
            FoldTypeRepository, SolverResourceRepository
        )

        # 验证仿真类型存在
        sim_type_repo = SimTypeRepository()
        sim_type = sim_type_repo.find_by_id_valid(sim_type_id)
        if not sim_type:
            raise NotFoundError(f"仿真类型 {sim_type_id} 不存在")

        # 获取参数组合
        param_groups = self._get_param_groups_with_params()

        # 获取求解器
        solver_repo = SolverRepository()
        solvers = solver_repo.find_all_valid()

        # 获取求解器资源池
        resource_repo = SolverResourceRepository()
        resources = resource_repo.find_all_valid()

        # 获取模型层级
        level_repo = ModelLevelRepository()
        levels = level_repo.find_all_valid()

        # 获取折叠态类型
        fold_type_repo = FoldTypeRepository()
        fold_types = fold_type_repo.find_all_valid()

        return {
            'simType': serialize_model(sim_type),
            'foldType': fold_type,
            'paramGroups': param_groups,
            'defaultParamGroup': param_groups[0] if param_groups else None,
            'solvers': serialize_models(solvers),
            'defaultSolver': serialize_model(solvers[0]) if solvers else None,
            'solverResources': serialize_models(resources),
            'defaultResource': serialize_model(resources[0]) if resources else None,
            'modelLevels': serialize_models(levels),
            'foldTypes': serialize_models(fold_types)
        }

    def get_default_config_for_order(
        self,
        project_id: int,
        sim_type_id: int,
        fold_type: int = 0
    ) -> Dict[str, Any]:
        """
        获取提单默认配置（核心接口）
        前端提单页面初始化时调用此接口，一次性获取所有需要的配置

        Args:
            project_id: 项目ID
            sim_type_id: 仿真类型ID
            fold_type: 折叠态类型 (0=展开态, 1=折叠态)

        Returns:
            默认配置字典，包含项目、仿真类型、参数组、求解器等所有配置
        """
        from app.common.serializers import serialize_model
        from app.api.v1.config.repository import ProjectRepository

        # 验证项目和仿真类型关联
        rel = self.project_sim_type_repo.find_by_project_and_sim_type(project_id, sim_type_id)
        if not rel:
            raise NotFoundError(f"项目 {project_id} 不支持仿真类型 {sim_type_id}")

        # 获取项目信息
        project_repo = ProjectRepository()
        project = project_repo.find_by_id_valid(project_id)
        if not project:
            raise NotFoundError(f"项目 {project_id} 不存在")

        # 获取仿真类型的完整配置
        full_config = self.get_sim_type_full_config(sim_type_id, fold_type)

        # 添加项目信息
        full_config['project'] = serialize_model(project)

        return full_config


