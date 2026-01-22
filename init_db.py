"""
统一数据库初始化脚本
整合 seed.py 和 init_config_data.py 的功能
支持从 data-config 目录导入配置数据，并创建测试用户

使用方法:
    python init_db.py --clean    # 清理所有数据
    python init_db.py --seed     # 导入种子数据
    python init_db.py --all      # 清理并导入（推荐）
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models.config import (
    Project, SimType, ParamDef, OutputDef, Solver, StatusDef,
    FoldType, ModelLevel, CareDevice, SolverResource, Department,
    ParamTplSet, ParamTplItem, CondOutSet
)
from app.models.auth import User, Role, Permission
from app.models.config_relations import ParamGroup, ParamGroupParamRel, ProjectSimTypeRel
from app.models.order import Order, OrderResult
from app.models.result import SimTypeResult, Round
from werkzeug.security import generate_password_hash

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent / 'structsim-ai-platform' / 'data-config'


def load_json_config(filename):
    """加载JSON配置文件"""
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        print(f"⚠️  配置文件不存在: {filepath}")
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        # 移除注释
        lines = []
        for line in content.split('\n'):
            if '//' in line:
                line = line[:line.index('//')]
            lines.append(line)
        clean_content = '\n'.join(lines)
        return json.loads(clean_content)


def clean_all_data():
    """清理所有数据"""
    print("\n" + "=" * 60)
    print("🗑️  清理所有数据...")
    print("=" * 60)
    
    try:
        # 按依赖顺序清理
        print("  清理订单和结果数据...")
        OrderResult.query.delete()
        Round.query.delete()
        SimTypeResult.query.delete()
        Order.query.delete()
        
        print("  清理关联表...")
        ParamGroupParamRel.query.delete()
        ProjectSimTypeRel.query.delete()
        
        print("  清理配置表...")
        ParamTplItem.query.delete()
        ParamTplSet.query.delete()
        CondOutSet.query.delete()
        ParamGroup.query.delete()
        ParamDef.query.delete()
        OutputDef.query.delete()
        StatusDef.query.delete()
        Solver.query.delete()
        SolverResource.query.delete()
        CareDevice.query.delete()
        ModelLevel.query.delete()
        FoldType.query.delete()
        SimType.query.delete()
        Project.query.delete()
        
        print("  清理用户相关表...")
        User.query.delete()
        Role.query.delete()
        Permission.query.delete()
        Department.query.delete()
        
        db.session.commit()
        print("✅ 数据清理完成\n")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 清理失败: {str(e)}\n")
        raise


def seed_test_users():
    """创建测试用户（不同权限）"""
    print("\n👥 创建测试用户...")
    
    # 1. 创建权限
    permissions = [
        Permission(id=1, name='查看仪表板', code='VIEW_DASHBOARD', type='PAGE', valid=1, sort=10),
        Permission(id=2, name='创建订单', code='CREATE_ORDER', type='ACTION', valid=1, sort=20),
        Permission(id=3, name='查看结果', code='VIEW_RESULTS', type='PAGE', valid=1, sort=30),
        Permission(id=4, name='管理配置', code='MANAGE_CONFIG', type='PAGE', valid=1, sort=40),
        Permission(id=5, name='管理用户', code='MANAGE_USERS', type='PAGE', valid=1, sort=50),
        Permission(id=6, name='系统设置', code='SYSTEM_SETTINGS', type='PAGE', valid=1, sort=60),
    ]
    for perm in permissions:
        db.session.add(perm)
    
    # 2. 创建角色
    roles = [
        Role(id=1, name='管理员', code='ADMIN', description='系统管理员，拥有所有权限',
             permission_ids=[1, 2, 3, 4, 5, 6], valid=1, sort=10),
        Role(id=2, name='工程师', code='ENGINEER', description='仿真工程师，可创建订单和查看结果',
             permission_ids=[1, 2, 3, 4], valid=1, sort=20),
        Role(id=3, name='查看者', code='VIEWER', description='只读用户，只能查看',
             permission_ids=[1, 3], valid=1, sort=30),
    ]
    for role in roles:
        db.session.add(role)
    
    # 3. 创建测试用户
    users = [
        {
            'id': 1,
            'username': 'alice',
            'email': 'alice@sim.com',
            'name': 'Alice Admin',
            'role_ids': [1],  # 管理员
            'description': '管理员账号 - 拥有所有权限'
        },
        {
            'id': 2,
            'username': 'bob',
            'email': 'bob@sim.com',
            'name': 'Bob Engineer',
            'role_ids': [2],  # 工程师
            'description': '工程师账号 - 可创建订单和管理配置'
        },
        {
            'id': 3,
            'username': 'charlie',
            'email': 'charlie@sim.com',
            'name': 'Charlie Viewer',
            'role_ids': [3],  # 查看者
            'description': '查看者账号 - 只读权限'
        },
        {
            'id': 4,
            'username': 'david',
            'email': 'david@sim.com',
            'name': 'David Engineer',
            'role_ids': [2],  # 工程师
            'description': '工程师账号2 - 可创建订单和管理配置'
        },
    ]
    
    for user_data in users:
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            name=user_data['name'],
            role_ids=user_data['role_ids'],
            valid=1,
            preferences={'lang': 1, 'theme': 1},
            created_at=int(datetime.now().timestamp())
        )
        db.session.add(user)
        print(f"  ✓ {user_data['name']} ({user_data['email']}) - {user_data['description']}")
    
    db.session.commit()
    print(f"✅ 创建了 {len(users)} 个测试用户\n")


def seed_config_data():
    """从 data-config 导入配置数据"""
    print("\n📦 导入配置数据...")
    
    # 加载配置文件
    base_config = load_json_config('base_config.json')
    param_groups_config = load_json_config('param_groups.json')
    
    if not base_config:
        print("⚠️  base_config.json 不存在，跳过配置数据导入")
        return
    
    # 导入项目
    print("  导入项目...")
    for item in base_config.get('projject_list', []):
        project = Project(
            id=int(item['project_id']),
            name=item['project_name'],
            code=item['project_name'].upper(),
            valid=1,
            sort=100,
            created_at=int(datetime.now().timestamp()),
            updated_at=int(datetime.now().timestamp())
        )
        db.session.add(project)
    
    # 导入仿真类型
    print("  导入仿真类型...")
    for item in base_config.get('sim_type_list', []):
        sim_type = SimType(
            id=int(item['sim_type_id']),
            name=item['sim_type_name'],
            code=item['sim_type_name'].upper(),
            valid=1,
            sort=100,
            created_at=int(datetime.now().timestamp()),
            updated_at=int(datetime.now().timestamp())
        )
        db.session.add(sim_type)
    
    # 导入参数定义
    print("  导入参数定义...")
    for item in base_config.get('param_map', []):
        param = ParamDef(
            id=item['opt_param_id'],
            name=item['param_desc'],
            key=item['param_name'],
            val_type=1,
            unit=item.get('param_unit', ''),
            min_val=item.get('param_default_min'),
            max_val=item.get('param_default_max'),
            default_val=str(item.get('param_default_init', '')),
            precision=6,
            required=1,
            valid=1,
            sort=item['opt_param_id']
        )
        db.session.add(param)
    
    # 导入输出定义
    print("  导入输出定义...")
    for item in base_config.get('resp_map', []):
        output = OutputDef(
            id=item['resp_param_id'],
            name=item['ouput_type'],
            code=item['ouput_type'],
            val_type=1,
            unit='',
            valid=1,
            sort=item['resp_param_id']
        )
        db.session.add(output)
    
    # 导入求解器
    print("  导入求解器...")
    for item in base_config.get('solver_list', []):
        solver = Solver(
            id=item['solver_id'],
            name=item['solver_name'],
            code=item['solver_name'].upper().replace(' ', '_'),
            valid=1,
            sort=item['solver_id']
        )
        db.session.add(solver)
    
    db.session.commit()
    print("✅ 配置数据导入完成\n")


def main():
    parser = argparse.ArgumentParser(description='统一数据库初始化脚本')
    parser.add_argument('--clean', action='store_true', help='清理所有数据')
    parser.add_argument('--seed', action='store_true', help='导入种子数据')
    parser.add_argument('--all', action='store_true', help='清理并导入（推荐）')
    parser.add_argument('--init', action='store_true', help='创建数据库表结构')
    args = parser.parse_args()

    if not any([args.clean, args.seed, args.all, args.init]):
        parser.print_help()
        return

    app = create_app()

    with app.app_context():
        print("\n" + "=" * 60)
        print("🚀 StructSim 数据库初始化")
        print("=" * 60)

        try:
            # 1. 创建表结构（如果需要）
            if args.init or args.all:
                print("\n📋 创建数据库表结构...")
                db.create_all()
                print("✅ 数据库表结构创建完成")

            # 2. 清理数据
            if args.all or args.clean:
                clean_all_data()

            # 3. 导入种子数据
            if args.all or args.seed:
                seed_test_users()
                seed_config_data()

            print("\n" + "=" * 60)
            print("✅ 初始化完成！")
            print("=" * 60)

            if args.all or args.seed:
                print("\n测试用户账号:")
                print("  1. alice@sim.com   - 管理员（所有权限）")
                print("  2. bob@sim.com     - 工程师（创建订单+管理配置）")
                print("  3. charlie@sim.com - 查看者（只读）")
                print("  4. david@sim.com   - 工程师（创建订单+管理配置）")
            print("\n")

        except Exception as e:
            print(f"\n❌ 初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

