"""
数据库初始化脚本 - 统一管理数据库结构和初始数据
用于项目迁移和新环境部署，确保数据库结构一致性

使用方法:
    python init_database.py --help                    # 查看帮助
    python init_database.py --init                    # 初始化数据库结构
    python init_database.py --seed                    # 填充测试数据
    python init_database.py --init --seed             # 初始化并填充数据
    python init_database.py --reset                   # 重置数据库（危险操作）
    python init_database.py --export-schema           # 导出数据库结构SQL
    python init_database.py --check                   # 检查数据库状态
"""
import argparse
import sys
from datetime import datetime
from app import create_app, db
from seed import seed_database


def init_database():
    """初始化数据库结构（创建所有表）"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("数据库初始化 - 创建表结构")
        print("=" * 60)
        
        # 创建所有表
        db.create_all()
        
        # 获取所有表名
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n✓ 成功创建 {len(tables)} 个表:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        print("\n数据库结构初始化完成！")
        return True


def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("⚠️  警告：即将重置数据库（删除所有数据）")
        print("=" * 60)
        
        confirm = input("\n确认要继续吗？输入 'YES' 确认: ")
        if confirm != 'YES':
            print("操作已取消")
            return False
        
        print("\n正在删除所有表...")
        db.drop_all()
        
        print("正在重新创建表结构...")
        db.create_all()
        
        print("\n✓ 数据库重置完成！")
        return True


def check_database():
    """检查数据库状态"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("数据库状态检查")
        print("=" * 60)
        
        try:
            # 检查数据库连接
            db.session.execute(db.text('SELECT 1'))
            print("\n✓ 数据库连接正常")
            
            # 获取表信息
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n数据库表数量: {len(tables)}")
            
            # 检查关键表是否存在
            required_tables = [
                'users', 'roles', 'permissions', 'menus',
                'projects', 'sim_types', 'param_defs', 'condition_defs', 'output_defs',
                'orders', 'sim_type_results', 'rounds',
                'solvers', 'workflows', 'status_defs'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"\n⚠️  缺少以下关键表:")
                for table in missing_tables:
                    print(f"  - {table}")
                print("\n建议运行: python init_database.py --init")
            else:
                print("\n✓ 所有关键表都存在")
            
            # 统计数据量
            print("\n数据统计:")
            data_tables = {
                'users': '用户',
                'orders': '订单',
                'projects': '项目',
                'sim_types': '仿真类型',
                'sim_type_results': '仿真结果',
                'rounds': '轮次数据'
            }
            
            for table, name in data_tables.items():
                if table in tables:
                    try:
                        result = db.session.execute(db.text(f'SELECT COUNT(*) FROM {table}'))
                        count = result.scalar()
                        print(f"  - {name} ({table}): {count} 条")
                    except Exception as e:
                        print(f"  - {name} ({table}): 查询失败")
            
            print("\n数据库检查完成！")
            return True
            
        except Exception as e:
            print(f"\n✗ 数据库连接失败: {e}")
            return False


def export_schema():
    """导出数据库结构SQL"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("导出数据库结构")
        print("=" * 60)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'migrations/schema_export_{timestamp}.sql'

        print(f"\n导出文件: {filename}")
        print("注意: 此功能需要手动使用 mysqldump 或其他工具")
        print("\n推荐命令:")
        print("  mysqldump -u root -p --no-data sim_ai_paltform > schema.sql")

        return True


def main():
    """主函数 - 解析命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(
        description='数据库初始化和管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python init_database.py --init              # 初始化数据库结构
  python init_database.py --seed              # 填充测试数据
  python init_database.py --init --seed       # 初始化并填充数据
  python init_database.py --reset             # 重置数据库
  python init_database.py --check             # 检查数据库状态
  python init_database.py --export-schema     # 导出数据库结构
        """
    )

    parser.add_argument('--init', action='store_true',
                       help='初始化数据库结构（创建所有表）')
    parser.add_argument('--seed', action='store_true',
                       help='填充测试数据')
    parser.add_argument('--reset', action='store_true',
                       help='重置数据库（删除所有数据并重新创建）')
    parser.add_argument('--check', action='store_true',
                       help='检查数据库状态')
    parser.add_argument('--export-schema', action='store_true',
                       help='导出数据库结构SQL')

    args = parser.parse_args()

    # 如果没有指定任何参数，显示帮助信息
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        # 执行相应操作
        if args.reset:
            if not reset_database():
                sys.exit(1)

        if args.init:
            if not init_database():
                sys.exit(1)

        if args.seed:
            print("\n" + "=" * 60)
            print("填充测试数据")
            print("=" * 60)
            seed_database()

        if args.check:
            if not check_database():
                sys.exit(1)

        if args.export_schema:
            if not export_schema():
                sys.exit(1)

        print("\n" + "=" * 60)
        print("✓ 所有操作完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

