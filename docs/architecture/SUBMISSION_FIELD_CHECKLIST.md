# 提单字段清单与联调检查项

最后更新：2026-04-10

## 1. 目的

这份清单面向联调和回归，只关注提单主链路当前真正生效的字段和检查点。

## 2. 用户基础会话

来源：`GET /api/v1/auth/session`

必须可用的字段：

- `user.domainAccount`
- `user.recentProjectIds`
- `user.maxBatchSize`
- `user.maxCpuCores`
- `user.dailyRoundLimit`
- `user.todayUsedRounds`
- `user.todayRemainingRounds`

检查项：

- 刷新页面后能拿到最新提单限制
- 不需要进入登录接口返回用户快照

## 3. 用户懒加载上下文

### 3.1 可见项目列表

来源：提单页懒加载查询

检查项：

- 只在进入提单页后请求
- 最近常用项目若不可见，能顺延到下一条可见常用项目
- 常用项目全部失效时回退到可见项目第一项

### 3.2 资源池

来源：`GET /api/v1/orders/resource-pools`

检查项：

- 未配置真实接口时，后端直接返回 mock 资源池
- 配置了真实接口但失败时，后端仍回退 mock
- `default_source_id` 无效时，前端回退到第一项
- 非 GPU 求解器时资源池区域必须显示

## 4. 项目上下文

来源：`GET /api/v1/orders/init-project-config?projectId={id}`

必查字段：

- `projectId`
- `projectName`
- `phases`
- `defaultPhaseId`
- `participantCandidates`
- `defaultParamGroup`
- `defaultCondOutGroup`
- `defaultSolver`

检查项：

- 项目没有默认仿真类型关系时，接口仍能正常返回
- `defaultPhaseId` 必须来自：
  - `pp_phase WHERE pp_record_id = project_id ORDER BY pp_phase_id DESC LIMIT 1`
- `phases` 必须来自该项目在 `pp_phase` 中出现过的阶段去重结果
- 阶段下拉为空时不应再报“未知错误”

## 5. 参与人

候选来源：全量用户  
使用场景：项目上下文

排序优先级：

1. 已勾选用户
2. 当前项目历史常选参与人
3. 其余用户

检查项：

- 勾选或取消后立即重排
- 已勾选用户始终置顶
- 历史常选参与人在未勾选时优先展示

## 6. 默认快速提单链路

默认值真源：

- 默认工况配置
- `condition_config` 带出的默认参数组
- `condition_config` 带出的默认输出组
- `condition_config` 带出的默认求解器

检查项：

- 默认项目确定后，默认工况能正常展开
- 参数组/输出组对项目过滤规则正确：
  - 显式关联项目：命中时可用
  - 项目关联为空：视为全部项目可用

## 7. 申请单实例状态

提交时重点检查：

- `projectId`
- `phaseId`
- `participantIds`
- `simTypeIds`
- `inputJson.projectInfo`
- `inputJson.conditions`
- `globalSolver`

说明：

- `conditionId` 只在 `conditions` 中作为申请单内主键使用
- `simTypeIds` 保留为聚合字段，不承担整页状态表达
- `optParam` 仅作历史兼容，不再作为新链路主语义

## 8. 回归建议

最少覆盖以下场景：

1. 最近常用项目失效后的顺延命中
2. 项目阶段默认值取最新 `pp_phase`
3. 项目无默认仿真类型关系时仍可打开抽屉
4. 资源池真实接口缺失时后端 mock 生效
5. 参与人排序符合“已勾选 > 历史常选 > 其余”
6. 默认工况能带出默认参数、输出、求解器
