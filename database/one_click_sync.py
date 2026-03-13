"""
一键数据库同步脚本 - 从SQLite同步到MySQL
功能：同步表结构和数据
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.orm import sessionmaker

# 数据库配置
SQLITE_URL = 'sqlite:///sim_ai_paltform.db'
MYSQL_URL = 'mysql+pymysql://opti_user:cQi8Xjw3xTbJFG7s@api.xinqilingxi.cn:3306/sim_ai_paltform'

def sync_database():
    """同步数据库"""
    print("=" * 60)
    print("开始同步 SQLite -> MySQL")
    print("=" * 60)

    # 连接源数据库（SQLite）
    source_engine = create_engine(SQLITE_URL)
    source_metadata = MetaData()
    source_metadata.reflect(bind=source_engine)
    SourceSession = sessionmaker(bind=source_engine)
    source_session = SourceSession()

    # 连接目标数据库（MySQL）
    target_engine = create_engine(MYSQL_URL)
    target_inspector = inspect(target_engine)
    TargetSession = sessionmaker(bind=target_engine)
    target_session = TargetSession()

    print(f"\n源数据库: SQLite")
    print(f"目标数据库: MySQL")
    print(f"发现 {len(source_metadata.tables)} 个表\n")

    synced_tables = []

    for table_name in sorted(source_metadata.tables.keys()):
        print(f"\n处理表: {table_name}")
        table = source_metadata.tables[table_name]

        # 检查目标表是否存在
        if table_name not in target_inspector.get_table_names():
            print(f"  [创建表] {table_name}")
            table.create(target_engine)
        else:
            print(f"  [表已存在] {table_name}")

        # 同步数据
        try:
            # 读取源数据
            source_data = source_session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            source_count = len(source_data)

            # 检查目标数据
            target_count = target_session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

            print(f"  源数据: {source_count} 条")
            print(f"  目标数据: {target_count} 条")

            if source_count > 0 and target_count == 0:
                print(f"  [同步数据] 插入 {source_count} 条记录")

                # 获取列名
                columns = [col.name for col in table.columns]
                col_str = ', '.join(columns)
                placeholders = ', '.join([f":{col}" for col in columns])

                # 批量插入
                insert_sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"

                for row in source_data:
                    row_dict = dict(zip(columns, row))
                    target_session.execute(text(insert_sql), row_dict)

                target_session.commit()
                print(f"  [完成] 数据同步成功")
                synced_tables.append(table_name)
            elif target_count > 0:
                print(f"  [跳过] 目标表已有数据")
            else:
                print(f"  [跳过] 源表无数据")

        except Exception as e:
            print(f"  [错误] {str(e)}")
            target_session.rollback()

    source_session.close()
    target_session.close()

    print("\n" + "=" * 60)
    print(f"同步完成: 共同步 {len(synced_tables)} 个表的数据")
    if synced_tables:
        print("已同步的表:")
        for t in synced_tables:
            print(f"  - {t}")
    print("=" * 60)

if __name__ == '__main__':
    sync_database()
