# MySQL 同步手册（精简）

## 一条最终命令（推荐）

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --sync-db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB"
```

> 该命令会：先导出源库完整 SQL，再自动导入目标库。

---

## 执行前仅检查两件事

1. 源库是你刚测试通过的数据源。
2. 源库已执行必要迁移（如 `database/migrations/add_condition_summary.sql`）。

---

## 失败时补救

- 外键/顺序问题：使用 `database/import_mysql.py`（脚本已自动开关 `FOREIGN_KEY_CHECKS`）。
- 局部语句失败排查：

```bash
python database/import_mysql.py --db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB" --latest --continue-on-error
```

- 导入后数据不全：先确认源库已把 `init-data` 对应数据真实入库（必要时执行 `python database/db_manager.py seed`），再重新同步。