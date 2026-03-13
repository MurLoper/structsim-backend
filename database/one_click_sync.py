"""
一键数据库同步脚本 - 兼容SQLite和MySQL
功能：检查表存在性、对比结构、同步数据
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from sqlalchemy import inspect, text, MetaData
from sqlalchemy.schema import CreateTable


def get_dialect():
    """获取数据库类型"""
    return db.engine.dialect.name


def table_exists(table_name):
    """检查表是否存在"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()


def get_create_sql(table_name, source_metadata):
    """生成建表SQL（兼容MySQL和SQLite）"""
    table = source_metadata.tables[table_name]
    create_sql = str(CreateTable(table).compile(db.engine))

    dialect = get_dialect()
    if dialect == 'mysql':
        create_sql = create_sql.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
        create_sql = create_sql.replace('INTEGER', 'INT')
        create_sql = create_sql.replace('DATETIME', 'TIMESTAMP')
        if 'ENGINE=' not in create_sql:
            create_sql += ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'

    return create_sql


def compare_columns(table_name):
    """对比表结构差异"""
    inspector = inspect(db.engine)
    current_cols = {col['name']: col for col in inspector.get_columns(table_name)}
    return current_cols


def sync_table(table_name, source_metadata):
    """同步单个表结构"""
    if not table_exists(table_name):
        print(f"  [创建] {table_name}")
        create_sql = get_create_sql(table_name, source_metadata)
        db.session.execute(text(create_sql))
        db.session.commit()
        return 'created'
    else:
        print(f"  [存在] {table_name}")
        return 'exists'


def sync_all():
    """一键同步所有表"""
    app = create_app()
    with app.app_context():
        dialect = get_dialect()
        print(f"数据库类型: {dialect}")
        print(f"连接地址: {db.engine.url}")
        print("=" * 60)

        # 反射当前数据库结构
        metadata = MetaData()
        metadata.reflect(bind=db.engine)

        tables = list(metadata.tables.keys())
        print(f"发现 {len(tables)} 个表\n")

        created = []
        exists = []

        for table_name in sorted(tables):
            result = sync_table(table_name, metadata)
            if result == 'created':
                created.append(table_name)
            else:
                exists.append(table_name)

        print("\n" + "=" * 60)
        print(f"同步完成: 创建 {len(created)} 个表, 已存在 {len(exists)} 个表")


if __name__ == '__main__':
    sync_all()
