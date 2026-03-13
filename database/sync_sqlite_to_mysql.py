"""
从SQLite同步数据到MySQL（处理外键约束）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, text, inspect

SQLITE_URL = 'sqlite:///instance/sim_ai_paltform.db'
MYSQL_URL = 'mysql+pymysql://opti_user:cQi8Xjw3xTbJFG7s@api.xinqilingxi.cn:3306/sim_ai_paltform'

def sync_data():
    print("=" * 60)
    print("开始同步 SQLite -> MySQL")
    print("=" * 60)

    src_engine = create_engine(SQLITE_URL)
    dst_engine = create_engine(MYSQL_URL)

    src_metadata = MetaData()
    src_metadata.reflect(bind=src_engine)

    dst_inspector = inspect(dst_engine)
    dst_tables = dst_inspector.get_table_names()

    print(f"\nSQLite表: {len(src_metadata.tables)}")
    print(f"MySQL表: {len(dst_tables)}\n")

    synced = []

    with src_engine.connect() as src_conn, dst_engine.connect() as dst_conn:
        # 禁用外键检查
        dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        dst_conn.commit()
        print("已禁用外键检查\n")

        for table_name in sorted(src_metadata.tables.keys()):
            if table_name not in dst_tables:
                print(f"[跳过] {table_name} - MySQL中不存在")
                continue

            src_data = src_conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            src_count = len(src_data)
            dst_count = dst_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

            print(f"{table_name}: SQLite={src_count}, MySQL={dst_count}")

            if src_count == 0:
                continue

            # 清空并插入
            dst_conn.execute(text(f"TRUNCATE TABLE {table_name}"))

            table = src_metadata.tables[table_name]
            columns = [col.name for col in table.columns]
            col_str = ', '.join(columns)
            placeholders = ', '.join([f":{col}" for col in columns])
            insert_sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"

            inserted = 0
            for row in src_data:
                try:
                    row_dict = dict(zip(columns, row))
                    dst_conn.execute(text(insert_sql), row_dict)
                    inserted += 1
                except Exception as e:
                    print(f"  错误: {str(e)[:100]}")

            dst_conn.commit()
            if inserted > 0:
                print(f"  -> 插入 {inserted} 条")
                synced.append(table_name)

        # 恢复外键检查
        dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        dst_conn.commit()
        print("\n已恢复外键检查")

    print("\n" + "=" * 60)
    print(f"同步完成: {len(synced)} 个表")
    print("=" * 60)

if __name__ == '__main__':
    sync_data()
