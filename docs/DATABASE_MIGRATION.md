# 数据库初始化和迁移指南

## 概述

本文档提供数据库初始化、迁移和数据同步的完整指南，确保项目在不同环境中的数据库结构一致性。

## 数据库结构

### 核心表（30个）

#### 1. 权限管理表
- `users` - 用户表
- `roles` - 角色表
- `permissions` - 权限表
- `menus` - 菜单表

#### 2. 配置表
- `projects` - 项目配置
- `sim_types` - 仿真类型
- `param_defs` - 参数定义
- `condition_defs` - 工况定义
- `output_defs` - 输出定义
- `solvers` - 求解器配置
- `workflows` - 工作流定义
- `status_defs` - 状态定义
- `automation_modules` - 自动化模块
- `fold_types` - 折叠类型
- `param_groups` - 参数分组
- `condition_output_groups` - 工况输出分组

#### 3. 模板和集合表
- `param_tpl_sets` - 参数模板集
- `param_tpl_items` - 参数模板项
- `cond_out_sets` - 工况输出集

#### 4. 关联表（多对多）
- `project_sim_type_rels` - 项目-仿真类型关联
- `sim_type_param_group_rels` - 仿真类型-参数分组关联
- `sim_type_cond_out_group_rels` - 仿真类型-工况输出分组关联
- `sim_type_solver_rels` - 仿真类型-求解器关联
- `param_group_param_rels` - 参数分组-参数关联
- `cond_out_group_condition_rels` - 工况输出分组-工况关联
- `cond_out_group_output_rels` - 工况输出分组-输出关联

#### 5. 业务表
- `orders` - 订单/申请单
- `sim_type_results` - 仿真类型结果
- `rounds` - 轮次数据
- `order_results` - 订单结果（预留）

---

## 快速开始

### 1. 新环境初始化

```bash
# 进入后端目录
cd structsim-backend

# 激活虚拟环境
source ../.venv/bin/activate  # Linux/Mac
# 或
..\.venv\Scripts\Activate.ps1  # Windows

# 初始化数据库结构
python init_database.py --init

# 填充测试数据
python init_database.py --seed

# 或者一步完成
python init_database.py --init --seed
```

### 2. 检查数据库状态

```bash
python init_database.py --check
```

输出示例：
```
✓ 数据库连接正常
数据库表数量: 30
✓ 所有关键表都存在

数据统计:
  - 用户 (users): 4 条
  - 订单 (orders): 25 条
  - 项目 (projects): 5 条
  - 仿真类型 (sim_types): 6 条
  - 仿真结果 (sim_type_results): 18 条
  - 轮次数据 (rounds): 215 条
```

---

## 数据初始化工具

### init_database.py

统一的数据库管理工具，支持以下操作：

```bash
# 查看帮助
python init_database.py --help

# 初始化数据库结构（创建所有表）
python init_database.py --init

# 填充测试数据
python init_database.py --seed

# 初始化并填充数据
python init_database.py --init --seed

# 重置数据库（危险操作，会删除所有数据）
python init_database.py --reset

# 检查数据库状态
python init_database.py --check

# 导出数据库结构
python init_database.py --export-schema
```

### seed.py

数据填充脚本，包含：

**配置数据：**
- 5个项目（车身结构、底盘系统、动力总成、电池包、整车集成）
- 6个仿真类型（静态强度、模态分析、疲劳分析、碰撞安全、NVH分析、热管理）
- 20+个参数定义
- 4个工况定义
- 6个输出定义
- 3个求解器
- 2个工作流
- 5个状态定义

**用户数据：**
- Alice Admin (alice@sim.com) - 管理员
- Bob Engineer (bob@sim.com) - 工程师
- Charlie Viewer (charlie@sim.com) - 查看者
- Guest (guest@sim.com) - 访客

**业务数据：**
- 25个测试订单
- 18个仿真结果（仅为已完成订单）
- 215个轮次数据（每个仿真结果5-15轮）

---

## 数据库迁移流程

### 场景1：开发环境 → 测试环境

```bash
# 1. 在开发环境导出数据库结构
mysqldump -u root -p --no-data sim_ai_paltform > schema.sql

# 2. 在测试环境导入结构
mysql -u root -p sim_ai_paltform < schema.sql

# 3. 填充测试数据
python init_database.py --seed
```

### 场景2：测试环境 → 生产环境

```bash
# 1. 导出完整数据（包含业务数据）
mysqldump -u root -p sim_ai_paltform > full_backup.sql

# 2. 在生产环境导入
mysql -u root -p sim_ai_paltform < full_backup.sql

# 注意：生产环境不要运行 --seed，避免覆盖真实数据
```

### 场景3：结构变更迁移

当模型定义发生变化时：

```bash
# 1. 更新模型文件（app/models/*.py）

# 2. 在开发环境测试
python init_database.py --reset  # 重置数据库
python init_database.py --init --seed  # 重新初始化

# 3. 创建迁移SQL脚本
# 将结构变更保存到 migrations/ 目录
# 例如：migrations/add_new_field_20260121.sql

# 4. 在其他环境执行迁移脚本
mysql -u root -p sim_ai_paltform < migrations/add_new_field_20260121.sql
```

---

## 数据删除顺序

由于外键约束，删除数据必须按以下顺序：

```python
# 1. 结果数据（最底层）
Round → SimTypeResult

# 2. 订单数据
Order

# 3. 关联表（多对多）
project_sim_type_rels
sim_type_param_group_rels
sim_type_cond_out_group_rels
sim_type_solver_rels
param_group_param_rels
cond_out_group_condition_rels
cond_out_group_output_rels

# 4. 配置数据
ParamTplItem → ParamTplSet
CondOutSet
param_groups
condition_output_groups

# 5. 主配置表
Project, SimType, ParamDef, ConditionDef, OutputDef
Solver, Workflow, StatusDef, AutomationModule, FoldType

# 6. 权限数据
Menu → Permission → Role → User
```

---

## 常见问题

### Q1: 外键约束错误

**错误信息：**
```
IntegrityError: Cannot delete or update a parent row: a foreign key constraint fails
```

**解决方案：**
按照正确的删除顺序操作，或使用 `init_database.py --reset` 重置数据库。

### Q2: 表已存在错误

**错误信息：**
```
Table 'xxx' already exists
```

**解决方案：**
```bash
# 检查数据库状态
python init_database.py --check

# 如果需要重新创建，使用reset
python init_database.py --reset
```

### Q3: 数据不一致

**解决方案：**
```bash
# 重新填充数据
python init_database.py --seed
```

---

## 生产环境注意事项

### ⚠️ 危险操作

以下操作会删除所有数据，**生产环境禁止使用**：

```bash
# 危险！会删除所有数据
python init_database.py --reset

# 危险！会覆盖现有数据
python init_database.py --seed
```

### ✅ 安全操作

生产环境推荐操作：

```bash
# 1. 仅检查状态
python init_database.py --check

# 2. 备份数据
mysqldump -u root -p sim_ai_paltform > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. 执行迁移前先测试
mysql -u root -p test_db < migration.sql

# 4. 确认无误后再在生产环境执行
mysql -u root -p sim_ai_paltform < migration.sql
```

---

## 数据库配置

### 开发环境

```python
# config.py
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/sim_ai_paltform'
```

### 生产环境

```python
# 使用环境变量
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
```

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0 | 2026-01-21 | 初始版本，包含30个表 |
| 1.1 | 2026-01-21 | 添加结果数据生成（SimTypeResult, Round） |
| 1.2 | 2026-01-21 | 修复外键约束问题，优化删除顺序 |

---

## 相关文件

- `init_database.py` - 数据库初始化工具
- `seed.py` - 数据填充脚本
- `app/models/` - 数据模型定义
- `migrations/` - 数据库迁移脚本目录
- `config.py` - 数据库配置

---

## 技术支持

如遇问题，请检查：
1. 数据库连接配置是否正确
2. MySQL服务是否运行
3. 用户权限是否足够
4. 数据库版本是否兼容（推荐MySQL 5.7+）

更多信息请参考：
- [项目文档](../docs/README.md)
- [API文档](../docs/api/README.md)
- [架构设计](../docs/architecture/README.md)

