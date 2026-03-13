# 数据库管理工具

## 目录结构

```
database/
├── schemas/          # 表结构定义（JSON格式）
├── data/            # 基础数据（JSON格式）
├── migrations/      # 数据库迁移脚本
├── sync_database.py # 数据库同步工具
├── one_click_sync.py # 一键同步脚本
└── init_data.py     # 数据初始化脚本
```

## 使用说明

### 1. 导出当前数据库结构

```bash
python database/sync_database.py export
```

导出结果保存在 `database/schemas/` 目录

### 2. 一键同步数据库（推荐）

```bash
python database/one_click_sync.py
```

功能：
- 检查表是否存在，不存在则创建
- 自动兼容 SQLite 和 MySQL
- 显示同步进度和结果

### 3. 初始化基础数据

```bash
python database/init_data.py
```

从 `database/data/` 目录导入配置数据

## MySQL 切换步骤

1. 修改 `.env` 配置：

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/structsim
```

2. 安装 MySQL 驱动：

```bash
pip install pymysql
```

3. 运行同步脚本：

```bash
python database/one_click_sync.py
```

4. 导入数据（可选）：

```bash
python database/init_data.py
```

## 注意事项

- 脚本自动处理 SQLite 和 MySQL 的语法差异
- MySQL 使用 InnoDB 引擎和 utf8mb4 字符集
- 已存在的表不会被覆盖
- 数据导入会跳过已有数据的表
