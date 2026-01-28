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


def seed_all():
    """导入所有数据"""
    seed_permissions()
    seed_roles()
    seed_departments()
    seed_users()
    seed_base_config()


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

