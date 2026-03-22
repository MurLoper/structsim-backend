# MySQL 全量迁移指南

当前策略是“先补 schema，再导出，再覆盖导入目标库”，默认不恢复外键，优先保证跨环境迁移稳定。

## 1. 先补 schema

如果源库还没有最新字段和表，先执行下面两类升级：

```bash
python database/migrations/user_identity_upgrade.py --db-url "mysql+pymysql://USER:PASS@HOST:3306/DB"
python database/migrations/order_condition_opti_upgrade.py --db-url "mysql+pymysql://USER:PASS@HOST:3306/DB"
```

如果应用是通过 Flask 启动，且未关闭自动升级，也会在启动时自动检查：

- `AUTO_IDENTITY_UPGRADE=true`
- `AUTO_ORDER_CONDITION_UPGRADE=true`

## 2. 仅导出完整数据库

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --output-file "database/export/full_latest.sql"
```

执行后会生成：

- `full_latest.sql`：完整结构和数据，建表语句默认去掉外键
- `full_latest_foreign_keys.sql`：可选的外键恢复语句

## 3. 一键覆盖同步到目标库

```bash
python database/sync_mysql_full.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --target-db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --output-file "database/export/full_sync_latest.sql"
```

行为说明：

1. 对源库做 schema 补齐检查
2. 导出源库完整 SQL
3. 清空目标库业务表
4. 覆盖导入最新结构和数据
5. 对目标库再次做 schema 补齐检查

## 4. 仅导入已有 SQL

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_latest.sql"
```

如果要先清空目标库再导入：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_latest.sql" --drop-all-first
```

## 5. 是否恢复外键

默认不恢复外键。

如果目标库数据已经稳定，需要恢复导出文件对应的外键：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_sync_latest.sql" --fk-sql-file "database/export/full_sync_latest_foreign_keys.sql"
```

## 6. 手工 SQL 迁移脚本

在无法直接运行 Python 升级脚本时，可以手工执行：

- `database/migrations/add_upload_chunks_table.sql`
- `database/migrations/add_order_condition_opti_table.sql`

其中 `add_order_condition_opti_table.sql` 会补：

- `orders.opt_issue_id`
- `orders.condition_summary`
- `order_condition_opti`

## 7. 建议顺序

推荐按下面顺序执行：

1. 先在源库运行 Python 升级脚本
2. 确认新表和新字段存在
3. 导出 `full_latest.sql`
4. 在目标库执行覆盖导入
5. 必要时再恢复外键
