"""
完整同步SQLite到MySQL（表结构+数据）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy.schema import CreateTable

SQLITE_URL = 'sqlite:///instance/sim_ai_paltform.db'
MYSQL_URL = 'mysql+pymysql://opti_user:cQi8Xjw3xTbJFG7s@api.xinqilingxi.cn:3306/sim_ai_paltform'

def sync_schema_and_data():
    print("=" * 60)
    print("完整同步 SQLite -> MySQL")
    print("=" * 60)

    src_engine = create_engine(SQLITE_URL)
    dst_engine = create_engine(MYSQL_URL)

    src_metadata = MetaData()
    src_metadata.reflect(bind=src_engine)

    dst_inspector = inspect(dst_engine)
    dst_tables = dst_inspector.get_table_names()

    print(f"\nSQLite表: {len(src_metadata.tables)}")
    print(f"MySQL表: {len(dst_tables)}\n")

    # 第一步：同步表结构
    print("=" * 60)
    print("第一步：同步表结构")
    print("=" * 60)

    created_tables = []
    with dst_engine.connect() as dst_conn:
        for table_name in sorted(src_metadata.tables.keys()):
            if table_name not in dst_tables:
                print(f"[创建] {table_name}")
                table = src_metadata.tables[table_name]

                # 生成建表SQL
                create_sql = str(CreateTable(table).compile(dst_engine))
                create_sql = create_sql.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
                create_sql = create_sql.replace('INTEGER', 'INT')
                create_sql = create_sql.replace('DATETIME', 'TIMESTAMP')

                if 'ENGINE=' not in create_sql:
                    create_sql += ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'

                try:
                    dst_conn.execute(text(create_sql))
                    dst_conn.commit()
                    created_tables.append(table_name)
                except Exception as e:
                    print(f"  错误: {str(e)[:100]}")

    print(f"\n创建了 {len(created_tables)} 个表")

    # 第二步：同步数据
    print("\n" + "=" * 60)
    print("第二步：同步数据")
    print("=" * 60 + "\n")

    synced = []
    with src_engine.connect() as src_conn, dst_engine.connect() as dst_conn:
        # 禁用外键检查
        dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        dst_conn.commit()

        # 刷新目标表列表
        dst_inspector = inspect(dst_engine)
        dst_tables = dst_inspector.get_table_names()

        for table_name in sorted(src_metadata.tables.keys()):
            if table_name not in dst_tables:
                continue

            src_data = src_conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            src_count = len(src_data)

            if src_count == 0:
                continue

            print(f"{table_name}: {src_count} 条", end=" ")

            # 清空表
            dst_conn.execute(text(f"TRUNCATE TABLE {table_name}"))

            # 获取列名
            table = src_metadata.tables[table_name]
            columns = [col.name for col in table.columns]

            # 批量插入
            inserted = 0
            for row in src_data:
                try:
                    row_dict = dict(zip(columns, row))

                    # 转义列名（处理MySQL保留字）
                    col_str = ', '.join([f'`{col}`' for col in columns])
                    placeholders = ', '.join([f":{col}" for col in columns])
                    insert_sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"

                    dst_conn.execute(text(insert_sql), row_dict)
                    inserted += 1
                except Exception as e:
                    if inserted == 0:
                        print(f"\n  错误: {str(e)[:80]}")
                    continue

            dst_conn.commit()
            if inserted > 0:
                print(f"-> {inserted} 条")
                synced.append(table_name)

        # 恢复外键检查
        dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        dst_conn.commit()

    print("\n" + "=" * 60)
    print(f"同步完成: {len(synced)} 个表")
    print("=" * 60)

if __name__ == '__main__':
    sync_schema_and_data()
