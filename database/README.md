# database 目录说明

当前目录只保留离线同步口径，和 `database/MIGRATION.md` 保持一致。

## 核心脚本

- `export_mysql.py`：从开发环境导出最新完整库，生成 `full_latest.sql`
- `import_mysql.py`：向目标库导入主 SQL，或单独执行外键恢复
- `export/`：导出目录，保存本次要交付到内网环境的 SQL 文件
- `migrations/`：保留历史补库脚本，仅在需要手工排障时参考

## 离线同步 3 步

### 第 1 步：开发环境更新导出包

先备份 `database/export/` 下需要保留的历史 SQL，再清理旧的 `database/export/*.sql`，然后执行：

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --output-file "database/export/full_latest.sql"
```

执行完成后，交付这两个文件即可：

- `database/export/full_latest.sql`
- `database/export/full_latest_foreign_keys.sql`

### 第 2 步：离线环境覆盖导入到目标库

目标数据库需要提前创建好。将第 1 步生成的 SQL 带到内网环境后执行：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --sql-file "database/export/full_latest.sql" --drop-all-first
```

### 第 3 步：按需恢复外键

如果本次需要恢复外键，再执行：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --fk-sql-file "database/export/full_latest_foreign_keys.sql" --fk-only
```

## 说明

- 默认以“先完成结构和数据覆盖导入”为主，不强制恢复外键
- `full_latest_foreign_keys.sql` 可能是空占位文件；如果当前导出未生成额外外键恢复语句，属于正常现象
- 更详细的说明见 `database/MIGRATION.md`
