# 数据库设计文档

> **版本**: v2.0  
> **最后更新**: 2025-01-18  
> **状态**: ✅ 生产就绪

---

## 📋 目录

1. [数据库概述](#1-数据库概述)
2. [核心表设计](#2-核心表设计)
3. [关系表设计](#3-关系表设计)
4. [索引设计](#4-索引设计)
5. [数据字典](#5-数据字典)

---

## 1. 数据库概述

### 1.1 技术栈

- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0
- **迁移工具**: Alembic (计划中)

### 1.2 命名规范

- **表名**: 小写下划线 (`projects`, `sim_types`)
- **字段名**: 小写下划线 (`created_at`, `default_sim_type_id`)
- **索引名**: `idx_表名_字段名` (`idx_projects_code`)
- **外键名**: `fk_表名_字段名` (`fk_orders_project_id`)

### 1.3 通用字段

所有表都包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT | 主键，自增 |
| `valid` | TINYINT | 是否有效，1=有效，0=禁用 |
| `created_at` | INT | 创建时间戳 |
| `updated_at` | INT | 更新时间戳 |

---

## 2. 核心表设计

### 2.1 项目表 (projects)

**用途**: 存储项目配置信息

```sql
CREATE TABLE projects (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL COMMENT '项目名称',
  code VARCHAR(50) UNIQUE COMMENT '项目编码',
  default_sim_type_id INT COMMENT '默认仿真类型ID',
  default_solver_id INT COMMENT '默认求解器ID',
  valid TINYINT DEFAULT 1 COMMENT '1=有效,0=禁用',
  sort INT DEFAULT 100 COMMENT '排序',
  remark TEXT COMMENT '备注',
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_projects_code (code),
  INDEX idx_projects_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目表';
```

**字段说明**:
- `name`: 项目名称，必填
- `code`: 项目编码，唯一标识
- `default_sim_type_id`: 默认仿真类型，外键关联 `sim_types.id`
- `default_solver_id`: 默认求解器，外键关联 `solvers.id`

---

### 2.2 仿真类型表 (sim_types)

**用途**: 存储仿真类型配置

```sql
CREATE TABLE sim_types (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '仿真类型名称',
  code VARCHAR(50) UNIQUE COMMENT '类型编码',
  category VARCHAR(50) COMMENT '分类: STRUCTURE/THERMAL/MODAL等',
  default_param_tpl_set_id INT COMMENT '默认参数模板集ID',
  default_cond_out_set_id INT COMMENT '默认工况输出集ID',
  default_solver_id INT COMMENT '默认求解器ID',
  support_alg_mask INT DEFAULT 0 COMMENT '支持的算法掩码: 1=DOE,2=Bayesian,3=Both',
  node_icon VARCHAR(100) COMMENT '节点图标',
  color_tag VARCHAR(20) COMMENT '颜色标签',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  remark TEXT,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_sim_types_code (code),
  INDEX idx_sim_types_category (category),
  INDEX idx_sim_types_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='仿真类型表';
```

**字段说明**:
- `support_alg_mask`: 位掩码，1=DOE，2=贝叶斯，3=两者都支持
- `node_icon`: React Flow 节点图标路径
- `color_tag`: 节点颜色标签 (如: #FF5500)

---

### 2.3 参数定义表 (param_defs)

**用途**: 全局参数定义

```sql
CREATE TABLE param_defs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '参数名称',
  `key` VARCHAR(50) NOT NULL UNIQUE COMMENT '参数键名',
  val_type TINYINT DEFAULT 1 COMMENT '1=number,2=int,3=string,4=enum,5=bool',
  unit VARCHAR(20) COMMENT '单位',
  min_val FLOAT COMMENT '最小值',
  max_val FLOAT COMMENT '最大值',
  precision TINYINT DEFAULT 3 COMMENT '精度',
  default_val VARCHAR(100) COMMENT '默认值',
  enum_options JSON COMMENT '枚举选项列表',
  required TINYINT DEFAULT 1 COMMENT '是否必填',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  remark TEXT,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_param_defs_key (`key`),
  INDEX idx_param_defs_val_type (val_type),
  INDEX idx_param_defs_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参数定义表';
```

**字段说明**:
- `val_type`: 1=浮点数，2=整数，3=字符串，4=枚举，5=布尔
- `enum_options`: JSON 数组，如 `["Steel_1040", "Alum_6061"]`
- `precision`: 数值精度，小数点后位数

---

### 2.4 求解器表 (solvers)

**用途**: 求解器配置

```sql
CREATE TABLE solvers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '求解器名称',
  code VARCHAR(50) UNIQUE COMMENT '求解器编码',
  version VARCHAR(20) COMMENT '版本号',
  cpu_core_min INT DEFAULT 1 COMMENT 'CPU最小核数',
  cpu_core_max INT DEFAULT 64 COMMENT 'CPU最大核数',
  cpu_core_default INT DEFAULT 4 COMMENT 'CPU默认核数',
  memory_min INT DEFAULT 1 COMMENT '内存最小值(GB)',
  memory_max INT DEFAULT 256 COMMENT '内存最大值(GB)',
  memory_default INT DEFAULT 8 COMMENT '内存默认值(GB)',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  remark TEXT,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_solvers_code (code),
  INDEX idx_solvers_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='求解器表';
```

---

### 2.5 工况定义表 (condition_defs)

**用途**: 工况定义

```sql
CREATE TABLE condition_defs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '工况名称',
  `key` VARCHAR(50) NOT NULL UNIQUE COMMENT '工况键名',
  cond_type TINYINT DEFAULT 1 COMMENT '1=载荷,2=约束,3=温度,4=压力',
  unit VARCHAR(20) COMMENT '单位',
  min_val FLOAT COMMENT '最小值',
  max_val FLOAT COMMENT '最大值',
  default_val VARCHAR(100) COMMENT '默认值',
  required TINYINT DEFAULT 1,
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  remark TEXT,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_condition_defs_key (`key`),
  INDEX idx_condition_defs_type (cond_type),
  INDEX idx_condition_defs_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况定义表';
```

---

### 2.6 输出定义表 (output_defs)

**用途**: 输出结果定义

```sql
CREATE TABLE output_defs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '输出名称',
  `key` VARCHAR(50) NOT NULL UNIQUE COMMENT '输出键名',
  out_type TINYINT DEFAULT 1 COMMENT '1=标量,2=向量,3=矩阵,4=文件',
  unit VARCHAR(20) COMMENT '单位',
  precision TINYINT DEFAULT 3 COMMENT '精度',
  required TINYINT DEFAULT 1,
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  remark TEXT,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_output_defs_key (`key`),
  INDEX idx_output_defs_type (out_type),
  INDEX idx_output_defs_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='输出定义表';
```

---

### 2.7 姿态类型表 (fold_types)

**用途**: 姿态类型定义

```sql
CREATE TABLE fold_types (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '姿态名称',
  code VARCHAR(50) UNIQUE COMMENT '姿态编码',
  description TEXT COMMENT '描述',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  remark TEXT,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_fold_types_code (code),
  INDEX idx_fold_types_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='姿态类型表';
```

---

## 3. 关系表设计

### 3.1 参数模板集表 (param_tpl_sets)

**用途**: 参数模板集（参数组合）

```sql
CREATE TABLE param_tpl_sets (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '模板集名称',
  sim_type_id INT NOT NULL COMMENT '仿真类型ID',
  description TEXT COMMENT '描述',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_param_tpl_sets_sim_type (sim_type_id),
  INDEX idx_param_tpl_sets_valid (valid),
  FOREIGN KEY (sim_type_id) REFERENCES sim_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参数模板集表';
```

### 3.2 参数模板集关联表 (param_tpl_set_rels)

**用途**: 参数模板集与参数定义的多对多关系

```sql
CREATE TABLE param_tpl_set_rels (
  id INT PRIMARY KEY AUTO_INCREMENT,
  param_tpl_set_id INT NOT NULL COMMENT '参数模板集ID',
  param_def_id INT NOT NULL COMMENT '参数定义ID',
  created_at INT NOT NULL,
  
  UNIQUE KEY uk_set_param (param_tpl_set_id, param_def_id),
  INDEX idx_param_tpl_set_rels_set (param_tpl_set_id),
  INDEX idx_param_tpl_set_rels_param (param_def_id),
  FOREIGN KEY (param_tpl_set_id) REFERENCES param_tpl_sets(id) ON DELETE CASCADE,
  FOREIGN KEY (param_def_id) REFERENCES param_defs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参数模板集关联表';
```

---

### 3.3 工况输出集表 (cond_out_sets)

**用途**: 工况输出集（工况和输出的组合）

```sql
CREATE TABLE cond_out_sets (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '工况输出集名称',
  sim_type_id INT NOT NULL COMMENT '仿真类型ID',
  description TEXT COMMENT '描述',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_cond_out_sets_sim_type (sim_type_id),
  INDEX idx_cond_out_sets_valid (valid),
  FOREIGN KEY (sim_type_id) REFERENCES sim_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况输出集表';
```

### 3.4 工况输出集关联表 (cond_out_set_rels)

**用途**: 工况输出集与工况/输出定义的关系

```sql
CREATE TABLE cond_out_set_rels (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cond_out_set_id INT NOT NULL COMMENT '工况输出集ID',
  rel_type TINYINT NOT NULL COMMENT '1=工况,2=输出',
  rel_id INT NOT NULL COMMENT '关联ID(condition_def_id或output_def_id)',
  created_at INT NOT NULL,
  
  UNIQUE KEY uk_set_type_rel (cond_out_set_id, rel_type, rel_id),
  INDEX idx_cond_out_set_rels_set (cond_out_set_id),
  INDEX idx_cond_out_set_rels_type_rel (rel_type, rel_id),
  FOREIGN KEY (cond_out_set_id) REFERENCES cond_out_sets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况输出集关联表';
```

---

### 3.5 参数组表 (param_groups)

**用途**: 参数分组（用于前端展示）

```sql
CREATE TABLE param_groups (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '参数组名称',
  description TEXT COMMENT '描述',
  valid TINYINT DEFAULT 1,
  sort INT DEFAULT 100,
  created_at INT NOT NULL,
  updated_at INT NOT NULL,
  
  INDEX idx_param_groups_valid (valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参数组表';
```

### 3.6 参数组关联表 (param_group_param_rels)

**用途**: 参数组与参数定义的多对多关系

```sql
CREATE TABLE param_group_param_rels (
  id INT PRIMARY KEY AUTO_INCREMENT,
  param_group_id INT NOT NULL COMMENT '参数组ID',
  param_def_id INT NOT NULL COMMENT '参数定义ID',
  created_at INT NOT NULL,
  
  UNIQUE KEY uk_group_param (param_group_id, param_def_id),
  INDEX idx_param_group_param_rels_group (param_group_id),
  INDEX idx_param_group_param_rels_param (param_def_id),
  FOREIGN KEY (param_group_id) REFERENCES param_groups(id) ON DELETE CASCADE,
  FOREIGN KEY (param_def_id) REFERENCES param_defs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参数组关联表';
```

---

## 4. 索引设计

### 4.1 主键索引

所有表都有主键索引 `PRIMARY KEY (id)`

### 4.2 唯一索引

| 表名 | 字段 | 说明 |
|------|------|------|
| projects | code | 项目编码唯一 |
| sim_types | code | 仿真类型编码唯一 |
| param_defs | key | 参数键名唯一 |
| solvers | code | 求解器编码唯一 |
| condition_defs | key | 工况键名唯一 |
| output_defs | key | 输出键名唯一 |
| fold_types | code | 姿态编码唯一 |

### 4.3 普通索引

| 表名 | 字段 | 说明 |
|------|------|------|
| 所有表 | valid | 查询有效记录 |
| sim_types | category | 按分类查询 |
| param_defs | val_type | 按类型查询 |
| condition_defs | cond_type | 按工况类型查询 |
| output_defs | out_type | 按输出类型查询 |

### 4.4 外键索引

所有外键字段都自动创建索引

---

## 5. 数据字典

### 5.1 参数值类型 (val_type)

| 值 | 说明 | 示例 |
|----|------|------|
| 1 | 浮点数 | 1.23 |
| 2 | 整数 | 100 |
| 3 | 字符串 | "text" |
| 4 | 枚举 | "Steel_1040" |
| 5 | 布尔 | true/false |

### 5.2 算法支持掩码 (support_alg_mask)

| 值 | 说明 |
|----|------|
| 0 | 不支持 |
| 1 | 仅 DOE |
| 2 | 仅贝叶斯 |
| 3 | DOE + 贝叶斯 |

### 5.3 工况类型 (cond_type)

| 值 | 说明 |
|----|------|
| 1 | 载荷 |
| 2 | 约束 |
| 3 | 温度 |
| 4 | 压力 |

### 5.4 输出类型 (out_type)

| 值 | 说明 |
|----|------|
| 1 | 标量 |
| 2 | 向量 |
| 3 | 矩阵 |
| 4 | 文件 |

---

**最后更新**: 2025-01-18  
**维护者**: 后端团队
