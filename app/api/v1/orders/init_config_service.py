"""
提单初始化 - Service层
职责：业务逻辑、获取初始化配置
禁止：HTTP相关逻辑
"""
from typing import Optional, Dict, Any, List
from app.extensions import db
from app.common.errors import NotFoundError, BusinessError
from app.models import (
    Project,
    SimType,
    ProjectSimTypeRel,
    SimTypeParamGroupRel,
    SimTypeCondOutGroupRel,
    SimTypeSolverRel,
    ParamGroup,
    ConditionOutputGroup,
    Solver,
    ParamGroupParamRel,
    CondOutGroupConditionRel,
    CondOutGroupOutputRel,
    ParamDef,
    ConditionDef,
    OutputDef
)


class OrderInitConfigService:
    """提单初始化配置服务"""
    
    def get_init_config(self, project_id: int, sim_type_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取提单初始化配置
        
        Args:
            project_id: 项目ID
            sim_type_id: 仿真类型ID，不传则使用项目默认
            
        Returns:
            初始化配置字典
        """
        # 1. 查询项目
        project = db.session.get(Project, project_id)
        if not project:
            raise NotFoundError(f"项目 {project_id} 不存在")
        
        # 2. 确定仿真类型
        if sim_type_id:
            # 验证仿真类型是否关联到项目
            rel = db.session.query(ProjectSimTypeRel).filter_by(
                project_id=project_id,
                sim_type_id=sim_type_id
            ).first()
            if not rel:
                raise BusinessError(f"仿真类型 {sim_type_id} 未关联到项目 {project_id}")
            sim_type = db.session.get(SimType, sim_type_id)
        else:
            # 使用项目默认仿真类型
            default_rel = db.session.query(ProjectSimTypeRel).filter_by(
                project_id=project_id,
                is_default=1
            ).first()
            if not default_rel:
                raise BusinessError(f"项目 {project_id} 未设置默认仿真类型")
            sim_type = db.session.get(SimType, default_rel.sim_type_id)
        
        if not sim_type:
            raise NotFoundError(f"仿真类型不存在")
        
        # 3. 获取参数组合选项
        param_group_options = self._get_param_group_options(sim_type.id)
        default_param_group = next((opt for opt in param_group_options if opt['isDefault'] == 1), None)
        
        # 4. 获取工况输出组合选项
        cond_out_group_options = self._get_cond_out_group_options(sim_type.id)
        default_cond_out_group = next((opt for opt in cond_out_group_options if opt['isDefault'] == 1), None)
        
        # 5. 获取求解器选项
        solver_options = self._get_solver_options(sim_type.id)
        default_solver = next((opt for opt in solver_options if opt['isDefault'] == 1), None)
        
        # 6. 组装响应
        return {
            'projectId': project.id,
            'projectName': project.name,
            'simTypeId': sim_type.id,
            'simTypeName': sim_type.name,
            'simTypeCode': sim_type.code,
            'defaultParamGroup': default_param_group,
            'defaultCondOutGroup': default_cond_out_group,
            'defaultSolver': default_solver,
            'paramGroupOptions': param_group_options,
            'condOutGroupOptions': cond_out_group_options,
            'solverOptions': solver_options
        }
    
    def _get_param_group_options(self, sim_type_id: int) -> List[Dict[str, Any]]:
        """获取参数组合选项"""
        rels = db.session.query(SimTypeParamGroupRel).filter_by(
            sim_type_id=sim_type_id
        ).order_by(SimTypeParamGroupRel.sort.asc()).all()
        
        options = []
        for rel in rels:
            param_group = db.session.get(ParamGroup, rel.param_group_id)
            if not param_group:
                continue
            
            # 获取参数组合包含的参数
            param_rels = db.session.query(ParamGroupParamRel).filter_by(
                param_group_id=param_group.id
            ).order_by(ParamGroupParamRel.sort.asc()).all()
            
            params = []
            for param_rel in param_rels:
                param_def = db.session.get(ParamDef, param_rel.param_def_id)
                if param_def:
                    params.append({
                        'paramDefId': param_def.id,
                        'paramName': param_def.name,
                        'paramKey': param_def.key,
                        'defaultValue': param_rel.default_value or param_def.default_value,
                        'unit': param_def.unit,
                        'valType': param_def.val_type,
                        'required': param_def.required
                    })
            
            options.append({
                'paramGroupId': param_group.id,
                'paramGroupName': param_group.name,
                'isDefault': rel.is_default,
                'params': params
            })
        
        return options
    
    def _get_cond_out_group_options(self, sim_type_id: int) -> List[Dict[str, Any]]:
        """获取工况输出组合选项"""
        rels = db.session.query(SimTypeCondOutGroupRel).filter_by(
            sim_type_id=sim_type_id
        ).order_by(SimTypeCondOutGroupRel.sort.asc()).all()
        
        options = []
        for rel in rels:
            cond_out_group = db.session.get(ConditionOutputGroup, rel.cond_out_group_id)
            if not cond_out_group:
                continue
            
            # 获取工况
            cond_rels = db.session.query(CondOutGroupConditionRel).filter_by(
                cond_out_group_id=cond_out_group.id
            ).order_by(CondOutGroupConditionRel.sort.asc()).all()
            
            conditions = []
            for cond_rel in cond_rels:
                cond_def = db.session.get(ConditionDef, cond_rel.condition_def_id)
                if cond_def:
                    conditions.append({
                        'conditionDefId': cond_def.id,
                        'conditionName': cond_def.name,
                        'conditionCode': cond_def.code,
                        'configData': cond_rel.config_data,
                        'conditionSchema': cond_def.condition_schema
                    })

            # 获取输出
            output_rels = db.session.query(CondOutGroupOutputRel).filter_by(
                cond_out_group_id=cond_out_group.id
            ).order_by(CondOutGroupOutputRel.sort.asc()).all()

            outputs = []
            for output_rel in output_rels:
                output_def = db.session.get(OutputDef, output_rel.output_def_id)
                if output_def:
                    outputs.append({
                        'outputDefId': output_def.id,
                        'outputName': output_def.name,
                        'outputCode': output_def.code,
                        'unit': output_def.unit,
                        'valType': output_def.val_type
                    })

            options.append({
                'condOutGroupId': cond_out_group.id,
                'condOutGroupName': cond_out_group.name,
                'isDefault': rel.is_default,
                'conditions': conditions,
                'outputs': outputs
            })

        return options

    def _get_solver_options(self, sim_type_id: int) -> List[Dict[str, Any]]:
        """获取求解器选项"""
        rels = db.session.query(SimTypeSolverRel).filter_by(
            sim_type_id=sim_type_id
        ).order_by(SimTypeSolverRel.sort.asc()).all()

        options = []
        for rel in rels:
            solver = db.session.get(Solver, rel.solver_id)
            if solver:
                options.append({
                    'solverId': solver.id,
                    'solverName': solver.name,
                    'solverCode': solver.code,
                    'solverVersion': solver.version,
                    'isDefault': rel.is_default
                })

        return options

