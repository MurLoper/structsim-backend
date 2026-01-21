from app.constants import ErrorCode
from app.models.config import Project, SimType, ParamDef, ConditionDef, OutputDef, Solver
from app.models.config_relations import (
    ProjectSimTypeRel,
    ParamGroup,
    ParamGroupParamRel,
    SimTypeParamGroupRel,
    ConditionOutputGroup,
    CondOutGroupConditionRel,
    CondOutGroupOutputRel,
    SimTypeCondOutGroupRel,
    SimTypeSolverRel,
)


def test_order_init_config_missing_project(client):
    resp = client.get('/api/v1/orders/init-config')
    data = resp.get_json()
    assert data['code'] == ErrorCode.VALIDATION_ERROR


def test_order_init_config_success(client, db_session):
    project = Project(name='项目A', code='PROJ_INIT', valid=1, sort=1)
    sim_type = SimType(name='结构', code='SIM_INIT', category='STRUCT', valid=1, sort=1)
    db_session.add(project)
    db_session.add(sim_type)
    db_session.commit()

    project_rel = ProjectSimTypeRel(project_id=project.id, sim_type_id=sim_type.id, is_default=1, sort=1)
    db_session.add(project_rel)

    param_def = ParamDef(name='参数A', key='param_init', val_type=1, required=1, sort=1)
    db_session.add(param_def)
    db_session.commit()

    param_group = ParamGroup(name='参数组A', description='demo', valid=1, sort=1)
    db_session.add(param_group)
    db_session.commit()

    param_rel = ParamGroupParamRel(param_group_id=param_group.id, param_def_id=param_def.id, default_value='1')
    db_session.add(param_rel)

    sim_param_rel = SimTypeParamGroupRel(sim_type_id=sim_type.id, param_group_id=param_group.id, is_default=1)
    db_session.add(sim_param_rel)

    condition_def = ConditionDef(name='工况A', code='COND_INIT', condition_schema={'k': 'v'}, valid=1, sort=1)
    output_def = OutputDef(name='输出A', code='OUT_INIT', val_type=1, valid=1, sort=1)
    db_session.add(condition_def)
    db_session.add(output_def)
    db_session.commit()

    cond_out_group = ConditionOutputGroup(name='工况输出组A', valid=1, sort=1)
    db_session.add(cond_out_group)
    db_session.commit()

    cond_rel = CondOutGroupConditionRel(
        cond_out_group_id=cond_out_group.id,
        condition_def_id=condition_def.id,
        config_data={'x': 1},
    )
    output_rel = CondOutGroupOutputRel(cond_out_group_id=cond_out_group.id, output_def_id=output_def.id)
    db_session.add(cond_rel)
    db_session.add(output_rel)

    sim_cond_rel = SimTypeCondOutGroupRel(sim_type_id=sim_type.id, cond_out_group_id=cond_out_group.id, is_default=1)
    db_session.add(sim_cond_rel)

    solver = Solver(name='SolverInit', code='SOL_INIT', sort=1)
    db_session.add(solver)
    db_session.commit()

    sim_solver_rel = SimTypeSolverRel(sim_type_id=sim_type.id, solver_id=solver.id, is_default=1)
    db_session.add(sim_solver_rel)

    db_session.commit()

    resp = client.get(f'/api/v1/orders/init-config?projectId={project.id}')
    data = resp.get_json()
    assert data['code'] == ErrorCode.SUCCESS
    assert data['data']['projectId'] == project.id
    assert data['data']['simTypeId'] == sim_type.id
    assert data['data']['defaultParamGroup']['paramGroupId'] == param_group.id
    assert data['data']['defaultCondOutGroup']['condOutGroupId'] == cond_out_group.id
    assert data['data']['defaultSolver']['solverId'] == solver.id
