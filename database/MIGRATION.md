# 数据库迁移指南

## 概述

本指南用于将 StructSim AI Platform 数据库从外网环境迁移到内网环境。

## 前置条件

- Python 3.8+
- MySQL 5.7+ 或 8.0+
- 已安装依赖：`pip install sqlalchemy pymysql`

## 迁移步骤

### 1. 导出数据库（外网环境）

在外网服务器上运行导出脚本：

```bash
cd structsim-backend
python database/export_mysql.py
```

导出的SQL文件位于：`database/export/database_export_YYYYMMDD_HHMMSS.sql`

### 2. 传输文件到内网

将导出的SQL文件复制到内网服务器：

```bash
# 使用scp或其他文件传输工具
scp database/export/database_export_*.sql user@internal-server:/path/to/structsim-backend/database/
```

### 3. 准备内网数据库

在内网MySQL服务器上创建数据库：

```sql
CREATE DATABASE sim_ai_paltform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sim_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON sim_ai_paltform.* TO 'sim_user'@'%';
FLUSH PRIVILEGES;
```

### 4. 导入数据库（内网环境）

在内网服务器上运行导入脚本：

```bash
cd structsim-backend
python database/import_mysql.py database/database_export_YYYYMMDD_HHMMSS.sql \
  --db-url "mysql+pymysql://sim_user:your_password@localhost:3306/sim_ai_paltform"
```

### 5. 更新配置文件

修改内网服务器的 `.env` 文件：

```bash
# 更新数据库连接
DATABASE_URL=mysql+pymysql://sim_user:your_password@localhost:3306/sim_ai_paltform
```

### 6. 验证迁移

启动应用并验证：

```bash
# 启动后端
python run.py

# 检查数据库连接
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('Tables:', db.engine.table_names())"
```

## 常见问题

### Q: 导入时报外键约束错误？
A: SQL文件已包含 `SET FOREIGN_KEY_CHECKS=0`，如仍有问题，手动执行该语句。

### Q: 字符编码问题？
A: 确保数据库和表都使用 `utf8mb4` 字符集。

### Q: 导入速度慢？
A: 可以在导入前临时调整MySQL配置：
```sql
SET GLOBAL max_allowed_packet=1073741824;
SET GLOBAL innodb_buffer_pool_size=2147483648;
```

## 脚本说明

### export_mysql.py
- 导出完整的数据库结构和数据
- 生成标准SQL文件
- 自动处理字符转义

### import_mysql.py
- 导入SQL文件到目标数据库
- 支持自定义数据库连接
- 显示导入进度

## 注意事项

1. 导出前确保数据库连接正常
2. 传输文件时注意文件大小限制
3. 导入前备份目标数据库
4. 验证数据完整性后再切换生产环境
