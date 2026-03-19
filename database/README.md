# database 目录说明

## 结构关系（清晰版）

- `export_mysql.py`：从**源 MySQL**导出完整 SQL（建表 + 数据）
- `import_mysql.py`：向**目标 MySQL**导入 SQL（自动处理外键检查）
- `migrations/`：结构变更脚本（DDL）
- `init-data/`：种子数据源（JSON）
- `db_manager.py`：初始化/seed/状态检查（把 `init-data` 写入数据库）
- `export/`：导出的 SQL 文件

> 结论：**可用数据同步链路 = migrations →（必要时 seed）→ export_mysql → import_mysql**

---

## 最短执行步骤（只保留必要动作）

1) 在源库先补齐结构（执行 `database/migrations/*.sql`，至少确保 `orders.condition_summary` 存在）

2) 一键跨库同步（可直接复制）

```bash
python database/export_mysql.py --source-db-url "mysql+pymysql://SOURCE_USER:SOURCE_PASS@SOURCE_HOST:3306/SOURCE_DB" --sync-db-url "mysql+pymysql://TARGET_USER:TARGET_PASS@TARGET_HOST:3306/TARGET_DB"
```

3) 验收一个接口：
- `/api/v1/orders?page=1&pageSize=20`

---

## 原理与补救（简版）

- 原理：导出脚本生成“可重放 SQL”，导入脚本在执行时关闭外键检查，避免因表顺序/FK 依赖导致失败。
- 若同步后缺数据：说明源库本身未入库完整（常见是只改了 `init-data`，未执行 seed）；先把数据写入源库，再重新同步。
- 若仍失败：用 `import_mysql.py --continue-on-error` 收集失败语句，再按报错补齐 schema/数据。