# MySQL 离线同步指南

只保留离线路径，固定 3 步。

适用前提：

- 开发环境数据库已经完成本次字段/表结构变更
- 目标内网数据库已经手工创建完成
- 内网环境无法直连开发数据库，只能使用开发环境导出的 SQL
- 默认先不同步外键，优先保证结构和数据可覆盖导入

## 第 1 步：开发环境更新导出包

先备份 `database/export/` 下需要保留的历史 SQL，然后清理旧的 `database/export/*.sql`，再执行：

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --output-file "database/export/full_latest.sql"
```

执行完成后，`database/export/` 下保留这两个文件即可：

- `full_latest.sql`：最新完整结构和数据
- `full_latest_foreign_keys.sql`：外键恢复建议

说明：

- `full_latest.sql` 已包含当前库中的表结构和数据，可用于离线覆盖导入
- `full_latest_foreign_keys.sql` 可能是空占位文件；如果当前导出未生成额外外键恢复语句，属于正常现象

## 第 2 步：离线环境一键覆盖同步到目标库

将第 1 步产出的 SQL 文件带到内网环境后，执行：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_latest.sql" --drop-all-first
```

行为说明：

- 目标数据库必须已经提前创建
- 脚本会先清空目标库现有表
- 然后覆盖导入最新结构和数据

## 第 3 步：按需恢复外键

如果本次需要恢复外键，再执行：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --fk-sql-file "database/export/full_latest_foreign_keys.sql" --fk-only
```

说明：

- 这一步是可选的
- `--fk-only` 只执行外键恢复，不会重新导入主 SQL
- 如果 `full_latest_foreign_keys.sql` 是空占位文件，执行后不会补出额外外键
