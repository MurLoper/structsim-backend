# 配置管理系统设计文档

## 1. 系统概述

配置管理系统旨在提供灵活的配置组合机制，让用户在提单时能够快速应用预设的参数组合、工况输出组合等，同时支持自定义修改。

## 2. 核心设计理念

### 2.1 三层配置结构

```
基础配置层 → 组合配置层 → 关联关系层
```

- **基础配置层**：定义原子级配置项（项目、仿真类型、参数、工况、输出、求解器等）
- **组合配置层**：将基础配置组合成可复用的配置组（参数组合、工况输出组合）
- **关联关系层**：管理配置之间的多对多关系，并标记默认配置

### 2.2 默认配置机制

每个仿真类型可以配置：
- **默认参数组合**：提单时自动应用的基础参数
- **默认工况输出组合**：提单时自动应用的工况和输出配置
- **默认求解器**：提单时自动选择的求解器
- **可选组合**：用户可以一键切换的其他预设组合

## 3. 数据模型设计

### 3.1 基础配置表（已存在）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `projects` | 项目表 | id, name, code |
| `sim_types` | 仿真类型表 | id, name, code, category |
| `param_defs` | 参数定义表 | id, name, key, val_type |
| `condition_defs` | 工况定义表 | id, name, code, schema |
| `output_defs` | 输出定义表 | id, name, code, val_type |
| `solvers` | 求解器表 | id, name, code, version |
| `fold_types` | 姿态类型表 | id, name, code, angle |

### 3.2 组合配置表（新增）

#### 3.2.1 参数组合表 `param_groups`

用于将多个参数定义组合成一个可复用的参数组。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(100) | 组合名称，如"基础参数组"、"高级参数组" |
| description | Text | 组合描述 |
| valid | SmallInteger | 是否有效 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |
| updated_at | Integer | 更新时间 |

#### 3.2.2 工况输出组合表 `condition_output_groups`

用于将工况和输出组合成一个可复用的配置组。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(100) | 组合名称，如"标准工况组"、"完整输出组" |
| description | Text | 组合描述 |
| valid | SmallInteger | 是否有效 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |
| updated_at | Integer | 更新时间 |

### 3.3 关联关系表（中间表）

#### 3.3.1 项目-仿真类型关联表 `project_sim_type_rels`

管理项目支持哪些仿真类型，以及每个项目的默认仿真类型。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| project_id | Integer | 项目ID |
| sim_type_id | Integer | 仿真类型ID |
| is_default | SmallInteger | 是否为该项目的默认仿真类型 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

#### 3.3.2 仿真类型-参数组合关联表 `sim_type_param_group_rels`

管理仿真类型支持哪些参数组合，以及默认参数组合。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| sim_type_id | Integer | 仿真类型ID |
| param_group_id | Integer | 参数组合ID |
| is_default | SmallInteger | 是否为该仿真类型的默认参数组合 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

#### 3.3.3 仿真类型-工况输出组合关联表 `sim_type_cond_out_group_rels`

管理仿真类型支持哪些工况输出组合，以及默认组合。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| sim_type_id | Integer | 仿真类型ID |
| cond_out_group_id | Integer | 工况输出组合ID |
| is_default | SmallInteger | 是否为该仿真类型的默认工况输出组合 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

#### 3.3.4 仿真类型-求解器关联表 `sim_type_solver_rels`

管理仿真类型支持哪些求解器，以及默认求解器。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| sim_type_id | Integer | 仿真类型ID |
| solver_id | Integer | 求解器ID |
| is_default | SmallInteger | 是否为该仿真类型的默认求解器 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

#### 3.3.5 参数组合-参数关联表 `param_group_param_rels`

管理参数组合包含哪些参数定义及其默认值。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| param_group_id | Integer | 参数组合ID |
| param_def_id | Integer | 参数定义ID |
| default_value | String(200) | 该参数在此组合中的默认值 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

#### 3.3.6 工况输出组合-工况关联表 `cond_out_group_condition_rels`

管理工况输出组合包含哪些工况定义及其配置。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| cond_out_group_id | Integer | 工况输出组合ID |
| condition_def_id | Integer | 工况定义ID |
| config_data | JSON | 工况配置数据 |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

#### 3.3.7 工况输出组合-输出关联表 `cond_out_group_output_rels`

管理工况输出组合包含哪些输出定义。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| cond_out_group_id | Integer | 工况输出组合ID |
| output_def_id | Integer | 输出定义ID |
| sort | Integer | 排序 |
| created_at | Integer | 创建时间 |

## 4. 业务流程

### 4.1 配置管理流程

#### 4.1.1 创建参数组合

1. 管理员创建参数组合（如"基础参数组"）
2. 选择要包含的参数定义
3. 为每个参数设置默认值
4. 保存参数组合

#### 4.1.2 创建工况输出组合

1. 管理员创建工况输出组合（如"标准工况组"）
2. 选择要包含的工况定义，并配置工况参数
3. 选择要包含的输出定义
4. 保存工况输出组合

#### 4.1.3 配置仿真类型

1. 选择仿真类型
2. 关联多个参数组合，并标记一个为默认
3. 关联多个工况输出组合，并标记一个为默认
4. 关联多个求解器，并标记一个为默认
5. 保存配置

#### 4.1.4 配置项目

1. 选择项目
2. 关联多个仿真类型，并标记一个为默认
3. 保存配置

### 4.2 提单流程

#### 4.2.1 初始化提单

1. 用户选择项目
2. 系统加载该项目的默认仿真类型
3. 系统加载该仿真类型的默认配置：
   - 默认参数组合（自动填充参数值）
   - 默认工况输出组合（自动填充工况和输出）
   - 默认求解器（自动选择求解器）

#### 4.2.2 快速切换配置

1. 用户可以一键切换到其他参数组合
2. 用户可以一键切换到其他工况输出组合
3. 用户可以一键切换到其他求解器
4. 用户可以一键清除当前配置，重新选择

#### 4.2.3 自定义配置

1. 用户可以在预设组合基础上修改参数值
2. 用户可以添加或删除工况
3. 用户可以添加或删除输出
4. 用户可以调整求解器参数

## 5. API 设计

### 5.1 参数组合管理

```
GET    /api/v1/config/param-groups              # 获取参数组合列表
POST   /api/v1/config/param-groups              # 创建参数组合
GET    /api/v1/config/param-groups/:id          # 获取参数组合详情
PUT    /api/v1/config/param-groups/:id          # 更新参数组合
DELETE /api/v1/config/param-groups/:id          # 删除参数组合
GET    /api/v1/config/param-groups/:id/params   # 获取组合包含的参数
POST   /api/v1/config/param-groups/:id/params   # 添加参数到组合
DELETE /api/v1/config/param-groups/:id/params/:param_id  # 从组合移除参数
```

### 5.2 工况输出组合管理

```
GET    /api/v1/config/cond-out-groups           # 获取工况输出组合列表
POST   /api/v1/config/cond-out-groups           # 创建工况输出组合
GET    /api/v1/config/cond-out-groups/:id       # 获取组合详情
PUT    /api/v1/config/cond-out-groups/:id       # 更新组合
DELETE /api/v1/config/cond-out-groups/:id       # 删除组合
GET    /api/v1/config/cond-out-groups/:id/conditions  # 获取组合包含的工况
POST   /api/v1/config/cond-out-groups/:id/conditions  # 添加工况到组合
DELETE /api/v1/config/cond-out-groups/:id/conditions/:cond_id  # 移除工况
GET    /api/v1/config/cond-out-groups/:id/outputs     # 获取组合包含的输出
POST   /api/v1/config/cond-out-groups/:id/outputs     # 添加输出到组合
DELETE /api/v1/config/cond-out-groups/:id/outputs/:output_id  # 移除输出
```

### 5.3 仿真类型配置管理

```
GET    /api/v1/config/sim-types/:id/param-groups      # 获取仿真类型关联的参数组合
POST   /api/v1/config/sim-types/:id/param-groups      # 关联参数组合
PUT    /api/v1/config/sim-types/:id/param-groups/:group_id/default  # 设为默认
DELETE /api/v1/config/sim-types/:id/param-groups/:group_id  # 取消关联

GET    /api/v1/config/sim-types/:id/cond-out-groups   # 获取仿真类型关联的工况输出组合
POST   /api/v1/config/sim-types/:id/cond-out-groups   # 关联工况输出组合
PUT    /api/v1/config/sim-types/:id/cond-out-groups/:group_id/default  # 设为默认
DELETE /api/v1/config/sim-types/:id/cond-out-groups/:group_id  # 取消关联

GET    /api/v1/config/sim-types/:id/solvers           # 获取仿真类型关联的求解器
POST   /api/v1/config/sim-types/:id/solvers           # 关联求解器
PUT    /api/v1/config/sim-types/:id/solvers/:solver_id/default  # 设为默认
DELETE /api/v1/config/sim-types/:id/solvers/:solver_id  # 取消关联
```

### 5.4 项目配置管理

```
GET    /api/v1/config/projects/:id/sim-types          # 获取项目关联的仿真类型
POST   /api/v1/config/projects/:id/sim-types          # 关联仿真类型
PUT    /api/v1/config/projects/:id/sim-types/:sim_type_id/default  # 设为默认
DELETE /api/v1/config/projects/:id/sim-types/:sim_type_id  # 取消关联
```

### 5.5 提单初始化

```
GET    /api/v1/orders/init-config?project_id=1&sim_type_id=2
```

响应示例：
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "project": {
      "id": 1,
      "name": "项目A"
    },
    "simType": {
      "id": 2,
      "name": "结构强度分析"
    },
    "defaultParamGroup": {
      "id": 1,
      "name": "基础参数组",
      "params": [
        {
          "paramDefId": 1,
          "name": "厚度",
          "key": "thickness",
          "defaultValue": "2.5",
          "unit": "mm"
        }
      ]
    },
    "availableParamGroups": [
      {"id": 2, "name": "高级参数组"},
      {"id": 3, "name": "轻量化参数组"}
    ],
    "defaultCondOutGroup": {
      "id": 1,
      "name": "标准工况组",
      "conditions": [...],
      "outputs": [...]
    },
    "availableCondOutGroups": [
      {"id": 2, "name": "完整工况组"}
    ],
    "defaultSolver": {
      "id": 1,
      "name": "ANSYS Mechanical",
      "version": "2023R1"
    },
    "availableSolvers": [
      {"id": 2, "name": "Abaqus"}
    ]
  }
}
```

## 6. 数据库迁移计划

### 6.1 阶段一：创建新表

1. 创建 `param_groups` 表
2. 创建 `condition_output_groups` 表
3. 创建所有关联关系表（7个中间表）

### 6.2 阶段二：数据迁移

1. 将现有 `param_tpl_sets` 和 `param_tpl_items` 数据迁移到新的参数组合表
2. 将现有 `cond_out_sets` 数据迁移到新的工况输出组合表
3. 创建默认关联关系

### 6.3 阶段三：废弃旧表

1. 标记 `param_tpl_sets`、`param_tpl_items`、`cond_out_sets` 为废弃
2. 更新所有引用这些表的代码
3. 在确认无问题后删除旧表

## 7. 前端界面设计

### 7.1 配置管理界面

#### 7.1.1 参数组合管理

- 列表展示所有参数组合
- 创建/编辑参数组合
- 拖拽选择参数定义
- 为每个参数设置默认值

#### 7.1.2 工况输出组合管理

- 列表展示所有工况输出组合
- 创建/编辑工况输出组合
- 选择工况定义并配置参数
- 选择输出定义

#### 7.1.3 仿真类型配置

- 选择仿真类型
- 关联参数组合（多选，标记默认）
- 关联工况输出组合（多选，标记默认）
- 关联求解器（多选，标记默认）

### 7.2 提单界面

#### 7.2.1 初始化视图

- 显示默认参数组合的参数列表
- 显示默认工况输出组合的工况和输出
- 显示默认求解器配置

#### 7.2.2 快速切换

- 下拉选择其他参数组合，一键应用
- 下拉选择其他工况输出组合，一键应用
- 下拉选择其他求解器，一键应用
- "清除配置"按钮，清空当前配置

#### 7.2.3 自定义编辑

- 在预设基础上修改参数值
- 添加/删除工况
- 添加/删除输出
- 调整求解器参数

## 8. 实施步骤

### 第一步：数据库设计与迁移

- [ ] 创建新的数据模型文件
- [ ] 编写数据库迁移脚本
- [ ] 测试数据迁移

### 第二步：后端 API 开发

- [ ] 实现参数组合管理 API
- [ ] 实现工况输出组合管理 API
- [ ] 实现关联关系管理 API
- [ ] 实现提单初始化 API

### 第三步：前端界面开发

- [ ] 开发配置管理界面
- [ ] 开发提单初始化界面
- [ ] 实现快速切换功能
- [ ] 实现自定义编辑功能

### 第四步：测试与优化

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 用户体验优化

## 9. 注意事项

1. **向后兼容**：在迁移过程中保持旧 API 可用，逐步废弃
2. **数据完整性**：确保关联关系的完整性约束
3. **默认配置唯一性**：每个仿真类型只能有一个默认参数组合、一个默认工况输出组合、一个默认求解器
4. **性能优化**：使用缓存减少数据库查询
5. **用户体验**：提供清晰的提示和引导，让用户理解配置组合的概念

## 10. 与现有系统的对比

### 10.1 现有系统

- `param_tpl_sets` + `param_tpl_items`：参数模板集，直接关联到仿真类型
- `cond_out_sets`：工况输出集，直接关联到仿真类型
- 缺少项目与仿真类型的关联管理
- 缺少灵活的多对多关联机制

### 10.2 新系统优势

- **更灵活的组合机制**：参数组合和工况输出组合可以被多个仿真类型复用
- **清晰的关联关系**：通过中间表管理所有多对多关系
- **默认配置支持**：每个关联都可以标记是否为默认
- **更好的扩展性**：易于添加新的配置类型和关联关系
- **项目级配置**：支持项目与仿真类型的关联管理
