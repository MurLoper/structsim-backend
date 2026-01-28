# StructSim 数据库管理

本目录包含数据库初始化、迁移和管理所需的所有文件。

## 支持的数据库

- **SQLite** (默认，开发/测试环境)
- **MySQL** (生产环境)

脚本会自动检测当前配置的数据库类型，使用对应的 SQL 语法。

## 目录结构

```
database/
├── db_manager.py        # 统一数据库管理工具
├── init-data/           # 初始化数据文件
│   ├── base_config.json # 基础配置（项目、仿真类型、状态定义等）
│   ├── users.json       # 用户、角色、权限、部门
│   ├── param_groups.json # 参数组配置
│   └── relative_config.json # 关联配置
├── migrations/          # 数据库迁移脚本
│   ├── add_icon_to_status_defs.sql
│   └── migrate_status_config.py
└── README.md
```

## 快速开始

### 首次安装（创建数据库并导入数据）

```bash
cd structsim-backend
python database/db_manager.py reset -f
```

### 查看数据库状态

```bash
python database/db_manager.py status
```

## 命令说明

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 创建数据库表结构 | `python database/db_manager.py init` |
| `seed` | 导入初始数据 | `python database/db_manager.py seed` |
| `clean` | 清理所有数据 | `python database/db_manager.py clean` |
| `reset` | 重置数据库（清理+创建+导入） | `python database/db_manager.py reset` |
| `status` | 查看数据库状态 | `python database/db_manager.py status` |

### 参数选项

| 参数 | 说明 |
|------|------|
| `-f, --force` | 强制执行，不提示确认 |

## 数据统计

| 数据类型 | 数量 | 说明 |
|---------|------|------|
| 项目 | 10 | 折叠屏手机、平板、手表等 |
| 仿真类型 | 5 | 跌落、落球、振动、冲击、热分析 |
| 模型层级 | 3 | 整机、单件、部件 |
| 折叠状态 | 3 | 展开态、折叠态、半折叠态 |
| 参数定义 | 20 | 姿态、材料、温度等参数 |
| 输出定义 | 11 | 位移、反力、应力、温度等 |
| 求解器 | 5 | GPU求解器、Abaqus、LS-DYNA、ANSYS |
| 状态定义 | 8 | 未开始、运行中、已完成、失败等（含icon） |
| 用户 | 10 | 管理员、工程师、测试等 |
| 角色 | 5 | 超级管理员、项目经理、开发、测试、产品 |
| 权限 | 8 | 查看仪表盘、管理配置、创建工单等 |

## 状态配置

系统支持 8 种运行状态（含图标和颜色）：

| ID | 名称 | 代码 | 类型 | 颜色 | 图标 |
|----|------|------|------|------|------|
| 0 | 未开始 | NOT_STARTED | PROCESS | #808080 | icon-weikaishi |
| 1 | 运行中 | RUNNING | PROCESS | #0000FF | icon-yunxingzhong |
| 2 | 已完成 | COMPLETED | FINAL | #008000 | icon-yiwancheng |
| 3 | 运行失败 | FAILED | FINAL | #FF0000 | icon-yunxingshibai |
| 4 | 草稿箱 | DRAFT | PROCESS | #0000FF | icon-caogaoxiang |
| 5 | 手动终止 | CANCELLED | FINAL | #FFA500 | icon-shoudongzhongzhi |
| 6 | 启动中 | STARTING | PROCESS | #800080 | icon-qidongzhong |
| 7 | 小模块完成 | PARTIAL_COMPLETED | PROCESS | #0000FF | icon-xiaomokuaiwancheng |

## 测试用户

| 用户名 | 邮箱 | 角色 | 说明 |
|-------|------|------|------|
| admin | admin@example.com | 超级管理员 | 拥有所有权限 |
| zhangsan | zhangsan@example.com | 项目经理 | 项目管理权限 |
| lisi | lisi@example.com | 开发工程师 | 开发相关权限 |
| wangwu | wangwu@example.com | 测试工程师 | 测试相关权限 |
| sunqi | sunqi@example.com | 产品经理 | 产品相关权限 |

## 数据库迁移

对于生产环境的增量迁移，使用 `migrations/` 目录下的脚本：

```bash
# 执行状态配置迁移（添加icon字段）
python database/migrations/migrate_status_config.py
```

## 常见问题

### Q: 数据库连接失败？

检查 `.env` 或 `config.py` 中的数据库配置：

```python
# SQLite (默认)
SQLALCHEMY_DATABASE_URI = 'sqlite:///structsim.db'

# MySQL
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@localhost/structsim'
```

### Q: 如何使用 SQLite 进行本地测试？

默认配置已使用 SQLite，直接运行即可：

```bash
python database/db_manager.py reset -f
```

### Q: 如何完全重置数据库？

```bash
python database/db_manager.py reset -f
```

### Q: 如何添加新的初始数据？

1. 编辑 `init-data/` 目录下的 JSON 文件
2. 运行 `python database/db_manager.py reset -f` 重新导入

## 相关文档

- [后端 API 文档](../docs/api/)
- [状态配置系统文档](../../docs/STATUS_CONFIG_SYSTEM.md)

