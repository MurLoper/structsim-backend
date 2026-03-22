# database 目录说明

## 核心脚本

- `export_mysql.py`：导出完整 MySQL，默认剥离外键，并生成配套的 `*_foreign_keys.sql`
- `import_mysql.py`：导入 SQL 到目标库，支持按需清空目标库并恢复外键
- `sync_mysql_full.py`：一键全量同步，流程为“导出源库 -> 覆盖导入目标库”
- `migrations/`：保留需要单独执行的补库脚本和 Python 升级脚本
- `export/`：默认导出目录，保存最新导出的 SQL 文件

## 当前迁移脚本

- `migrations/add_upload_chunks_table.sql`：补上传分片表
- `migrations/add_order_condition_opti_table.sql`：补 `orders.opt_issue_id`、`orders.condition_summary` 和 `order_condition_opti`
- `migrations/user_identity_upgrade.py`：补用户身份字段、角色资源限制字段
- `migrations/order_condition_opti_upgrade.py`：补订单 condition 运行实体相关表结构

## 推荐链路

1. 源库先执行自动升级或手工迁移，确保 schema 已补齐
2. 用 `export_mysql.py` 导出最新完整库
3. 用 `sync_mysql_full.py` 覆盖同步到目标库，或用 `import_mysql.py` 导入已有 SQL

## 自动升级开关

- `AUTO_IDENTITY_UPGRADE=true`：应用启动时自动检查并补用户身份相关字段
- `AUTO_ORDER_CONDITION_UPGRADE=true`：应用启动时自动检查并补订单 condition 相关字段和表

两个开关默认开启，仅在 MySQL 主库上生效，SQLite 开发库会自动跳过。

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

手工补订单 condition 相关表结构：

```bash
python database/migrations/order_condition_opti_upgrade.py --db-url "mysql+pymysql://USER:PASS@HOST:3306/DB"
```

更多迁移说明见 `database/MIGRATION.md`。
