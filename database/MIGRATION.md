# MySQL 全量迁移指南

> 当前策略：**默认无外键导出 + 覆盖导入目标库**。避免跨环境导入时的外键冲突。

## 1. 仅导出完整数据库（包含空表）

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --output-file "database/export/full_latest.sql"
```

执行后会生成：
- `full_latest.sql`：完整结构 + 数据（建表语句已移除外键）
- `full_latest_foreign_keys.sql`：可选的外键恢复语句

## 2. 一键覆盖同步到目标库（推荐）

```bash
python database/sync_mysql_full.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --target-db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --output-file "database/export/full_sync_latest.sql"
```

行为说明：
1. 从源库导出完整 SQL（默认去外键）
2. 清空目标库全部业务表
3. 导入导出 SQL，使目标库结构和字段与源库保持一致
4. 校验关键表（默认 `upload_files, upload_chunks`）

## 3. 仅导入已有 SQL

如果你已经有导出的 SQL 文件，可以直接导入：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_latest.sql"
```

如果需要先清空目标库再导入，可额外加：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_latest.sql" --drop-all-first
```

## 4. 同步后是否恢复外键

默认不恢复外键。若你确认目标库数据稳定，可执行：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_sync_latest.sql" --fk-sql-file "database/export/full_sync_latest_foreign_keys.sql"
```

## 5. 外键建议

建议恢复（价值高）：
- `upload_chunks.upload_id -> upload_files.upload_id`：避免孤儿分片，上传完整性更好
- 订单结果主链路外键（如 `rounds -> sim_type_results -> orders`）：减少结果脏数据

可不恢复（价值一般）：
- 高频迭代的配置关系表外键。跨环境迁移频繁时，保留无外键更稳。

## 6. 上传异常快速修复

`database/migrations/` 当前仅保留上传分片表修复脚本。

若出现 `upload_chunks` 缺失，执行：

```bash
python database/import_mysql.py --sql-file "database/migrations/add_upload_chunks_table.sql"
```

---

更多目录说明见：`database/README.md`
