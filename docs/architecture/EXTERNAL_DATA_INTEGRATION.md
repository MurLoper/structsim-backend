# 外部数据接入说明

最后更新：2026-04-13

## 1. 接入边界

后端通过同一台 MySQL 5.6 实例读取多个外部 schema，用于项目阶段、输出后处理组件、自动化提单结果聚合。

固定原则：
- 外部库默认只读，生产提单路径不直接写外部库。
- 测试和演示数据只通过独立 mock 脚本写入。
- 不建立跨库外键。
- 查询必须兼容 MySQL 5.6，不使用 CTE、窗口函数和 MySQL 8 专属 JSON 语法。

## 2. 配置项

共享连接配置：
- `EXTERNAL_MYSQL_HOST`
- `EXTERNAL_MYSQL_PORT`
- `EXTERNAL_MYSQL_USER`
- `EXTERNAL_MYSQL_PASSWORD`

schema 配置：
- `EXTERNAL_MYSQL_SCHEMA_SIMULATION_PROJECT=simulation_project`
- `EXTERNAL_MYSQL_SCHEMA_STRUCT_MODULE=struct_module`
- `EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL=union_opt_kernal`
- `EXTERNAL_MYSQL_SCHEMA_UNION_OPT_CONF=union_opt_conf`
- `EXTERNAL_MYSQL_SCHEMA_SQRS_HW=sqrs_hw`

旧配置 `EXTERNAL_MYSQL_SCHEMA_SIMLATION_PROJECT` 已废弃并删除，不再做 fallback。

## 3. 项目阶段

来源 schema：`simulation_project`

使用表：
- `phase`：阶段字典。
- `pp_phase`：项目与阶段映射。

规则：
- 阶段列表从当前项目在 `pp_phase` 中出现过的 `phase_id` 去重后关联 `phase`。
- 默认阶段取当前项目最新映射：

```sql
SELECT phase_id
FROM simulation_project.pp_phase
WHERE pp_record_id = :project_id
ORDER BY pp_phase_id DESC
LIMIT 1;
```

若阶段名称为空，后端兜底为 `阶段-{phaseId}`。

## 4. 输出后处理组件

来源 schema：`struct_module`

使用表：
- `componet` 或实际环境中的组件字典表。

后端统一映射为：
- `code`
- `name`
- `isDefault`
- `source`
- `remark`

前端不硬编码 component 枚举。

## 5. 本地申请单与外部自动化关系

本地新链路：

```text
orders
  -> order_case_opti
    -> case_condition_opti
```

字段关联：
- `orders.opt_issue_id -> union_opt_kernal.opt_issues.id`
- `order_case_opti.opt_job_id -> union_opt_kernal.jobs.id`
- `case_condition_opti.opt_condition_config_id -> union_opt_kernal.job_condition_config.n_id`

历史表 `order_condition_opti` 已退出当前执行链路；新代码、新迁移和最新导出只以 `order_case_opti / case_condition_opti` 为准。

## 6. 自动化提单形态

参数全局应用：
- `inputJson.globalParams.applyToAll = true`
- 一个订单生成 `1 issue + 1 job + n job_condition_config`
- 参数共用，输出按工况独立。
- `rotateDropFlag=true` 时，所有工况对应 `subject_config_struct.n_rotate_drop = 1`。

按工况独立参数：
- `inputJson.globalParams.applyToAll != true`
- 一个订单生成 `1 issue + n job`
- 每个 job 下只有一个 `job_condition_config`
- `condition.params.rotateDropFlag=true` 只影响该工况自己的 `subject_config_struct.n_rotate_drop`。

## 7. union_opt_kernal 结果表

当前结果查询覆盖以下表：
- `opt_issues`
- `jobs`
- `job_condition_config`
- `subject_config_struct`
- `opt_circle`
- `opt_data`
- `post_schedule_info`
- `post_data_save`
- `para`
- `para_config`
- `resp_config`
- `server_module_config`

查询策略：
- 先查本地 `orders / order_case_opti / case_condition_opti` 得到 `issue_id / job_id / condition_config_id`。
- 再按主键集合分批查询外部表。
- 服务层组装，不做一条大 SQL 全量联表。
- 单个 case/job 默认一次返回完整结果行，目标规模按 500 行以内设计，不走后端分页。
- 已生成轮次但未出结果时，用 `resp_config` 补齐输出空位。
- 已出结果时，通过 `post_schedule_info -> post_data_save` 补最终值与附件路径。

## 8. 测试库脚本

重建外部测试库结构和 mock 关联数据：

```bash
python database/migrations/rebuild_external_mock_structures.py
```

脚本会执行：
- 重建 `simulation_project.phase / pp_phase`。
- 重建 `union_opt_kernal` 目标表。
- 按当前本地订单生成外部 mock 结果数据。
- 回填本地 `orders.opt_issue_id`、`order_case_opti.opt_job_id`、`case_condition_opti.opt_condition_config_id`。

导出最新本地库结构：

```bash
python database/export_mysql.py --output-file database/export/full_latest.sql
```

当前导出与同步只保留 `order_case_opti / case_condition_opti` 新链路；历史 `order_condition_opti` 不再创建、不再导出、不再作为结果接口口径。

## 9. 嵌入入口认证

前端提供最小 iframe 入口：
- `/embed/orders`
- `/embed/create`

嵌入页隐藏主导航，但仍走本平台权限、隐私协议和会话校验。

认证规则：
- 优先使用本平台 `auth_token`。
- 若不存在 `auth_token`，前端读取 cookie 中的 `opt_access_token` 并调用 `POST /api/v1/auth/opt-access-token` 换取本平台 JWT。
- 后端真实接口使用 `AUTH_GET_USER_INFO_URL` 拉取用户信息。
- 公司接口成功口径兼容 `success_flag=true`、`success=true`、`code=0/200`。
- 真实地址未配置时，后端按 cookie 中的 `domain_account / user_account / user_name / real_name` 生成 mock 用户，并分配默认游客权限。
