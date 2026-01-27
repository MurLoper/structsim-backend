"""
配置中心 - 服务层
职责：业务编排、事务管理、调用Repository、组装返回数据
禁止：直接SQL操作、HTTP相关逻辑
"""
from typing import Optional, List, Dict, Any
from app.common.errors import NotFoundError
from app.common.serializers import serialize_model, serialize_models
from app.api.v1.config.repository import (
    ProjectRepository, SimTypeRepository, ParamDefRepository, SolverRepository,
    ConditionDefRepository, OutputDefRepository, FoldTypeRepository,
    ParamTplSetRepository, CondOutSetRepository, WorkflowRepository,
    StatusDefRepository, AutomationModuleRepository,
    ModelLevelRepository, CareDeviceRepository, SolverResourceRepository, DepartmentRepository
)


class ConfigService:
    """配置中心服务 - 业务编排层"""

    def __init__(self):
        self._repos: Dict[str, Any] = {}

    def _get_repo(self, name: str, repo_class):
        """懒加载Repository"""
        if name not in self._repos:
            self._repos[name] = repo_class()
        return self._repos[name]

    @property
    def project_repo(self) -> ProjectRepository:
        return self._get_repo('project', ProjectRepository)

    @property
    def sim_type_repo(self) -> SimTypeRepository:
        return self._get_repo('sim_type', SimTypeRepository)

    @property
    def param_def_repo(self) -> ParamDefRepository:
        return self._get_repo('param_def', ParamDefRepository)

    @property
    def solver_repo(self) -> SolverRepository:
        return self._get_repo('solver', SolverRepository)

    @property
    def condition_def_repo(self) -> ConditionDefRepository:
        return self._get_repo('condition_def', ConditionDefRepository)

    @property
    def output_def_repo(self) -> OutputDefRepository:
        return self._get_repo('output_def', OutputDefRepository)

    @property
    def fold_type_repo(self) -> FoldTypeRepository:
        return self._get_repo('fold_type', FoldTypeRepository)

    @property
    def param_tpl_set_repo(self) -> ParamTplSetRepository:
        return self._get_repo('param_tpl_set', ParamTplSetRepository)

    @property
    def cond_out_set_repo(self) -> CondOutSetRepository:
        return self._get_repo('cond_out_set', CondOutSetRepository)

    @property
    def workflow_repo(self) -> WorkflowRepository:
        return self._get_repo('workflow', WorkflowRepository)

    @property
    def status_def_repo(self) -> StatusDefRepository:
        return self._get_repo('status_def', StatusDefRepository)

    @property
    def automation_module_repo(self) -> AutomationModuleRepository:
        return self._get_repo('automation_module', AutomationModuleRepository)

    @property
    def model_level_repo(self) -> ModelLevelRepository:
        return self._get_repo('model_level', ModelLevelRepository)

    @property
    def care_device_repo(self) -> CareDeviceRepository:
        return self._get_repo('care_device', CareDeviceRepository)

    @property
    def solver_resource_repo(self) -> SolverResourceRepository:
        return self._get_repo('solver_resource', SolverResourceRepository)

    @property
    def department_repo(self) -> DepartmentRepository:
        return self._get_repo('department', DepartmentRepository)

    # ============ 通用CRUD方法 ============
    def _list(self, repo, to_dict=True) -> List:
        items = repo.find_all_valid()
        return serialize_models(items) if to_dict else items

    def _get(self, repo, id: int, name: str) -> Dict:
        item = repo.find_by_id_valid(id)
        if not item:
            raise NotFoundError(name, id)
        return serialize_model(item)

    def _create(self, repo, data: Dict) -> Dict:
        item = repo.create(data)
        return serialize_model(item)

    def _update(self, repo, id: int, data: Dict, name: str) -> Dict:
        item = repo.update(id, data)
        if not item:
            raise NotFoundError(name, id)
        return serialize_model(item)

    def _delete(self, repo, id: int, name: str) -> bool:
        if not repo.soft_delete(id):
            raise NotFoundError(name, id)
        return True

    # ============ 项目配置 ============
    def get_projects(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        获取项目列表
        如果提供 user_id，则只返回该用户有权限的项目
        如果是管理员，返回所有项目
        """
        if user_id:
            # 权限检查：目前允许所有认证用户操作，后续可结合RBAC
            # 如果是管理员，返回所有项目
            # 如果是普通用户，只返回有权限的项目
            projects = self.project_repo.find_by_user(user_id)
        else:
            projects = self.project_repo.find_all_valid()
        return serialize_models(projects)

    def get_project(self, id: int) -> Dict:
        """获取单个项目"""
        return self._get(self.project_repo, id, "项目")

    def create_project(self, data: Dict) -> Dict:
        """创建项目"""
        return self._create(self.project_repo, data)

    def update_project(self, id: int, data: Dict) -> Dict:
        """更新项目"""
        return self._update(self.project_repo, id, data, "项目")

    def delete_project(self, id: int) -> bool:
        """删除项目（软删除）"""
        return self._delete(self.project_repo, id, "项目")

    # ============ 仿真类型 ============
    def get_sim_types(self) -> List[Dict]:
        return self._list(self.sim_type_repo)

    def get_sim_type(self, id: int) -> Dict:
        return self._get(self.sim_type_repo, id, "仿真类型")

    def create_sim_type(self, data: Dict) -> Dict:
        return self._create(self.sim_type_repo, data)

    def update_sim_type(self, id: int, data: Dict) -> Dict:
        return self._update(self.sim_type_repo, id, data, "仿真类型")

    def delete_sim_type(self, id: int) -> bool:
        return self._delete(self.sim_type_repo, id, "仿真类型")

    # ============ 参数定义 ============
    def get_param_defs(self) -> List[Dict]:
        return self._list(self.param_def_repo)

    def create_param_def(self, data: Dict) -> Dict:
        return self._create(self.param_def_repo, data)

    def update_param_def(self, id: int, data: Dict) -> Dict:
        return self._update(self.param_def_repo, id, data, "参数定义")

    def delete_param_def(self, id: int) -> bool:
        return self._delete(self.param_def_repo, id, "参数定义")

    # ============ 求解器 ============
    def get_solvers(self) -> List[Dict]:
        return self._list(self.solver_repo)

    def create_solver(self, data: Dict) -> Dict:
        return self._create(self.solver_repo, data)

    def update_solver(self, id: int, data: Dict) -> Dict:
        return self._update(self.solver_repo, id, data, "求解器")

    def delete_solver(self, id: int) -> bool:
        return self._delete(self.solver_repo, id, "求解器")

    # ============ 工况定义 ============
    def get_condition_defs(self) -> List[Dict]:
        return self._list(self.condition_def_repo)

    def create_condition_def(self, data: Dict) -> Dict:
        return self._create(self.condition_def_repo, data)

    def update_condition_def(self, id: int, data: Dict) -> Dict:
        return self._update(self.condition_def_repo, id, data, "工况定义")

    def delete_condition_def(self, id: int) -> bool:
        return self._delete(self.condition_def_repo, id, "工况定义")

    # ============ 输出定义 ============
    def get_output_defs(self) -> List[Dict]:
        return self._list(self.output_def_repo)

    def create_output_def(self, data: Dict) -> Dict:
        return self._create(self.output_def_repo, data)

    def update_output_def(self, id: int, data: Dict) -> Dict:
        return self._update(self.output_def_repo, id, data, "输出定义")

    def delete_output_def(self, id: int) -> bool:
        return self._delete(self.output_def_repo, id, "输出定义")

    # ============ 姿态类型 ============
    def get_fold_types(self) -> List[Dict]:
        return self._list(self.fold_type_repo)

    def create_fold_type(self, data: Dict) -> Dict:
        return self._create(self.fold_type_repo, data)

    def update_fold_type(self, id: int, data: Dict) -> Dict:
        return self._update(self.fold_type_repo, id, data, "姿态类型")

    def delete_fold_type(self, id: int) -> bool:
        return self._delete(self.fold_type_repo, id, "姿态类型")

    # ============ 模板集查询 ============
    def get_param_tpl_sets(self, sim_type_id: Optional[int] = None) -> List[Dict]:
        if sim_type_id:
            items = self.param_tpl_set_repo.find_by_sim_type(sim_type_id)
        else:
            items = self.param_tpl_set_repo.find_all_valid()
        return [item.to_dict() for item in items]

    def get_cond_out_sets(self, sim_type_id: Optional[int] = None) -> List[Dict]:
        if sim_type_id:
            items = self.cond_out_set_repo.find_by_sim_type(sim_type_id)
        else:
            items = self.cond_out_set_repo.find_all_valid()
        return [item.to_dict() for item in items]

    # ============ 其他配置查询 ============
    def get_workflows(self, workflow_type: Optional[str] = None) -> List[Dict]:
        if workflow_type:
            items = self.workflow_repo.find_by_type(workflow_type)
        else:
            items = self.workflow_repo.find_all_valid()
        return [item.to_dict() for item in items]

    def get_status_defs(self) -> List[Dict]:
        return self._list(self.status_def_repo)

    def update_status_def(self, id: int, data: Dict) -> Dict:
        """更新状态定义"""
        return self._update(self.status_def_repo, id, data, "状态定义")

    def get_automation_modules(self, category: Optional[str] = None) -> List[Dict]:
        if category:
            items = self.automation_module_repo.find_by_category(category)
        else:
            items = self.automation_module_repo.find_all_valid()
        return [item.to_dict() for item in items]

    # ============ 聚合接口 ============
    def get_base_data(self) -> Dict[str, List]:
        """获取所有基础配置数据（用于前端初始化）"""
        return {
            'simTypes': self.get_sim_types(),
            'paramDefs': self.get_param_defs(),
            'conditionDefs': self.get_condition_defs(),
            'outputDefs': self.get_output_defs(),
            'solvers': self.get_solvers(),
            'statusDefs': self.get_status_defs(),
            'foldTypes': self.get_fold_types(),
            'automationModules': self.get_automation_modules(),
            'modelLevels': self.get_model_levels(),
            'careDevices': self.get_care_devices(),
            'solverResources': self.get_solver_resources(),
            'departments': self.get_departments()
        }

    # ============ 模型层级 ============
    def get_model_levels(self) -> List[Dict]:
        return self._list(self.model_level_repo)

    def get_model_level(self, id: int) -> Dict:
        return self._get(self.model_level_repo, id, "模型层级")

    def create_model_level(self, data: Dict) -> Dict:
        return self._create(self.model_level_repo, data)

    def update_model_level(self, id: int, data: Dict) -> Dict:
        return self._update(self.model_level_repo, id, data, "模型层级")

    def delete_model_level(self, id: int) -> bool:
        return self._delete(self.model_level_repo, id, "模型层级")

    # ============ 关注器件 ============
    def get_care_devices(self) -> List[Dict]:
        return self._list(self.care_device_repo)

    def get_care_device(self, id: int) -> Dict:
        return self._get(self.care_device_repo, id, "关注器件")

    def create_care_device(self, data: Dict) -> Dict:
        return self._create(self.care_device_repo, data)

    def update_care_device(self, id: int, data: Dict) -> Dict:
        return self._update(self.care_device_repo, id, data, "关注器件")

    def delete_care_device(self, id: int) -> bool:
        return self._delete(self.care_device_repo, id, "关注器件")

    # ============ 求解器资源池 ============
    def get_solver_resources(self) -> List[Dict]:
        return self._list(self.solver_resource_repo)

    def get_solver_resource(self, id: int) -> Dict:
        return self._get(self.solver_resource_repo, id, "求解器资源池")

    def create_solver_resource(self, data: Dict) -> Dict:
        return self._create(self.solver_resource_repo, data)

    def update_solver_resource(self, id: int, data: Dict) -> Dict:
        return self._update(self.solver_resource_repo, id, data, "求解器资源池")

    def delete_solver_resource(self, id: int) -> bool:
        return self._delete(self.solver_resource_repo, id, "求解器资源池")

    # ============ 部门 ============
    def get_departments(self) -> List[Dict]:
        return self._list(self.department_repo)

    def get_department(self, id: int) -> Dict:
        return self._get(self.department_repo, id, "部门")

    def create_department(self, data: Dict) -> Dict:
        return self._create(self.department_repo, data)

    def update_department(self, id: int, data: Dict) -> Dict:
        return self._update(self.department_repo, id, data, "部门")

    def delete_department(self, id: int) -> bool:
        return self._delete(self.department_repo, id, "部门")

    def get_sub_departments(self, parent_id: int) -> List[Dict]:
        """获取子部门列表"""
        items = self.department_repo.find_by_parent_id(parent_id)
        return [item.to_dict() for item in items]


# 单例实例
config_service = ConfigService()

