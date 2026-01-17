"""
配置中心 - 服务层
职责：业务编排、事务管理、调用Repository、组装返回数据
禁止：直接SQL操作、HTTP相关逻辑
"""
from typing import Optional, List, Dict, Any
from app.common.errors import NotFoundError
from app.api.v1.config.repository import (
    SimTypeRepository, ParamDefRepository, SolverRepository,
    ConditionDefRepository, OutputDefRepository, FoldTypeRepository,
    ParamTplSetRepository, CondOutSetRepository, WorkflowRepository,
    StatusDefRepository, AutomationModuleRepository
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

    # ============ 通用CRUD方法 ============
    def _list(self, repo, to_dict=True) -> List:
        items = repo.find_all_valid()
        return [item.to_dict() for item in items] if to_dict else items

    def _get(self, repo, id: int, name: str) -> Dict:
        item = repo.find_by_id_valid(id)
        if not item:
            raise NotFoundError(name, id)
        return item.to_dict()

    def _create(self, repo, data: Dict) -> Dict:
        item = repo.create(data)
        return item.to_dict()

    def _update(self, repo, id: int, data: Dict, name: str) -> Dict:
        item = repo.update(id, data)
        if not item:
            raise NotFoundError(name, id)
        return item.to_dict()

    def _delete(self, repo, id: int, name: str) -> bool:
        if not repo.soft_delete(id):
            raise NotFoundError(name, id)
        return True

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
            'automationModules': self.get_automation_modules()
        }


# 单例实例
config_service = ConfigService()

