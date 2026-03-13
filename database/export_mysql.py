"""
导出MySQL数据库到SQL文件
用于迁移到内网环境
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, text, inspect
from datetime import datetime

MYSQL_URL = 'mysql+pymysql://opti_user:cQi8Xjw3xTbJFG7s@api.xinqilingxi.cn:3306/sim_ai_paltform'
OUTPUT_DIR = Path(__file__).parent / 'export'

def export_database():
    """导出数据库结构和数据"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    engine = create_engine(MYSQL_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = OUTPUT_DIR / f'database_export_{timestamp}.sql'

    print("=" * 60)
    print("导出MySQL数据库")
    print("=" * 60)
    print(f"\n输出文件: {output_file}\n")

    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入头部
        f.write("-- StructSim AI Platform Database Export\n")
        f.write(f"-- Export Time: {datetime.now()}\n")
        f.write("-- Database: sim_ai_paltform\n\n")
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        f.write("SET NAMES utf8mb4;\n\n")

        with engine.connect() as conn:
            # 导出每个表
            for table_name in sorted(metadata.tables.keys()):
                print(f"导出表: {table_name}")

                # 获取建表语句
                result = conn.execute(text(f"SHOW CREATE TABLE {table_name}"))
                create_sql = result.fetchone()[1]

                f.write(f"-- Table: {table_name}\n")
                f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                f.write(f"{create_sql};\n\n")

                # 导出数据
                data = conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                if data:
                    columns = metadata.tables[table_name].columns.keys()
                    col_str = ', '.join([f'`{col}`' for col in columns])

                    f.write(f"-- Data for {table_name}\n")
                    f.write(f"INSERT INTO `{table_name}` ({col_str}) VALUES\n")

                    for i, row in enumerate(data):
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                # 转义字符串
                                val_str = str(val).replace('\\', '\\\\').replace("'", "\\'")
                                values.append(f"'{val_str}'")

                        value_str = f"({', '.join(values)})"
                        if i < len(data) - 1:
                            f.write(f"{value_str},\n")
                        else:
                            f.write(f"{value_str};\n")

                    f.write(f"\n")

        f.write("SET FOREIGN_KEY_CHECKS=1;\n")

    print(f"\n导出完成！")
    print(f"文件大小: {output_file.stat().st_size / 1024:.2f} KB")
    print(f"文件路径: {output_file}")

if __name__ == '__main__':
    export_database()
