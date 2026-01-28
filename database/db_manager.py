#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StructSim 数据库管理工具
统一的数据库初始化、清理、迁移和数据导入工具

使用方法:
    python database/db_manager.py init          # 创建数据库和表结构
    python database/db_manager.py seed          # 导入初始数据
    python database/db_manager.py clean         # 清理所有数据
    python database/db_manager.py reset         # 重置数据库（清理+导入）
    python database/db_manager.py status        # 查看数据库状态
"""

import sys
import io

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models.config import (
    Project, SimType, ParamDef, OutputDef, Solver, StatusDef,
    FoldType, ModelLevel, CareDevice, SolverResource, Department,
    ParamTplSet, ParamTplItem, CondOutSet, ConditionDef, AutomationModule, Workflow
)
from app.models.auth import User, Role, Permission
from app.models.config_relations import ParamGroup, ParamGroupParamRel, ProjectSimTypeRel
from app.models.order import Order, OrderResult
from app.models.result import SimTypeResult, Round
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# 数据文件路径
INIT_DATA_DIR = SCRIPT_DIR / 'init-data'


def load_json(filename: str) -> dict:
    """加载JSON文件"""
    filepath = INIT_DATA_DIR / filename
    if not filepath.exists():
        print(f"⚠️  文件不存在: {filepath}")
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_timestamp() -> int:
    """获取当前时间戳（秒）"""
    return int(datetime.now().timestamp())


def normalize_timestamp(ts) -> int:
    """标准化时间戳为秒级（处理毫秒级时间戳）"""
    if ts is None:
        return get_timestamp()
    ts = int(ts)
    # 如果时间戳大于 10^12，说明是毫秒级，需要转换为秒级
    if ts > 10**12:
        return ts // 1000
    return ts


# ============ 数据库操作 ============

def init_database():
    """创建数据库表结构"""
    print("\n📋 创建数据库表结构...")
    try:
        db.create_all()
        print("✅ 数据库表结构创建完成")
        return True
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False


def clean_database():
    """清理所有数据（支持 MySQL 和 SQLite）"""
    print("\n🗑️  清理所有数据...")
    try:
        # 检测数据库类型
        db_url = str(db.engine.url)
        is_sqlite = 'sqlite' in db_url

        # 需要清空的表列表
        tables = [
            'order_results', 'rounds', 'sim_type_results', 'orders',
            'param_group_param_rels', 'project_sim_type_rels',
            'sim_type_param_group_rels', 'sim_type_cond_out_group_rels',
            'sim_type_solver_rels', 'cond_out_group_condition_rels',
            'cond_out_group_output_rels',
            'param_tpl_items', 'param_tpl_sets', 'cond_out_sets',
            'param_groups', 'condition_output_groups',
            'param_defs', 'condition_defs', 'output_defs',
            'status_defs', 'solvers', 'solver_resources',
            'care_devices', 'model_levels', 'fold_types',
            'sim_types', 'projects', 'automation_modules', 'workflows',
            'users', 'roles', 'permissions', 'departments', 'menus',
            'user_project_permissions'
        ]

        if is_sqlite:
            # SQLite: 使用 DELETE 并禁用外键约束
            db.session.execute(text('PRAGMA foreign_keys = OFF'))
            for table in tables:
                try:
                    db.session.execute(text(f'DELETE FROM {table}'))
                    print(f"  ✓ 清空表: {table}")
                except Exception:
                    pass
            db.session.execute(text('PRAGMA foreign_keys = ON'))
        else:
            # MySQL: 使用 TRUNCATE
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
            for table in tables:
                try:
                    db.session.execute(text(f'TRUNCATE TABLE {table}'))
                    print(f"  ✓ 清空表: {table}")
                except Exception:
                    pass
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))

        db.session.commit()
        print("✅ 数据清理完成")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ 清理失败: {e}")
        return False


def show_status():
    """显示数据库状态"""
    print("\n📊 数据库状态:")
    try:
        stats = {
            '项目': Project.query.count(),
            '仿真类型': SimType.query.count(),
            '参数定义': ParamDef.query.count(),
            '输出定义': OutputDef.query.count(),
            '状态定义': StatusDef.query.count(),
            '求解器': Solver.query.count(),
            '用户': User.query.count(),
            '角色': Role.query.count(),
            '权限': Permission.query.count(),
            '订单': Order.query.count(),
            '仿真类型结果': SimTypeResult.query.count(),
            '轮次数据': Round.query.count(),
        }
        for name, count in stats.items():
            print(f"  {name}: {count} 条")
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


# ============ 数据导入 ============

def seed_permissions():
    """导入权限数据"""
    print("\n🔐 导入权限数据...")
    data = load_json('users.json')
    if not data:
        return

    count = 0
    for item in data.get('permissions', []):
        if not Permission.query.get(item['permission_id']):
            db.session.add(Permission(
                id=item['permission_id'],
                name=item['permission_name'],
                code=item['permission_code'],
                type='PAGE',
                valid=1,
                sort=item['permission_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 权限: {count} 条 (跳过 {len(data.get('permissions', [])) - count} 条已存在)")


def seed_roles():
    """导入角色数据"""
    print("👔 导入角色数据...")
    data = load_json('users.json')
    if not data:
        return

    count = 0
    for item in data.get('roles', []):
        if not Role.query.get(item['role_id']):
            db.session.add(Role(
                id=item['role_id'],
                name=item['role_name'],
                code=item.get('role_code', item['role_name'].upper()),
                description=item.get('description', ''),
                permission_ids=item.get('permissions', []),
                valid=1,
                sort=item['role_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 角色: {count} 条 (跳过 {len(data.get('roles', [])) - count} 条已存在)")


def seed_departments():
    """导入部门数据"""
    print("🏢 导入部门数据...")
    data = load_json('users.json')
    if not data:
        return

    count = 0
    for item in data.get('departments', []):
        if not Department.query.get(item['department_id']):
            db.session.add(Department(
                id=item['department_id'],
                name=item['department_name'],
                code=item.get('department_code', item['department_name'].upper()),
                parent_id=item.get('parent_id', 0),
                valid=1,
                sort=item['department_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 部门: {count} 条 (跳过 {len(data.get('departments', [])) - count} 条已存在)")


def seed_users():
    """导入测试用户"""
    print("👥 导入测试用户...")
    data = load_json('users.json')
    if not data:
        return

    ts = get_timestamp()

    # 构建用户角色映射
    user_role_map = {}
    for ur in data.get('user_roles', []):
        uid = ur['user_id']
        if uid not in user_role_map:
            user_role_map[uid] = []
        user_role_map[uid].append(ur['role_id'])

    # 构建部门ID到名称的映射
    dept_map = {d['department_id']: d['department_name'] for d in data.get('departments', [])}

    count = 0
    for item in data.get('users', []):
        user_id = item['user_id']
        if not User.query.get(user_id):
            dept_id = item.get('department', 1)
            dept_name = dept_map.get(dept_id, '研发部')
            db.session.add(User(
                id=user_id,
                username=item['user_name'],
                email=item['user_email'],
                name=item.get('real_name', item['user_name']),
                role_ids=user_role_map.get(user_id, []),
                department=dept_name,
                valid=1,
                preferences={'lang': 1, 'theme': 1},
                created_at=ts
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 用户: {count} 条 (跳过 {len(data.get('users', [])) - count} 条已存在)")

    # 打印用户信息
    print("\n  测试用户账号:")
    for item in data.get('users', [])[:5]:
        print(f"    - {item['user_email']:30} ({item.get('real_name', item['user_name'])})")
    if len(data.get('users', [])) > 5:
        print(f"    ... 共 {len(data.get('users', []))} 个用户")


def seed_base_config():
    """导入基础配置数据"""
    print("\n📦 导入基础配置...")
    data = load_json('base_config.json')
    if not data:
        print("⚠️  base_config.json 不存在，跳过")
        return

    ts = get_timestamp()

    # 项目
    count = 0
    for item in data.get('projects', []):
        pid = int(item['project_id'])
        if not Project.query.get(pid):
            db.session.add(Project(
                id=pid,
                name=item['project_name'],
                code=f"PRJ_{item['project_id']}",
                valid=1, sort=100, created_at=ts, updated_at=ts
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 项目: {count} 条")

    # 仿真类型
    count = 0
    for item in data.get('sim_types', []):
        if not SimType.query.get(item['sim_type_id']):
            db.session.add(SimType(
                id=item['sim_type_id'],
                name=item['sim_type_name'],
                code=item['sim_type_name'].upper(),
                valid=1, sort=item['sim_type_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 仿真类型: {count} 条")

    # 模型层级
    count = 0
    for item in data.get('model_levels', []):
        if not ModelLevel.query.get(item['model_level_id']):
            db.session.add(ModelLevel(
                id=item['model_level_id'],
                name=item['model_level_name'],
                code=item['model_level_name'].upper(),
                valid=1, sort=item['model_level_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 模型层级: {count} 条")

    # 折叠状态
    count = 0
    for item in data.get('fold_types', []):
        if not FoldType.query.get(item['fold_type_id']):
            db.session.add(FoldType(
                id=item['fold_type_id'],
                name=item['fold_type_name'],
                code=item['fold_type_name'].upper(),
                valid=1, sort=item['fold_type_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 折叠状态: {count} 条")

    # 求解器
    count = 0
    for item in data.get('solvers', []):
        if not Solver.query.get(item['solver_id']):
            db.session.add(Solver(
                id=item['solver_id'],
                name=item['solver_name'],
                code=item['solver_name'].upper().replace(' ', '_'),
                valid=1, sort=item['solver_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 求解器: {count} 条")

    # 求解器资源
    count = 0
    for item in data.get('solver_resources', []):
        if not SolverResource.query.get(item['resource_id']):
            db.session.add(SolverResource(
                id=item['resource_id'],
                name=item['resource_name'],
                cpu_cores=item.get('cpu_cores', 16),
                memory_gb=item.get('memory_gb', 64),
                valid=1
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 求解器资源: {count} 条")

    # 状态定义（包含icon字段，使用Lucide图标名称）
    count = 0
    for item in data.get('status_defs', []):
        if not StatusDef.query.get(item['status_id']):
            db.session.add(StatusDef(
                id=item['status_id'],
                name=item['status_name'],
                code=item.get('status_code', item['status_name'].upper()),
                type=item.get('status_type', 'PROCESS'),
                color=item.get('color_tag', '#808080'),
                icon=item.get('icon', ''),
                valid=1,
                sort=item.get('sort', item['status_id'] * 10)
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 状态定义: {count} 条")

    # 关注设备
    count = 0
    for item in data.get('care_devices', []):
        if not CareDevice.query.get(item['device_id']):
            db.session.add(CareDevice(
                id=item['device_id'],
                name=item['device_name'],
                code=item.get('device_code', item['device_name'].upper()),
                valid=1
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 关注设备: {count} 条")

    # 参数定义
    count = 0
    for item in data.get('param_defs', []):
        if not ParamDef.query.get(item['opt_param_id']):
            db.session.add(ParamDef(
                id=item['opt_param_id'],
                name=item.get('param_desc', item['param_name']),
                key=item['param_name'],
                val_type=1,
                unit=item.get('param_unit', ''),
                min_val=item.get('param_default_min'),
                max_val=item.get('param_default_max'),
                default_val=str(item.get('param_default_init', '')),
                precision=6, required=1, valid=1,
                sort=item['opt_param_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 参数定义: {count} 条")

    # 输出定义
    count = 0
    for item in data.get('output_defs', []):
        if not OutputDef.query.get(item['resp_param_id']):
            db.session.add(OutputDef(
                id=item['resp_param_id'],
                name=item.get('description', item['output_type']),
                code=item['output_type'],
                val_type=1, unit='', valid=1,
                sort=item['resp_param_id'] * 10
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 输出定义: {count} 条")
    print("✅ 基础配置导入完成")


def seed_orders_and_results():
    """导入订单和仿真结果模拟数据"""
    print("\n📊 导入订单和仿真结果模拟数据...")
    data = load_json('orders_mock.json')
    if not data:
        print("⚠️  orders_mock.json 不存在，跳过")
        return

    ts = get_timestamp()

    # 导入订单
    count = 0
    for item in data.get('orders', []):
        if not Order.query.get(item['id']):
            db.session.add(Order(
                id=item['id'],
                order_no=item['order_no'],
                project_id=item['project_id'],
                origin_file_type=item.get('origin_file_type', 1),
                origin_file_name=item.get('origin_file_name'),
                origin_file_path=item.get('origin_file_path'),
                fold_type_id=item.get('fold_type_id'),
                participant_uids=item.get('participant_uids', []),
                remark=item.get('remark', ''),
                sim_type_ids=item.get('sim_type_ids', []),
                status=item.get('status', 0),
                progress=item.get('progress', 0),
                created_by=item.get('created_by', 1),
                created_at=ts,
                updated_at=ts
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 订单: {count} 条")

    # 导入仿真类型结果
    count = 0
    for item in data.get('sim_type_results', []):
        if not SimTypeResult.query.get(item['id']):
            db.session.add(SimTypeResult(
                id=item['id'],
                order_id=item['order_id'],
                sim_type_id=item['sim_type_id'],
                status=item.get('status', 0),
                progress=item.get('progress', 0),
                total_rounds=item.get('total_rounds', 0),
                completed_rounds=item.get('completed_rounds', 0),
                failed_rounds=item.get('failed_rounds', 0),
                best_exists=item.get('best_exists', 0),
                best_round_index=item.get('best_round_index'),
                created_at=ts,
                updated_at=ts
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 仿真类型结果: {count} 条")

    # 为已完成的仿真类型结果生成轮次数据
    seed_rounds_data()
    print("✅ 订单和仿真结果导入完成")


def seed_rounds_data():
    """生成轮次模拟数据（优化批量插入，不同仿真类型使用不同参数/输出组合）"""
    import random
    print("  📈 生成轮次数据...")

    ts = get_timestamp()
    sim_type_results = SimTypeResult.query.filter(SimTypeResult.total_rounds > 0).all()

    # 不同仿真类型的参数配置（8个参数/仿真类型）
    SIM_TYPE_PARAMS = {
        1: {  # 跌落仿真
            "1": lambda: round(random.uniform(0, 90), 2),      # x_deg
            "2": lambda: round(random.uniform(0, 360), 2),     # y_deg
            "3": lambda: round(random.uniform(0, 90), 2),      # z_deg
            "4": lambda: round(random.uniform(0.5, 2.0), 2),   # drop_height
            "5": lambda: round(random.uniform(0, 5), 2),       # surface_friction
            "6": lambda: round(random.uniform(0, 10), 2),      # init_velocity
            "14": lambda: round(random.uniform(50, 300), 1),   # youngs_modulus
            "15": lambda: round(random.uniform(0.2, 0.5), 3),  # poisson_ratio
        },
        2: {  # 落球仿真
            "7": lambda: round(random.uniform(0.1, 1.0), 3),   # ball_mass
            "8": lambda: round(random.uniform(10, 50), 1),     # ball_radius
            "9": lambda: round(random.uniform(-100, 100), 1),  # impact_x
            "10": lambda: round(random.uniform(-100, 100), 1), # impact_y
            "4": lambda: round(random.uniform(0.5, 2.0), 2),   # drop_height
            "6": lambda: round(random.uniform(0, 10), 2),      # init_velocity
            "14": lambda: round(random.uniform(50, 300), 1),   # youngs_modulus
            "16": lambda: round(random.uniform(7000, 8000), 0),# density
        },
        3: {  # 振动仿真
            "11": lambda: round(random.uniform(10, 2000), 1),  # frequency
            "12": lambda: round(random.uniform(0.1, 10), 2),   # amplitude
            "13": lambda: round(random.uniform(1, 60), 1),     # duration
            "1": lambda: round(random.uniform(0, 90), 2),      # x_deg
            "2": lambda: round(random.uniform(0, 360), 2),     # y_deg
            "3": lambda: round(random.uniform(0, 90), 2),      # z_deg
            "19": lambda: round(random.uniform(0.01, 0.1), 3), # damping_ratio
            "20": lambda: round(random.uniform(1, 10), 1),     # cycles
        },
        4: {  # 冲击仿真
            "4": lambda: round(random.uniform(0.5, 2.0), 2),   # drop_height
            "6": lambda: round(random.uniform(0, 10), 2),      # init_velocity
            "14": lambda: round(random.uniform(50, 300), 1),   # youngs_modulus
            "1": lambda: round(random.uniform(0, 90), 2),      # x_deg
            "2": lambda: round(random.uniform(0, 360), 2),     # y_deg
            "13": lambda: round(random.uniform(0.001, 0.1), 4),# duration
            "21": lambda: round(random.uniform(100, 1000), 0), # impact_force
            "22": lambda: round(random.uniform(0.1, 1.0), 2),  # contact_area
        },
        5: {  # 热分析
            "17": lambda: round(random.uniform(-40, 85), 1),   # ambient_temp
            "18": lambda: round(random.uniform(0, 10000), 1),  # heat_flux
            "13": lambda: round(random.uniform(1, 60), 1),     # duration
            "23": lambda: round(random.uniform(0.1, 50), 2),   # thermal_conductivity
            "24": lambda: round(random.uniform(100, 1000), 0), # specific_heat
            "25": lambda: round(random.uniform(0.1, 1.0), 2),  # emissivity
            "26": lambda: round(random.uniform(1, 100), 1),    # convection_coeff
            "27": lambda: round(random.uniform(20, 100), 1),   # initial_temp
        },
    }

    # 不同仿真类型的输出配置（6个输出/仿真类型）
    SIM_TYPE_OUTPUTS = {
        1: {  # 跌落仿真 - 位移、应力、应变
            "1": lambda: round(random.uniform(-5, 5), 4),      # LEP1
            "2": lambda: round(random.uniform(-5, 5), 4),      # LEP2
            "3": lambda: round(random.uniform(-2, 2), 4),      # LEP3
            "9": lambda: round(random.uniform(100, 800), 2),   # MISES
            "7": lambda: round(random.uniform(50, 500), 2),    # S11
            "12": lambda: round(random.uniform(0, 0.05), 5),   # PEEQ
        },
        2: {  # 落球仿真 - 反力、应力、能量
            "4": lambda: round(random.uniform(0, 1000), 2),    # RF1
            "5": lambda: round(random.uniform(0, 1000), 2),    # RF2
            "6": lambda: round(random.uniform(0, 500), 2),     # RF3
            "7": lambda: round(random.uniform(50, 500), 2),    # S11
            "9": lambda: round(random.uniform(100, 800), 2),   # MISES
            "13": lambda: round(random.uniform(0, 100), 2),    # ALLKE
        },
        3: {  # 振动仿真 - 位移、主应力、加速度
            "1": lambda: round(random.uniform(-10, 10), 4),    # LEP1
            "2": lambda: round(random.uniform(-10, 10), 4),    # LEP2
            "7": lambda: round(random.uniform(50, 500), 2),    # S11
            "8": lambda: round(random.uniform(30, 400), 2),    # S22
            "14": lambda: round(random.uniform(0, 1000), 2),   # A1 (acceleration)
            "15": lambda: round(random.uniform(0, 50), 2),     # natural_freq
        },
        4: {  # 冲击仿真 - 反力、应力、能量
            "4": lambda: round(random.uniform(0, 2000), 2),    # RF1
            "5": lambda: round(random.uniform(0, 2000), 2),    # RF2
            "9": lambda: round(random.uniform(200, 1200), 2),  # MISES
            "12": lambda: round(random.uniform(0, 0.1), 5),    # PEEQ
            "13": lambda: round(random.uniform(0, 500), 2),    # ALLKE
            "16": lambda: round(random.uniform(0, 1000), 2),   # ALLIE
        },
        5: {  # 热分析 - 温度、热流、梯度
            "10": lambda: round(random.uniform(-40, 150), 2),  # TEMP
            "11": lambda: round(random.uniform(0, 5000), 2),   # HFL
            "17": lambda: round(random.uniform(0, 100), 2),    # NT11 (nodal temp)
            "18": lambda: round(random.uniform(0, 500), 2),    # RFL (reaction flux)
            "19": lambda: round(random.uniform(0, 50), 3),     # TEMP_GRAD_X
            "20": lambda: round(random.uniform(0, 50), 3),     # TEMP_GRAD_Y
        },
    }

    # 默认配置（兜底）- 8个参数
    DEFAULT_PARAMS = {
        "1": lambda: round(random.uniform(0, 90), 2),
        "2": lambda: round(random.uniform(0, 360), 2),
        "3": lambda: round(random.uniform(0, 90), 2),
        "4": lambda: round(random.uniform(0.5, 2.0), 2),
        "5": lambda: round(random.uniform(0, 5), 2),
        "6": lambda: round(random.uniform(0, 10), 2),
        "14": lambda: round(random.uniform(50, 300), 1),
        "15": lambda: round(random.uniform(0.2, 0.5), 3),
    }
    # 默认配置（兜底）- 6个输出
    DEFAULT_OUTPUTS = {
        "1": lambda: round(random.uniform(-5, 5), 4),
        "2": lambda: round(random.uniform(-5, 5), 4),
        "3": lambda: round(random.uniform(-2, 2), 4),
        "9": lambda: round(random.uniform(100, 800), 2),
        "7": lambda: round(random.uniform(50, 500), 2),
        "12": lambda: round(random.uniform(0, 0.05), 5),
    }

    total_rounds = 0
    batch_size = 500

    for result in sim_type_results:
        existing = Round.query.filter_by(sim_type_result_id=result.id).count()
        if existing > 0:
            print(f"    跳过 SimTypeResult {result.id}（已有 {existing} 条）")
            continue

        sim_type_id = result.sim_type_id
        param_config = SIM_TYPE_PARAMS.get(sim_type_id, DEFAULT_PARAMS)
        output_config = SIM_TYPE_OUTPUTS.get(sim_type_id, DEFAULT_OUTPUTS)

        print(f"    生成 SimTypeResult {result.id} (sim_type={sim_type_id}): {result.total_rounds} 轮次...")
        batch = []

        for i in range(1, result.total_rounds + 1):
            # 根据仿真类型生成对应的参数值
            params = {k: fn() for k, fn in param_config.items()}

            # 根据仿真类型生成对应的输出结果
            outputs = {k: fn() for k, fn in output_config.items()}

            # 确定状态
            if i <= result.completed_rounds:
                status = 2  # 已完成
            elif i <= result.completed_rounds + result.failed_rounds:
                status = 3  # 失败
            else:
                status = 1  # 运行中

            batch.append(Round(
                sim_type_result_id=result.id,
                order_id=result.order_id,
                sim_type_id=result.sim_type_id,
                round_index=i,
                params=params,
                outputs=outputs if status == 2 else None,
                status=status,
                started_at=ts - (result.total_rounds - i) * 60,
                finished_at=ts - (result.total_rounds - i) * 60 + 30 if status == 2 else None,
                created_at=ts,
                updated_at=ts
            ))
            total_rounds += 1

            if len(batch) >= batch_size:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                batch = []

        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()

    print(f"  ✓ 轮次数据: {total_rounds} 条")


def seed_all():
    """导入所有数据"""
    seed_permissions()
    seed_roles()
    seed_departments()
    seed_users()
    seed_base_config()
    seed_orders_and_results()


# ============ 主函数 ============

def main():
    parser = argparse.ArgumentParser(
        description='StructSim 数据库管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python database/db_manager.py init          创建数据库表结构
  python database/db_manager.py seed          导入初始数据
  python database/db_manager.py clean         清理所有数据
  python database/db_manager.py reset         重置数据库（清理+创建+导入）
  python database/db_manager.py status        查看数据库状态
        """
    )
    parser.add_argument('command', choices=['init', 'seed', 'clean', 'reset', 'status'],
                        help='要执行的命令')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制执行，不提示确认')
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        print("\n" + "=" * 60)
        print("🚀 StructSim 数据库管理工具")
        print("=" * 60)

        try:
            if args.command == 'init':
                init_database()

            elif args.command == 'seed':
                seed_all()

            elif args.command == 'clean':
                if not args.force:
                    confirm = input("\n⚠️  确定要清理所有数据吗？(y/N): ")
                    if confirm.lower() != 'y':
                        print("已取消")
                        return
                clean_database()

            elif args.command == 'reset':
                if not args.force:
                    confirm = input("\n⚠️  确定要重置数据库吗？这将删除所有数据！(y/N): ")
                    if confirm.lower() != 'y':
                        print("已取消")
                        return
                clean_database()
                init_database()
                seed_all()

            elif args.command == 'status':
                show_status()

            print("\n" + "=" * 60)
            print("✅ 操作完成！")
            print("=" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ 操作失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

