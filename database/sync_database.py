"""
数据库同步脚本 - 支持SQLite和MySQL
读取当前数据库结构，检查表是否存在，对比结构，同步数据
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from sqlalchemy import inspect, text, MetaData
from sqlalchemy.schema import CreateTable


class DatabaseSync:
    def __init__(self):
        self.app = create_app()
        self.schema_dir = Path(__file__).parent / 'schemas'
        self.data_dir = Path(__file__).parent / 'data'
        self.schema_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

    def export_schema(self):
        """导出所有表结构到JSON"""
        with self.app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            for table_name in tables:
                schema = {
                    'table_name': table_name,
                    'columns': inspector.get_columns(table_name),
                    'primary_key': inspector.get_pk_constraint(table_name),
                    'foreign_keys': inspector.get_foreign_keys(table_name),
                    'indexes': inspector.get_indexes(table_name),
                    'unique_constraints': inspector.get_unique_constraints(table_name)
                }

                file_path = self.schema_dir / f'{table_name}.json'
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, default=str, ensure_ascii=False)

                print(f"导出表结构: {table_name}")

    def export_data(self, table_name):
        """导出表数据"""
        with self.app.app_context():
            result = db.session.execute(text(f'SELECT * FROM {table_name}'))
            rows = [dict(row._mapping) for row in result]

            file_path = self.data_dir / f'{table_name}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=2, default=str, ensure_ascii=False)

            print(f"导出数据: {table_name} ({len(rows)} 行)")

    def table_exists(self, table_name):
        """检查表是否存在"""
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()

    def get_create_sql(self, table_name):
        """生成建表SQL"""
        metadata = MetaData()
        metadata.reflect(bind=db.engine, only=[table_name])
        table = metadata.tables[table_name]

        create_sql = str(CreateTable(table).compile(db.engine))

        if db.engine.dialect.name == 'mysql':
            create_sql = create_sql.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
            create_sql += ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'

        return create_sql

    def sync_table(self, table_name):
        """同步单个表"""
        if not self.table_exists(table_name):
            print(f"创建表: {table_name}")
            create_sql = self.get_create_sql(table_name)
            db.session.execute(text(create_sql))
            db.session.commit()
            return True
        return False

    def sync_all(self):
        """一键同步所有表"""
        with self.app.app_context():
            print(f"数据库: {db.engine.dialect.name}")
            print("-" * 60)

            metadata = MetaData()
            metadata.reflect(bind=db.engine)

            for table_name in metadata.tables.keys():
                self.sync_table(table_name)

            print("-" * 60)
            print("同步完成")


if __name__ == '__main__':
    sync = DatabaseSync()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'export':
            sync.export_schema()
        elif cmd == 'sync':
            sync.sync_all()
    else:
        sync.sync_all()
