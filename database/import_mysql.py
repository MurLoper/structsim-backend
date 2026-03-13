"""
导入SQL文件到MySQL数据库
用于内网环境部署
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
import argparse

def import_database(sql_file, db_url):
    """导入SQL文件"""
    print("=" * 60)
    print("导入数据库")
    print("=" * 60)
    print(f"\nSQL文件: {sql_file}")
    print(f"目标数据库: {db_url}\n")

    if not Path(sql_file).exists():
        print(f"错误: 文件不存在 {sql_file}")
        return

    engine = create_engine(db_url)

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 分割SQL语句
    statements = []
    current = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        current.append(line)
        if line.endswith(';'):
            statements.append(' '.join(current))
            current = []

    print(f"共 {len(statements)} 条SQL语句\n")

    with engine.connect() as conn:
        for i, stmt in enumerate(statements, 1):
            try:
                conn.execute(text(stmt))
                conn.commit()
                if i % 10 == 0:
                    print(f"已执行 {i}/{len(statements)} 条")
            except Exception as e:
                print(f"错误 (语句 {i}): {str(e)[:100]}")

    print("\n导入完成！")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='导入SQL文件到MySQL')
    parser.add_argument('sql_file', help='SQL文件路径')
    parser.add_argument('--db-url', default='mysql+pymysql://root:password@localhost:3306/sim_ai_paltform',
                        help='数据库连接URL')

    args = parser.parse_args()
    import_database(args.sql_file, args.db_url)
