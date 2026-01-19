"""
数据库种子脚本 - 填充初始测试数据
按照 requirement_and_design.md 规范设计
"""
import time
from app import create_app, db
from app.models import (
    # 配置表
    Project, SimType, ParamDef, ParamTplSet, ParamTplItem,
    ConditionDef, OutputDef, CondOutSet, Solver, Workflow,
    StatusDef, AutomationModule, FoldType,
    # 权限表
    User, Role, Permission, Menu
)


def seed_database():
    """Seed the database with initial data."""
    app = create_app()

    with app.app_context():
        # Create tables
        db.create_all()

        print("Clearing existing data...")
        # 清除现有数据（按依赖顺序）
        db.session.query(ParamTplItem).delete()
        db.session.query(ParamTplSet).delete()
        db.session.query(CondOutSet).delete()
        db.session.query(Project).delete()
        db.session.query(SimType).delete()
        db.session.query(ParamDef).delete()
        db.session.query(ConditionDef).delete()
        db.session.query(OutputDef).delete()
        db.session.query(Solver).delete()
        db.session.query(Workflow).delete()
        db.session.query(StatusDef).delete()
        db.session.query(AutomationModule).delete()
        db.session.query(FoldType).delete()
        db.session.query(Menu).delete()
        db.session.query(Permission).delete()
        db.session.query(Role).delete()
        db.session.query(User).delete()

        now = int(time.time())

        print("Seeding users...")
        # ============ 用户 ============
        users = [
            User(id=1, username='alice', email='alice@sim.com', name='Alice Admin',
                 role_ids=[1], valid=1, preferences={'lang': 1, 'theme': 1}, created_at=now),
            User(id=2, username='bob', email='bob@sim.com', name='Bob Engineer',
                 role_ids=[2], valid=1, preferences={'lang': 1, 'theme': 1}, created_at=now),
            User(id=3, username='charlie', email='charlie@sim.com', name='Charlie Viewer',
                 role_ids=[3], valid=1, preferences={'lang': 1, 'theme': 1}, created_at=now),
            User(id=4, username='guest', email='guest@sim.com', name='Guest',
                 role_ids=[], valid=1, preferences={'lang': 1, 'theme': 1}, created_at=now),
        ]
        db.session.add_all(users)

        print("Seeding roles and permissions...")
        # ============ 权限 ============
        permissions = [
            Permission(id=1, name='查看工作台', code='VIEW_DASHBOARD', type='PAGE', valid=1, sort=10),
            Permission(id=2, name='创建提单', code='CREATE_ORDER', type='PAGE', valid=1, sort=20),
            Permission(id=3, name='查看申请单', code='VIEW_ORDERS', type='PAGE', valid=1, sort=30),
            Permission(id=4, name='查看结果', code='VIEW_RESULTS', type='PAGE', valid=1, sort=40),
            Permission(id=5, name='管理配置', code='MANAGE_CONFIG', type='PAGE', valid=1, sort=50),
            Permission(id=6, name='管理用户', code='MANAGE_USERS', type='PAGE', valid=1, sort=60),
        ]
        db.session.add_all(permissions)

        # ============ 角色 ============
        admin_permission_ids = [p.id for p in permissions]
        roles = [
            Role(id=1, name='管理员', code='ADMIN', description='系统管理员',
                 permission_ids=admin_permission_ids, valid=1, sort=10),
            Role(id=2, name='工程师', code='ENGINEER', description='仿真工程师',
                 permission_ids=[1, 2, 3, 4], valid=1, sort=20),
            Role(id=3, name='查看者', code='VIEWER', description='只读用户',
                 permission_ids=[1, 3, 4], valid=1, sort=30),
        ]
        db.session.add_all(roles)

        print("Seeding simulation types...")
        # ============ 仿真类型（至少5种）============
        sim_types = [
            SimType(id=1, name='静力分析', code='STATIC', category='STRUCTURE',
                    support_alg_mask=3, node_icon='static', color_tag='blue', valid=1, sort=10),
            SimType(id=2, name='模态分析', code='MODAL', category='STRUCTURE',
                    support_alg_mask=1, node_icon='modal', color_tag='green', valid=1, sort=20),
            SimType(id=3, name='热分析', code='THERMAL', category='THERMAL',
                    support_alg_mask=3, node_icon='thermal', color_tag='orange', valid=1, sort=30),
            SimType(id=4, name='疲劳分析', code='FATIGUE', category='STRUCTURE',
                    support_alg_mask=3, node_icon='fatigue', color_tag='red', valid=1, sort=40),
            SimType(id=5, name='碰撞分析', code='CRASH', category='DYNAMIC',
                    support_alg_mask=1, node_icon='crash', color_tag='purple', valid=1, sort=50),
            SimType(id=6, name='NVH分析', code='NVH', category='ACOUSTIC',
                    support_alg_mask=3, node_icon='nvh', color_tag='cyan', valid=1, sort=60),
        ]
        for st in sim_types:
            db.session.add(st)
        db.session.flush()

        print("Seeding parameter definitions...")
        # ============ 参数定义 ============
        param_defs = [
            ParamDef(id=1, name='厚度', key='thickness', val_type=1, unit='mm',
                     min_val=0.1, max_val=10, precision=3, required=1, valid=1, sort=10),
            ParamDef(id=2, name='密度', key='density', val_type=1, unit='kg/m³',
                     min_val=1000, max_val=10000, precision=1, required=1, valid=1, sort=20),
            ParamDef(id=3, name='弹性模量', key='youngs_modulus', val_type=1, unit='GPa',
                     min_val=60, max_val=220, precision=1, required=1, valid=1, sort=30),
            ParamDef(id=4, name='泊松比', key='poisson_ratio', val_type=1, unit='',
                     min_val=0.1, max_val=0.5, precision=3, required=1, valid=1, sort=40),
            ParamDef(id=5, name='材料ID', key='material_id', val_type=4, unit='',
                     enum_options=['Steel_1040', 'Alum_6061', 'Ti_Alloy', 'Carbon_Fiber'],
                     required=1, valid=1, sort=50),
            ParamDef(id=6, name='载荷', key='load', val_type=1, unit='N',
                     min_val=0, max_val=100000, precision=0, required=1, valid=1, sort=60),
            ParamDef(id=7, name='温度', key='temperature', val_type=1, unit='°C',
                     min_val=-50, max_val=200, precision=1, required=0, valid=1, sort=70),
        ]
        for p in param_defs:
            db.session.add(p)
        db.session.flush()

        print("Seeding condition definitions...")
        # ============ 工况定义 ============
        condition_defs = [
            ConditionDef(id=1, name='弯曲工况', code='BENDING',
                        schema={'load': {'type': 'number', 'unit': 'N'}, 'direction': {'type': 'enum', 'values': ['X', 'Y', 'Z']}},
                        valid=1, sort=10),
            ConditionDef(id=2, name='扭转工况', code='TORSION',
                        schema={'torque': {'type': 'number', 'unit': 'Nm'}, 'axis': {'type': 'enum', 'values': ['X', 'Y', 'Z']}},
                        valid=1, sort=20),
            ConditionDef(id=3, name='制动工况', code='BRAKING',
                        schema={'deceleration': {'type': 'number', 'unit': 'g'}},
                        valid=1, sort=30),
            ConditionDef(id=4, name='转弯工况', code='CORNERING',
                        schema={'lateral_g': {'type': 'number', 'unit': 'g'}},
                        valid=1, sort=40),
        ]
        for c in condition_defs:
            db.session.add(c)
        db.session.flush()

        print("Seeding output definitions...")
        # ============ 输出定义 ============
        output_defs = [
            OutputDef(id=1, name='最大变形', code='MAX_DEFORM', val_type=1, unit='mm', valid=1, sort=10),
            OutputDef(id=2, name='最大应力', code='MAX_STRESS', val_type=1, unit='MPa', valid=1, sort=20),
            OutputDef(id=3, name='安全系数', code='SAFETY_FACTOR', val_type=1, unit='', valid=1, sort=30),
            OutputDef(id=4, name='质量', code='MASS', val_type=1, unit='kg', valid=1, sort=40),
            OutputDef(id=5, name='最高温度', code='MAX_TEMP', val_type=1, unit='°C', valid=1, sort=50),
            OutputDef(id=6, name='一阶频率', code='FREQ_1ST', val_type=1, unit='Hz', valid=1, sort=60),
        ]
        for o in output_defs:
            db.session.add(o)
        db.session.flush()

        print("Seeding projects...")
        # ============ 项目 ============
        projects = [
            Project(id=1, name='底盘刚度优化', code='CHASSIS_OPT', default_sim_type_id=1,
                    default_solver_id=1, valid=1, sort=10, created_at=now),
            Project(id=2, name='电池包热分析', code='BATTERY_THERMAL', default_sim_type_id=3,
                    default_solver_id=2, valid=1, sort=20, created_at=now),
            Project(id=3, name='悬架臂应力测试', code='SUSPENSION_STRESS', default_sim_type_id=1,
                    default_solver_id=1, valid=1, sort=30, created_at=now),
            Project(id=4, name='车身气动分析', code='BODY_AERO', default_sim_type_id=1,
                    default_solver_id=3, valid=1, sort=40, created_at=now),
            Project(id=5, name='碰撞测试', code='CRASH_TEST', default_sim_type_id=5,
                    default_solver_id=4, valid=1, sort=50, created_at=now),
        ]
        for p in projects:
            db.session.add(p)
        db.session.flush()

        print("Seeding solvers...")
        # ============ 求解器 ============
        solvers = [
            Solver(id=1, name='Abaqus Standard', code='ABAQUS_STD', version='2024',
                   cpu_core_min=1, cpu_core_max=256, cpu_core_default=16,
                   memory_min=4, memory_max=1024, memory_default=64, valid=1, sort=10),
            Solver(id=2, name='Abaqus Explicit', code='ABAQUS_EXP', version='2024',
                   cpu_core_min=1, cpu_core_max=512, cpu_core_default=32,
                   memory_min=8, memory_max=2048, memory_default=128, valid=1, sort=20),
            Solver(id=3, name='ANSYS Mechanical', code='ANSYS_MECH', version='2024R1',
                   cpu_core_min=1, cpu_core_max=256, cpu_core_default=16,
                   memory_min=4, memory_max=1024, memory_default=64, valid=1, sort=30),
            Solver(id=4, name='LS-DYNA', code='LSDYNA', version='R14',
                   cpu_core_min=1, cpu_core_max=1024, cpu_core_default=64,
                   memory_min=16, memory_max=4096, memory_default=256, valid=1, sort=40),
        ]
        for s in solvers:
            db.session.add(s)
        db.session.flush()

        print("Seeding status definitions...")
        # ============ 状态定义 ============
        status_defs = [
            StatusDef(id=1, name='待处理', code='PENDING', type='PROCESS',
                     color='bg-slate-100 text-slate-700', valid=1, sort=10),
            StatusDef(id=2, name='排队中', code='QUEUED', type='PROCESS',
                     color='bg-blue-50 text-blue-700', valid=1, sort=20),
            StatusDef(id=3, name='运行中', code='RUNNING', type='PROCESS',
                     color='bg-blue-500 text-white', valid=1, sort=30),
            StatusDef(id=4, name='已完成', code='DONE', type='FINAL',
                     color='bg-green-100 text-green-700', valid=1, sort=40),
            StatusDef(id=5, name='失败', code='FAILED', type='FINAL',
                     color='bg-red-100 text-red-700', valid=1, sort=50),
            StatusDef(id=6, name='警告', code='WARNING', type='FINAL',
                     color='bg-amber-100 text-amber-700', valid=1, sort=60),
        ]
        for s in status_defs:
            db.session.add(s)
        db.session.flush()

        print("Seeding fold types...")
        # ============ 姿态类型 ============
        fold_types = [
            FoldType(id=1, name='折叠 (0°)', code='FOLDED', angle=0, valid=1, sort=10),
            FoldType(id=2, name='半开 (90°)', code='HALF', angle=90, valid=1, sort=20),
            FoldType(id=3, name='展开 (180°)', code='UNFOLDED', angle=180, valid=1, sort=30),
            FoldType(id=4, name='帐篷模式 (45°)', code='TENT', angle=45, valid=1, sort=40),
        ]
        for f in fold_types:
            db.session.add(f)
        db.session.flush()

        print("Seeding automation modules...")
        # ============ 自动化模块 ============
        automation_modules = [
            AutomationModule(id=1, name='请求初始化', code='REQ_INIT', category='Orchestration', version='1.0.2', valid=1, sort=10),
            AutomationModule(id=2, name='任务分发', code='JOB_DIST', category='Orchestration', version='2.1.0', valid=1, sort=20),
            AutomationModule(id=3, name='结果聚合', code='RESULT_AGG', category='Reporting', version='1.5.0', valid=1, sort=30),
            AutomationModule(id=4, name='几何检查', code='GEO_CHECK', category='Pre-processing', version='3.0.1', valid=1, sort=40),
            AutomationModule(id=5, name='自动网格', code='AUTO_MESH', category='Pre-processing', version='4.2.0', valid=1, sort=50),
            AutomationModule(id=6, name='边界条件', code='BC_APPLY', category='Pre-processing', version='2.0.0', valid=1, sort=60),
            AutomationModule(id=7, name='DOE生成', code='DOE_GEN', category='Optimization', version='1.2.0', valid=1, sort=70),
            AutomationModule(id=8, name='参数更新', code='PARAM_UPDATE', category='Solver', version='1.0.0', valid=1, sort=80),
            AutomationModule(id=9, name='FEA求解', code='FEA_SOLVE', category='Solver', version='8.0.0', valid=1, sort=90),
            AutomationModule(id=10, name='结果提取', code='RESULT_EXTRACT', category='Post-processing', version='2.3.0', valid=1, sort=100),
            AutomationModule(id=11, name='临时清理', code='TEMP_CLEAN', category='Maintenance', version='1.0.0', valid=1, sort=110),
        ]
        for m in automation_modules:
            db.session.add(m)
        db.session.flush()

        print("Seeding workflows...")
        # ============ 工作流 ============
        workflows = [
            Workflow(id=1, name='标准申请单流程', code='WF_ORDER_STD', type='ORDER',
                    nodes=[
                        {'nodeId': 1, 'type': 'START', 'name': '提交', 'moduleId': None},
                        {'nodeId': 2, 'type': 'AUTO', 'name': '初始化', 'moduleId': 1},
                        {'nodeId': 3, 'type': 'AUTO', 'name': '任务分发', 'moduleId': 2},
                        {'nodeId': 4, 'type': 'AUTO', 'name': '结果聚合', 'moduleId': 3},
                        {'nodeId': 5, 'type': 'END', 'name': '完成', 'moduleId': None},
                    ],
                    edges=[
                        {'from': 1, 'to': 2}, {'from': 2, 'to': 3}, {'from': 3, 'to': 4}, {'from': 4, 'to': 5}
                    ],
                    valid=1, sort=10),
            Workflow(id=2, name='静力仿真流程', code='WF_SIM_STATIC', type='SIM_TYPE',
                    nodes=[
                        {'nodeId': 1, 'type': 'START', 'name': '开始', 'moduleId': None},
                        {'nodeId': 2, 'type': 'AUTO', 'name': '几何检查', 'moduleId': 4},
                        {'nodeId': 3, 'type': 'AUTO', 'name': '网格划分', 'moduleId': 5},
                        {'nodeId': 4, 'type': 'AUTO', 'name': 'DOE生成', 'moduleId': 7},
                        {'nodeId': 5, 'type': 'END', 'name': '完成', 'moduleId': None},
                    ],
                    edges=[
                        {'from': 1, 'to': 2}, {'from': 2, 'to': 3}, {'from': 3, 'to': 4}, {'from': 4, 'to': 5}
                    ],
                    valid=1, sort=20),
            Workflow(id=3, name='标准轮次流程', code='WF_ROUND_STD', type='ROUND',
                    nodes=[
                        {'nodeId': 1, 'type': 'START', 'name': '开始', 'moduleId': None},
                        {'nodeId': 2, 'type': 'AUTO', 'name': '参数更新', 'moduleId': 8},
                        {'nodeId': 3, 'type': 'AUTO', 'name': '求解', 'moduleId': 9},
                        {'nodeId': 4, 'type': 'AUTO', 'name': '结果提取', 'moduleId': 10},
                        {'nodeId': 5, 'type': 'AUTO', 'name': '清理', 'moduleId': 11},
                        {'nodeId': 6, 'type': 'END', 'name': '完成', 'moduleId': None},
                    ],
                    edges=[
                        {'from': 1, 'to': 2}, {'from': 2, 'to': 3}, {'from': 3, 'to': 4},
                        {'from': 4, 'to': 5}, {'from': 5, 'to': 6}
                    ],
                    valid=1, sort=30),
        ]
        for w in workflows:
            db.session.add(w)
        db.session.flush()

        print("Seeding parameter template sets...")
        # ============ 参数模板集 ============
        param_tpl_sets = [
            ParamTplSet(id=1, sim_type_id=1, name='静力分析-默认模板集', valid=1, sort=10),
            ParamTplSet(id=2, sim_type_id=2, name='模态分析-默认模板集', valid=1, sort=20),
            ParamTplSet(id=3, sim_type_id=3, name='热分析-默认模板集', valid=1, sort=30),
        ]
        for p in param_tpl_sets:
            db.session.add(p)
        db.session.flush()

        # ============ 参数模板明细 ============
        param_tpl_items = [
            ParamTplItem(id=1, tpl_set_id=1, tpl_name='默认模板V1',
                        param_vals={'1': 1.2, '2': 2700, '3': 210, '4': 0.3}, valid=1, sort=10),
            ParamTplItem(id=2, tpl_set_id=1, tpl_name='轻量化模板',
                        param_vals={'1': 0.8, '2': 2700, '3': 70, '4': 0.33}, valid=1, sort=20),
            ParamTplItem(id=3, tpl_set_id=2, tpl_name='模态默认模板',
                        param_vals={'1': 1.5, '2': 7800, '3': 210, '4': 0.3}, valid=1, sort=10),
        ]
        for p in param_tpl_items:
            db.session.add(p)
        db.session.flush()

        print("Seeding condition output sets...")
        # ============ 工况输出集 ============
        cond_out_sets = [
            CondOutSet(id=1, sim_type_id=1, name='静力-默认工况输出集',
                      cond_items=[
                          {'condId': 1, 'vals': {'load': 5000, 'direction': 'Z'}},
                          {'condId': 2, 'vals': {'torque': 1000, 'axis': 'X'}}
                      ],
                      output_ids=[1, 2, 3, 4], valid=1, sort=10),
            CondOutSet(id=2, sim_type_id=3, name='热分析-默认工况输出集',
                      cond_items=[],
                      output_ids=[5], valid=1, sort=20),
        ]
        for c in cond_out_sets:
            db.session.add(c)
        db.session.flush()

        # 更新仿真类型的默认模板集和工况输出集
        SimType.query.filter_by(id=1).update({
            'default_param_tpl_set_id': 1,
            'default_cond_out_set_id': 1,
            'default_solver_id': 1
        })
        SimType.query.filter_by(id=2).update({'default_param_tpl_set_id': 2})
        SimType.query.filter_by(id=3).update({
            'default_param_tpl_set_id': 3,
            'default_cond_out_set_id': 2
        })

        print("Seeding menus...")
        # ============ 菜单 ============
        menus = [
            Menu(id=1, parent_id=0, name='工作台', title_i18n_key='menu.dashboard',
                 icon='dashboard', path='/dashboard', permission_id=1, valid=1, sort=10),
            Menu(id=2, parent_id=0, name='在线提单', title_i18n_key='menu.order',
                 icon='file-plus', path='/order/create', permission_id=2, valid=1, sort=20),
            Menu(id=3, parent_id=0, name='申请单', title_i18n_key='menu.orders',
                 icon='file-list', path='/orders', permission_id=3, valid=1, sort=30),
            Menu(id=4, parent_id=0, name='配置中心', title_i18n_key='menu.config',
                 icon='settings', path='/config', permission_id=5, valid=1, sort=40),
            Menu(id=5, parent_id=4, name='项目配置', title_i18n_key='menu.config.projects',
                 icon='folder', path='/config/projects', permission_id=5, valid=1, sort=10),
            Menu(id=6, parent_id=4, name='仿真类型', title_i18n_key='menu.config.simTypes',
                 icon='cpu', path='/config/sim-types', permission_id=5, valid=1, sort=20),
            Menu(id=7, parent_id=4, name='参数配置', title_i18n_key='menu.config.params',
                 icon='sliders', path='/config/params', permission_id=5, valid=1, sort=30),
            Menu(id=8, parent_id=0, name='系统管理', title_i18n_key='menu.system',
                 icon='shield', path='/system', permission_id=6, valid=1, sort=50),
        ]
        for m in menus:
            db.session.add(m)

        db.session.commit()
        print("Database seeded successfully!")


if __name__ == '__main__':
    seed_database()

