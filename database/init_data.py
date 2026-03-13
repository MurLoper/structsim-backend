"""
数据初始化脚本 - 导入基础配置数据
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from sqlalchemy import text, inspect


def table_is_empty(table_name):
    """检查表是否为空"""
    result = db.session.execute(text(f'SELECT COUNT(*) as cnt FROM {table_name}'))
    count = result.scalar()
    return count == 0


def import_table_data(table_name):
    """导入表数据"""
    data_file = Path(__file__).parent / 'data' / f'{table_name}.json'

    if not data_file.exists():
        return 0

    with open(data_file, 'r', encoding='utf-8') as f:
        rows = json.load(f)

    if not rows:
        return 0

    # 获取列名
    cols = list(rows[0].keys())
    placeholders = ', '.join([f':{col}' for col in cols])
    col_names = ', '.join(cols)

    insert_sql = f'INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})'

    for row in rows:
        try:
            db.session.execute(text(insert_sql), row)
        except Exception as e:
            print(f"  [跳过] {table_name}: {e}")
            db.session.rollback()
            continue

    db.session.commit()
    return len(rows)


def init_all():
    """初始化所有基础数据"""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        print("开始导入数据")
        print("=" * 60)

        imported = 0
        skipped = 0

        for table_name in sorted(tables):
            if not table_is_empty(table_name):
                print(f"  [已有数据] {table_name}")
                skipped += 1
                continue

            count = import_table_data(table_name)
            if count > 0:
                print(f"  [导入] {table_name}: {count} 行")
                imported += 1
            else:
                skipped += 1

        print("=" * 60)
        print(f"完成: 导入 {imported} 个表, 跳过 {skipped} 个表")


if __name__ == '__main__':
    init_all()
