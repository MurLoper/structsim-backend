#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StructSim 数据库管理工具
统一的数据库初始化、清理、迁移和数据导入工具

使用方法:
    python database/db_manager.py init          # 创建数据库和表结构
    python database/db_manager.py seed          # 导入初始数据（从 init-data）
    python database/db_manager.py sync          # 从导出数据完整同步（exported-data）
    python database/db_manager.py export        # 导出当前数据库到 exported-data
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
from app.models.auth import User, Role, Permission, Menu
from app.models.config_relations import ParamGroup, ParamGroupParamRel, ProjectSimTypeRel, WorkingCondition, FoldTypeSimTypeRel
from app.models.order import Order, OrderResult
from app.models.result import SimTypeResult, Round
from werkzeug.security import generate_password_hash
from sqlalchemy import text, inspect

# 数据文件路径
INIT_DATA_DIR = SCRIPT_DIR / 'init-data'
EXPORTED_DATA_DIR = SCRIPT_DIR / 'exported-data'


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

def get_existing_columns(table_name: str) -> set:
    """获取表的现有字段"""
    try:
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        return {col['name'] for col in columns}
    except Exception:
        return set()


def ensure_table_columns():
    """确保表结构完整（幂等操作）"""
    print("\n🔧 检查并更新表结构...")

    db_url = str(db.engine.url)
    is_mysql = 'mysql' in db_url

    # 定义需要检查的表和字段
    # 格式: {表名: [(字段名, MySQL定义, SQLite定义), ...]}
    schema_updates = {
        'menus': [
            ('component', 'VARCHAR(200) COMMENT "前端组件路径"', 'VARCHAR(200)'),
            ('menu_type', 'VARCHAR(20) DEFAULT "MENU" COMMENT "菜单类型"', 'VARCHAR(20) DEFAULT "MENU"'),
            ('hidden', 'SMALLINT DEFAULT 0 COMMENT "是否隐藏"', 'SMALLINT DEFAULT 0'),
            ('permission_code', 'VARCHAR(50) COMMENT "所需权限编码"', 'VARCHAR(50)'),
        ],
        'users': [
            ('password_hash', 'VARCHAR(256) COMMENT "密码哈希"', 'VARCHAR(256)'),
        ],
    }

    updated = 0
    for table, columns in schema_updates.items():
        existing = get_existing_columns(table)
        if not existing:
            print(f"  ⚠️  表 {table} 不存在，将在 init 时创建")
            continue

        for col_name, mysql_def, sqlite_def in columns:
            if col_name in existing:
                continue

            definition = mysql_def if is_mysql else sqlite_def
            try:
                if is_mysql:
                    sql = f"ALTER TABLE `{table}` ADD COLUMN `{col_name}` {definition}"
                else:
                    sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {definition}"
                db.session.execute(text(sql))
                db.session.commit()
                print(f"  ✓ {table}.{col_name} 已添加")
                updated += 1
            except Exception as e:
                print(f"  ⚠️  添加 {table}.{col_name} 失败: {e}")

    if updated == 0:
        print("  ✓ 表结构已是最新")
    else:
        print(f"  ✓ 更新了 {updated} 个字段")


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
            db.session.commit()
        else:
            # MySQL: 使用原始连接执行 TRUNCATE（DDL语句）
            # 先提交当前事务，避免冲突
            db.session.commit()
            with db.engine.connect() as conn:
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
                conn.commit()
                for table in tables:
                    try:
                        conn.execute(text(f'TRUNCATE TABLE `{table}`'))
                        conn.commit()
                        print(f"  ✓ 清空表: {table}")
                    except Exception as e:
                        # 表可能不存在，忽略错误
                        pass
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
                conn.commit()

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
    updated = 0
    for item in data.get('permissions', []):
        existing = db.session.get(Permission, item['permission_id'])
        if not existing:
            db.session.add(Permission(
                id=item['permission_id'],
                name=item['permission_name'],
                code=item['permission_code'],
                type='PAGE',
                valid=1,
                sort=item['permission_id'] * 10
            ))
            count += 1
        else:
            # 更新已存在的权限（确保code正确）
            if existing.code != item['permission_code']:
                existing.code = item['permission_code']
                existing.name = item['permission_name']
                updated += 1
    db.session.commit()
    msg = f"  ✓ 权限: 新增 {count} 条"
    if updated > 0:
        msg += f", 更新 {updated} 条"
    print(msg)


def seed_roles():
    """导入角色数据"""
    print("👔 导入角色数据...")
    data = load_json('users.json')
    if not data:
        return

    count = 0
    for item in data.get('roles', []):
        if not db.session.get(Role, item['role_id']):
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
        if not db.session.get(Department, item['department_id']):
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
    # 默认密码（所有测试用户统一密码）
    default_password = 'Sim@2024'

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
        if not db.session.get(User, user_id):
            dept_id = item.get('department', 1)
            dept_name = dept_map.get(dept_id, '研发部')
            user = User(
                id=user_id,
                username=item['user_name'],
                email=item['user_email'],
                name=item.get('real_name', item['user_name']),
                role_ids=user_role_map.get(user_id, []),
                department=dept_name,
                valid=1,
                preferences={'lang': 1, 'theme': 1},
                created_at=ts
            )
            # 设置密码
            user.set_password(default_password)
            db.session.add(user)
            count += 1
    db.session.commit()
    print(f"  ✓ 用户: {count} 条 (跳过 {len(data.get('users', [])) - count} 条已存在)")

    # 打印用户信息
    print(f"\n  测试用户账号 (默认密码: {default_password}):")
    for item in data.get('users', [])[:5]:
        print(f"    - {item['user_email']:30} ({item.get('real_name', item['user_name'])})")
    if len(data.get('users', [])) > 5:
        print(f"    ... 共 {len(data.get('users', []))} 个用户")


def seed_menus():
    """导入菜单数据"""
    print("\n📋 导入菜单数据...")

    menus_json = load_json('menus.json')
    menus_data = menus_json.get('menus', []) if isinstance(menus_json, dict) else []
    if not menus_data:
        print("⚠️  menus.json 不存在或为空，跳过")
        return

    count = 0
    for item in menus_data:
        if not db.session.get(Menu, item['id']):
            db.session.add(Menu(
                id=item['id'],
                parent_id=item['parent_id'],
                name=item['name'],
                title_i18n_key=item['title_i18n_key'],
                icon=item['icon'],
                path=item['path'],
                component=item['component'],
                menu_type=item['menu_type'],
                hidden=item['hidden'],
                permission_code=item['permission_code'],
                valid=1,
                sort=item['sort']
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 菜单: {count} 条 (跳过 {len(menus_data) - count} 条已存在)")


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
        if not db.session.get(Project, pid):
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
        if not db.session.get(SimType, item['sim_type_id']):
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
        if not db.session.get(ModelLevel, item['model_level_id']):
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
        fold_id = item['fold_type_id']
        existing = db.session.get(FoldType, fold_id)
        if existing:
            continue
        # 检查 code 是否已存在（用原始名称，不转大写）
        code = item['fold_type_name']
        exists_by_code = FoldType.query.filter_by(code=code).first()
        if exists_by_code:
            continue
        db.session.add(FoldType(
            id=fold_id,
            name=item['fold_type_name'],
            code=code,
            valid=1, sort=fold_id * 10
        ))
        count += 1
        db.session.flush()  # 立即写入避免批量冲突
    db.session.commit()
    print(f"  ✓ 折叠状态: {count} 条")

    # 求解器
    count = 0
    for item in data.get('solvers', []):
        solver_id = item['solver_id']
        existing = db.session.get(Solver, solver_id)
        if existing:
            continue
        code = item['solver_name']
        exists_by_code = Solver.query.filter_by(code=code).first()
        if exists_by_code:
            continue
        db.session.add(Solver(
            id=solver_id,
            name=item['solver_name'],
            code=code,
            valid=1, sort=solver_id * 10
        ))
        count += 1
        db.session.flush()
    db.session.commit()
    print(f"  ✓ 求解器: {count} 条")

    # 求解器资源
    count = 0
    for item in data.get('solver_resources', []):
        if not db.session.get(SolverResource, item['resource_id']):
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
        if not db.session.get(StatusDef, item['status_id']):
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
        if not db.session.get(CareDevice, item['device_id']):
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
        if not db.session.get(ParamDef, item['opt_param_id']):
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
        if not db.session.get(OutputDef, item['resp_param_id']):
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

    # 自动化模块
    count = 0
    for item in data.get('automation_modules', []):
        if not db.session.get(AutomationModule, item['module_id']):
            db.session.add(AutomationModule(
                id=item['module_id'],
                name=item['module_name'],
                code=item['module_code'],
                category=item.get('category', 'GENERAL'),
                timeout_sec=item.get('timeout_sec', 7200),
                valid=1
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 自动化模块: {count} 条")

    # 工作流
    count = 0
    for item in data.get('workflows', []):
        if not db.session.get(Workflow, item['workflow_id']):
            db.session.add(Workflow(
                id=item['workflow_id'],
                name=item['workflow_name'],
                code=item['workflow_code'],
                type=item.get('workflow_type', 'ROUND'),
                nodes=item.get('nodes', []),
                edges=item.get('edges', []),
                valid=1
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 工作流: {count} 条")

    # 姿态-仿真类型关联
    count = 0
    for item in data.get('fold_type_sim_type_rels', []):
        existing = FoldTypeSimTypeRel.query.filter_by(
            fold_type_id=item['fold_type_id'],
            sim_type_id=item['sim_type_id']
        ).first()
        if not existing:
            db.session.add(FoldTypeSimTypeRel(
                fold_type_id=item['fold_type_id'],
                sim_type_id=item['sim_type_id'],
                is_default=item.get('is_default', 0),
                sort=item.get('sort', 100)
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 姿态-仿真类型关联: {count} 条")

    # 工况配置
    count = 0
    for item in data.get('working_conditions', []):
        if not db.session.get(WorkingCondition, item['id']):
            db.session.add(WorkingCondition(
                id=item['id'],
                name=item['name'],
                code=item['code'],
                fold_type_id=item['fold_type_id'],
                sim_type_id=item['sim_type_id'],
                sort=item.get('sort', 100),
                valid=1
            ))
            count += 1
    db.session.commit()
    print(f"  ✓ 工况配置: {count} 条")

    print("✅ 基础配置导入完成")


def seed_orders_and_results():
    """导入订单和仿真结果模拟数据"""
    print("\n📊 导入订单和仿真结果模拟数据...")
    data = load_json('orders_mock.json')
    if not data:
        print("⚠️  orders_mock.json 不存在，跳过")
        return

    ts = get_timestamp()

    # 加载用户数据，建立 created_by 映射（mock数据中1,2,3映射到实际用户ID）
    users_data = load_json('users.json')
    user_ids = [u['user_id'] for u in users_data.get('users', [])]
    default_user_id = user_ids[0] if user_ids else 10001

    def map_user_id(mock_id):
        """将mock数据中的小ID映射到实际用户ID"""
        if mock_id is None:
            return default_user_id
        # mock_id 1,2,3... 映射到 user_ids 列表中对应位置
        idx = mock_id - 1
        if 0 <= idx < len(user_ids):
            return user_ids[idx]
        return default_user_id

    # 导入订单（使用 no_autoflush 避免查询时触发 flush）
    count = 0
    with db.session.no_autoflush:
        for item in data.get('orders', []):
            if not db.session.get(Order, item['id']):
                # fold_type_id 为 0 时设为 None，避免外键约束失败
                fold_type_id = item.get('fold_type_id')
                if fold_type_id == 0:
                    fold_type_id = None
                db.session.add(Order(
                    id=item['id'],
                    order_no=item['order_no'],
                    project_id=item['project_id'],
                    origin_file_type=item.get('origin_file_type', 1),
                    origin_file_name=item.get('origin_file_name'),
                    origin_file_path=item.get('origin_file_path'),
                    fold_type_id=fold_type_id,
                    participant_uids=[map_user_id(uid) for uid in item.get('participant_uids', [])],
                    remark=item.get('remark', ''),
                    sim_type_ids=item.get('sim_type_ids', []),
                    status=item.get('status', 0),
                    progress=item.get('progress', 0),
                    created_by=map_user_id(item.get('created_by')),
                    created_at=ts,
                    updated_at=ts
                ))
                count += 1
    db.session.commit()
    print(f"  ✓ 订单: {count} 条")

    # 导入仿真类型结果
    count = 0
    with db.session.no_autoflush:
        for item in data.get('sim_type_results', []):
            if not db.session.get(SimTypeResult, item['id']):
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

    # 错误信息模板
    ERROR_MESSAGES = [
        "求解器异常退出，错误码: SOLVER_CRASH_001",
        "网格质量检查失败: 存在负体积单元",
        "材料参数超出有效范围",
        "接触算法收敛失败，迭代次数超限",
        "内存不足，无法完成计算",
        "模型文件损坏或格式不正确",
        "边界条件设置冲突",
        "时间步长过大导致数值不稳定",
        "节点位移超出允许范围",
        "应力值超过材料极限",
        "热传导计算发散",
        "动态分析时间积分失败",
        "接触穿透检测异常",
        "单元刚度矩阵奇异",
        "载荷施加顺序错误",
    ]

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

            # 确定状态和流程节点
            error_msg = None
            stuck_module_id = None

            if i <= result.completed_rounds:
                status = 2  # 已完成
                flow_cur_node_id = 7  # 最后一个节点
                flow_node_progress = {"node_1": 100, "node_2": 100, "node_3": 100, "node_4": 100, "node_5": 100, "node_6": 100, "node_7": 100}
            elif i <= result.completed_rounds + result.failed_rounds:
                status = 3  # 失败
                # 随机在某个节点失败
                failed_node = random.randint(3, 6)
                flow_cur_node_id = failed_node
                flow_node_progress = {f"node_{j}": 100 if j < failed_node else (random.randint(10, 90) if j == failed_node else 0) for j in range(1, 8)}
                # 添加错误信息
                error_msg = random.choice(ERROR_MESSAGES)
                stuck_module_id = failed_node
            else:
                status = 1  # 运行中
                # 随机在某个节点运行中
                running_node = random.randint(1, 6)
                flow_cur_node_id = running_node
                flow_node_progress = {f"node_{j}": 100 if j < running_node else (random.randint(10, 90) if j == running_node else 0) for j in range(1, 8)}

            batch.append(Round(
                sim_type_result_id=result.id,
                order_id=result.order_id,
                sim_type_id=result.sim_type_id,
                round_index=i,
                params=params,
                outputs=outputs if status == 2 else None,
                status=status,
                flow_cur_node_id=flow_cur_node_id,
                flow_node_progress=flow_node_progress,
                stuck_module_id=stuck_module_id,
                error_msg=error_msg,
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
    # 先确保表结构完整
    ensure_table_columns()

    seed_permissions()
    seed_roles()
    seed_departments()
    seed_users()
    seed_menus()
    seed_base_config()
    seed_orders_and_results()


# ============ 数据同步（从导出文件） ============

def load_exported_data() -> dict:
    """加载导出的完整数据"""
    filepath = EXPORTED_DATA_DIR / 'full_data.json'
    if not filepath.exists():
        print(f"⚠️  导出数据文件不存在: {filepath}")
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def sync_table_data(table_name: str, data: list, model_class, id_field: str = 'id'):
    """同步单个表的数据"""
    if not data:
        return 0

    count = 0
    for item in data:
        record_id = item.get(id_field)
        if record_id is None:
            continue

        existing = db.session.get(model_class, record_id)
        if existing:
            # 更新现有记录
            for key, value in item.items():
                if hasattr(existing, key) and key != id_field:
                    setattr(existing, key, value)
        else:
            # 创建新记录
            try:
                obj = model_class(**item)
                db.session.add(obj)
                count += 1
            except Exception as e:
                print(f"    ⚠️  创建记录失败 {table_name}[{record_id}]: {e}")

    db.session.commit()
    return count


def sync_from_exported():
    """从导出数据完整同步到数据库"""
    print("\n📥 从导出数据同步...")

    data = load_exported_data()
    if not data:
        print("❌ 无法加载导出数据")
        return False

    # 表名到模型类的映射
    TABLE_MODEL_MAP = {
        'departments': Department,
        'permissions': Permission,
        'roles': Role,
        'menus': Menu,
        'projects': Project,
        'sim_types': SimType,
        'model_levels': ModelLevel,
        'fold_types': FoldType,
        'solvers': Solver,
        'solver_resources': SolverResource,
        'status_defs': StatusDef,
        'care_devices': CareDevice,
        'param_defs': ParamDef,
        'output_defs': OutputDef,
        'condition_defs': ConditionDef,
        'automation_modules': AutomationModule,
        'workflows': Workflow,
        'users': User,
    }

    # 按顺序同步（考虑外键依赖）
    sync_order = [
        'departments', 'permissions', 'roles', 'menus',
        'projects', 'sim_types', 'model_levels', 'fold_types',
        'solvers', 'solver_resources', 'status_defs', 'care_devices',
        'param_defs', 'output_defs', 'condition_defs',
        'automation_modules', 'workflows', 'users',
    ]

    total = 0
    for table in sync_order:
        if table not in data:
            continue
        model = TABLE_MODEL_MAP.get(table)
        if not model:
            continue

        count = sync_table_data(table, data[table], model)
        if count > 0:
            print(f"  ✓ {table}: 新增 {count} 条")
        total += count

    print(f"\n✅ 同步完成，共新增 {total} 条记录")
    return True


def export_database():
    """导出当前数据库到 JSON 文件"""
    print("\n📤 导出数据库...")

    EXPORTED_DATA_DIR.mkdir(exist_ok=True)

    # 获取所有表数据
    all_data = {}
    tables_info = [
        ('departments', Department),
        ('permissions', Permission),
        ('roles', Role),
        ('menus', Menu),
        ('projects', Project),
        ('sim_types', SimType),
        ('model_levels', ModelLevel),
        ('fold_types', FoldType),
        ('solvers', Solver),
        ('solver_resources', SolverResource),
        ('status_defs', StatusDef),
        ('care_devices', CareDevice),
        ('param_defs', ParamDef),
        ('output_defs', OutputDef),
        ('condition_defs', ConditionDef),
        ('automation_modules', AutomationModule),
        ('workflows', Workflow),
        ('users', User),
        ('orders', Order),
        ('sim_type_results', SimTypeResult),
        ('rounds', Round),
    ]

    for table_name, model in tables_info:
        try:
            records = model.query.all()
            if records:
                all_data[table_name] = [r.to_dict() if hasattr(r, 'to_dict') else serialize_model(r) for r in records]
                print(f"  ✓ {table_name}: {len(records)} 条")
        except Exception as e:
            print(f"  ⚠️ {table_name}: 导出失败 - {e}")

    # 保存到文件
    output_file = EXPORTED_DATA_DIR / 'full_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ 导出完成: {output_file}")
    return True


def serialize_model(obj):
    """序列化 SQLAlchemy 模型对象"""
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = int(val.timestamp())
        result[col.name] = val
    return result


# ============ 主函数 ============

# 预定义数据库配置
DB_CONFIGS = {
    'sqlite': 'sqlite:///structsim.db',
    'mysql': 'mysql+pymysql://root:password@localhost:3306/structsim?charset=utf8mb4',
}


def main():
    parser = argparse.ArgumentParser(
        description='StructSim 数据库管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python database/db_manager.py init          创建数据库表结构
  python database/db_manager.py seed          导入初始数据（从 init-data）
  python database/db_manager.py sync          从导出数据完整同步（exported-data）
  python database/db_manager.py export        导出当前数据库到 exported-data
  python database/db_manager.py clean         清理所有数据
  python database/db_manager.py reset         重置数据库（清理+创建+导入）
  python database/db_manager.py status        查看数据库状态

数据库切换:
  python database/db_manager.py sync -f --db sqlite   使用 SQLite 数据库
  python database/db_manager.py sync -f --db mysql    使用 MySQL 数据库

环境变量:
  DATABASE_URL=mysql+pymysql://user:pass@host:3306/db  自定义数据库连接
        """
    )
    parser.add_argument('command', choices=['init', 'seed', 'sync', 'export', 'clean', 'reset', 'status'],
                        help='要执行的命令')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制执行，不提示确认')
    parser.add_argument('--db', choices=['sqlite', 'mysql'], default=None,
                        help='指定数据库类型 (默认使用环境变量 DATABASE_URL 或 sqlite)')
    args = parser.parse_args()

    # 如果指定了 --db 参数，设置环境变量
    import os
    if args.db:
        db_url = DB_CONFIGS.get(args.db)
        if db_url:
            os.environ['DATABASE_URL'] = db_url
            print(f"📌 使用数据库: {args.db.upper()}")

    app = create_app()

    with app.app_context():
        print("\n" + "=" * 60)
        print("🚀 StructSim 数据库管理工具")
        print("=" * 60)

        # 显示当前数据库连接信息
        current_db = str(db.engine.url)
        db_type = 'SQLite' if 'sqlite' in current_db else 'MySQL'
        print(f"📊 数据库类型: {db_type}")
        print(f"📍 连接地址: {current_db}")

        try:
            if args.command == 'init':
                init_database()

            elif args.command == 'seed':
                seed_all()

            elif args.command == 'sync':
                if not args.force:
                    confirm = input("\n⚠️  确定要从导出数据同步吗？(y/N): ")
                    if confirm.lower() != 'y':
                        print("已取消")
                        return
                init_database()
                sync_from_exported()

            elif args.command == 'export':
                export_database()

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

