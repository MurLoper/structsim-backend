# database 目录说明

## 核心脚本

- `export_mysql.py`：导出完整 MySQL，默认剥离外键，并生成配套的 `*_foreign_keys.sql`
- `import_mysql.py`：导入 SQL 到目标库，支持按需清空目标库并恢复外键
- `sync_mysql_full.py`：一键全量同步，流程为“导出源库 -> 覆盖导入目标库”
- `migrations/`：保留需要单独执行的修复 SQL，目前主要是上传分片表修复脚本
- `export/`：默认导出目录，保存最新导出的 SQL 文件

## 推荐链路

- 只导出当前库：`export_mysql.py`
- 将源库完整覆盖到目标库：`sync_mysql_full.py`
- 仅导入已有 SQL：`import_mysql.py`
- 导入后按需恢复外键：`import_mysql.py --fk-sql-file ...`

## 关键原则

1. 每次功能/字段变更后，都可用 `export_mysql.py` 导出当前完整库（包含空表）
2. 迁移到任意平台时，用 `sync_mysql_full.py` 覆盖旧库，避免“新表没建/旧字段没删”问题
3. 默认不加外键，降低迁移失败概率；上线稳定后按需恢复外键
4. 结果校验默认关注 `upload_files` 和 `upload_chunks`，可通过命令参数改成其他关键表

## 常用命令

导出当前库：

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://USER:PASS@HOST:3306/DB" --output-file "database/export/full_latest.sql"
```

导入到目标库：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://USER:PASS@HOST:3306/DB" --sql-file "database/export/full_latest.sql"
```

覆盖同步到目标库：

```bash
python database/sync_mysql_full.py --source-db-url "mysql+pymysql://SOURCE_USER:PASS@SOURCE_HOST:3306/SOURCE_DB" --target-db-url "mysql+pymysql://TARGET_USER:PASS@TARGET_HOST:3306/TARGET_DB" --output-file "database/export/full_sync_latest.sql"
```

## 详细操作文档

请看：`database/MIGRATION.md`
