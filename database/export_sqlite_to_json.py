"""
导出SQLite数据库到JSON文件
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, inspect, text
from datetime import datetime

SQLITE_URL = 'sqlite:///sim_ai_paltform.db'
OUTPUT_DIR = Path(__file__).parent / 'exported-data'

def export_to_json():
    """导出所有表数据到JSON"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    engine = create_engine(SQLITE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    print(f"连接数据库: {SQLITE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"发现 {len(metadata.tables)} 个表\n")

    exported = {}

    with engine.connect() as conn:
        for table_name in sorted(metadata.tables.keys()):
            print(f"导出表: {table_name}")

            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            columns = result.keys()
            rows = result.fetchall()

            table_data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # 处理日期时间
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                table_data.append(row_dict)

            exported[table_name] = table_data

            # 保存单个表文件
            table_file = OUTPUT_DIR / f"{table_name}.json"
            with open(table_file, 'w', encoding='utf-8') as f:
                json.dump(table_data, f, ensure_ascii=False, indent=2)

            print(f"  -> {len(table_data)} 条记录 -> {table_file.name}")

    # 保存完整数据
    all_file = OUTPUT_DIR / "all_tables.json"
    with open(all_file, 'w', encoding='utf-8') as f:
        json.dump(exported, f, ensure_ascii=False, indent=2)

    print(f"\n导出完成！共 {len(exported)} 个表")
    print(f"完整数据: {all_file}")

if __name__ == '__main__':
    export_to_json()
