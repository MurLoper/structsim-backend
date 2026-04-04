# 外部数据接入说明

## 1. 接入目标

当前后端通过同一台 MySQL 5.6 实例的多个 schema，补齐以下能力：

- 提交页项目阶段
- 输出后处理 `component` 字典
- 结果分析中的外部优化任务聚合

## 2. 外部实例

- Host：`154.9.255.18`
- Port：`3306`
- 连接方式：只读查询

配置项：

- `EXTERNAL_MYSQL_HOST`
- `EXTERNAL_MYSQL_PORT`
- `EXTERNAL_MYSQL_USER`
- `EXTERNAL_MYSQL_PASSWORD`
- `EXTERNAL_MYSQL_SCHEMA_SIMLATION_PROJECT`
- `EXTERNAL_MYSQL_SCHEMA_STRUCT_MODULE`
- `EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL`
- `EXTERNAL_MYSQL_SCHEMA_UNION_OPT_CONF`
- `EXTERNAL_MYSQL_SCHEMA_SQRS_HW`

## 3. schema 与用途

### 3.1 `simlation_project`

- `phase`
  - 阶段字典
  - 当前使用字段：`phase_id`、`phase_desc`
- `pp_phase`
  - `project_id -> phase_id` 映射
  - 当前使用字段：`pp_phase_id`、`pp_record_id`、`phase_id`

后端规则：

- 项目阶段下拉来自 `phase`
- 默认阶段通过 `pp_phase.pp_record_id = project_id` 查出 `phase_id`
- 若项目未命中映射，则返回空默认值，前端允许用户手动选择

### 3.2 `struct_module`

- `component`
  - 输出后处理 `component` 字典来源
  - 当前使用字段：`id`、`component`

后端对外统一映射为：

- `code`
- `name`
- `is_default`
- `source`
- `remark`

### 3.3 `union_opt_kernal`

- `opt_issues`
  - 订单级外部优化任务
  - 通过 `orders.opt_issue_id` 关联
- `jobs`
  - 工况级外部任务
  - 通过 `order_condition_opti.opt_job_id` 关联
- `opt_circles`
  - 轮次摘要
- `opt_data`
  - 轮次内数据明细
- `post_data_save`
  - 输出结果摘要
- `resp_config`
  - 响应配置补充信息

## 4. 本地表关联口径

当前只做字段关联，不加外键：

- `orders.phase_id`
- `orders.opt_issue_id`
- `order_condition_opti.opt_job_id`

对应关系：

- `orders.phase_id`：提交时选中的项目阶段
- `orders.opt_issue_id -> union_opt_kernal.opt_issues.id`
- `order_condition_opti.opt_job_id -> union_opt_kernal.jobs.id`

## 5. 结果分析最小闭环

当前结果分析只接最小闭环，不做全库广关联：

- 订单级：`opt_issues`
- 工况级：`jobs`
- 轮次级：`opt_circles`
- 输出摘要：`post_data_save + resp_config`

外部结果缺失时，后端降级回本地 mock / 空结果，不阻断页面。

## 6. 阶段映射示例数据

当前仓库内置了一个可重复执行的示例脚本：

- [`database/migrations/seed_pp_phase_sample.py`](../../database/migrations/seed_pp_phase_sample.py)

脚本行为：

1. 从本地主库读取 `projects.id`
2. 从外部 `simlation_project.phase` 读取可用 `phase_id`
3. 对尚未存在映射的项目，按稳定顺序轮询分配阶段
4. 不覆盖已有的 `pp_phase` 数据

执行方式：

```bash
venv\Scripts\python database\migrations\seed_pp_phase_sample.py --dry-run
venv\Scripts\python database\migrations\seed_pp_phase_sample.py
```

当前已生成一批测试映射：

- `1751 -> 1`
- `1752 -> 2`
- `1753 -> 3`
- `1754 -> 1`
- `1755 -> 2`
- `1756 -> 3`
- `1757 -> 1`
- `1758 -> 2`
- `1759 -> 3`
- `1760 -> 1`

## 7. 约束

- 不对外部库做迁移
- 不写回外部优化库
- 不建立跨库外键
- 所有查询必须兼容 MySQL 5.6
- 不使用 CTE、窗口函数、8.x 专属 JSON 语法
