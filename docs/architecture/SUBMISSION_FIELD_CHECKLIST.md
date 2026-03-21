# 提单主链路字段清单与联调清单

面向当前前后端代码实现的提单主链路梳理。
**最后更新**: 2026-03-21

## 1. 适用范围

本文只覆盖当前上线前必须收口的提单主链路：

- 提单页运行时状态树
- 初始化取数
- 提交 payload
- `inputJson` 快照
- 编辑态恢复
- 订单列表摘要
- 结果页与详情页后续消费边界

本文不把登录 / SSO 视为提单配置化主链路的一部分，但将其视为并行 P0 基础能力。

## 2. 当前页面真实结构

当前提单页不是简单平铺表单，更接近以下树状结构：

```text
项目
├─ 原始文件 originFile
├─ 原始姿态 originFoldTypeId
├─ 目标姿态 foldTypeIds[]
│  ├─ 仿真类型 simTypeId
│  │  └─ conditionId
│  │     ├─ params
│  │     ├─ output
│  │     ├─ solver
│  │     └─ careDeviceIds
├─ 参与人 participantIds[]
├─ 标题 issueTitle
└─ 备注 remark
```

页面运行时真正以 `conditionId` 作为“目标姿态 + 仿真类型”组合的主键。

## 3. 前端运行时状态树

来源：

- `structsim-ai-platform/src/pages/submission/index.tsx`
- `structsim-ai-platform/src/pages/submission/hooks/useSubmissionState.ts`
- `structsim-ai-platform/src/pages/submission/types.ts`

当前运行时核心状态如下：

- `form`
  - `projectId`
  - `issueTitle`
  - `modelLevelId`
  - `originFile`
  - `originFoldTypeId`
  - `participantIds`
  - `foldTypeIds`
  - `remark`
  - `simTypeIds`
- `selectedSimTypes`
  - 数组项结构为 `{ conditionId, foldTypeId, simTypeId }`
- `simTypeConfigs`
  - `Record<conditionId, SimTypeConfig>`
- `globalSolver`
- `inpSets`

`SimTypeConfig` 当前结构：

```json
{
  "conditionId": 101,
  "foldTypeId": 1,
  "simTypeId": 2,
  "params": {},
  "output": {},
  "solver": {},
  "careDeviceIds": []
}
```

结论：

- 页面主状态树以 `conditionId` 挂配置。
- `simTypeIds` 只保留选中仿真类型集合语义，不能单独表达完整页面状态。
- `optParam` 无法表达多姿态同一 `simTypeId` 的多个配置实例。

## 4. 当前初始化取数现状

### 4.1 前端提单页直接消费的数据

`useSubmissionState` 当前直接取数来源：

- 项目 `useProjects`
- 仿真类型 `useSimTypes`
- 目标姿态 `useFoldTypes`
- 参数定义 `useParamDefs`
- 求解器 `useSolvers`
- 输出定义 `useOutputDefs`
- 工况定义 `useConditionDefs`
- 参数组 `useParamGroups`
- 输出组 `useOutputSets`
- 工况配置 `useConditionConfigs`
- 用户列表 `rbacApi.getUsers`
- 关注器件 `useCareDevices`
- 资源池 `useSolverResources`

### 4.2 `init-config` 接口当前定位

后端当前提供：

```text
GET /api/v1/orders/init-config?projectId={id}&simTypeId={id?}
```

返回结构主要是单个 `simTypeId` 维度的默认参数组、默认输出组、默认求解器及其候选项。

### 4.3 当前真实差异

当前提单页主实现并不直接依赖 `init-config` 来完成整页装配，而是通过多组配置查询在前端解释出页面运行态。

这意味着：

- `init-config` 目前更接近“旧单仿真类型初始化接口”
- 前端当前页面运行态已经升级为“多姿态、多工况、以 `conditionId` 为主键”的树状结构
- 若想最快上线，不应先重做整页前端，而应先统一协议边界

## 5. 提交 payload 字段清单

来源：`structsim-ai-platform/src/pages/submission/index.tsx`

当前提交时顶层 payload 结构如下：

```json
{
  "projectId": 1,
  "modelLevelId": 1,
  "originFile": {},
  "originFoldTypeId": 1,
  "foldTypeIds": [1, 2],
  "participantIds": ["u1"],
  "remark": "",
  "simTypeIds": [11, 12],
  "optParam": {},
  "conditionSummary": {},
  "inputJson": {},
  "clientMeta": {
    "lang": "zh-CN"
  }
}
```

字段分类如下：

| 字段 | 当前用途 | 是否主链路必须 |
| --- | --- | --- |
| `projectId` | 项目标识 | 是 |
| `modelLevelId` | 模型层级 | 是 |
| `originFile` | 原始文件来源 | 是 |
| `originFoldTypeId` | 原始姿态 | 建议保留 |
| `foldTypeIds` | 目标姿态集合 | 是 |
| `participantIds` | 协作参与人 | 建议保留 |
| `remark` | 备注 | 否 |
| `simTypeIds` | 已选仿真类型集合 | 是 |
| `optParam` | 兼容旧结构的冗余映射 | 否 |
| `conditionSummary` | 列表摘要 | 否 |
| `inputJson` | 主快照 | 是 |
| `clientMeta` | 客户端元数据 | 否 |

## 6. `inputJson` 完整结构清单

当前前端提交：

```json
{
  "version": 2,
  "projectInfo": {
    "projectId": 1,
    "projectName": "项目A",
    "modelLevelId": 1,
    "originFile": {},
    "originFoldTypeId": 1,
    "participantIds": [],
    "issueTitle": "",
    "remark": ""
  },
  "conditions": [
    {
      "conditionId": 101,
      "foldTypeId": 1,
      "foldTypeName": "目标姿态A",
      "simTypeId": 11,
      "simTypeName": "仿真类型A",
      "params": {},
      "output": {},
      "solver": {},
      "careDeviceIds": []
    }
  ],
  "globalSolver": {},
  "inpSets": []
}
```

当前建议定位：

- `projectInfo`: 页面顶层项目快照
- `conditions`: 主业务树
- `globalSolver`: 全局求解器默认值
- `inpSets`: 从 INP 解析出的集合信息

## 7. `optParam` 当前真实定位

来源：`submission/index.tsx` 提交逻辑。

当前构造方式：

- 以 `simTypeId` 为 key
- 只取当前找到的第一个同 `simTypeId` 配置
- value 内只放 `params`、`output`、`solver`

这意味着：

- `optParam` 不是主快照
- `optParam` 无法完整表达“同一仿真类型在不同目标姿态下的多个 condition”
- `optParam` 仅适合作为兼容旧结构的过渡字段

结论：

- `inputJson` 必须作为唯一可信回填来源
- `optParam` 只保留到旧链路完全下线为止

## 8. 编辑态恢复清单

来源：`submission/index.tsx` 中 `restoreOrderSnapshot`

恢复顺序如下：

1. 优先读取 `order.inputJson` / `order.input_json`
2. 恢复 `projectInfo`
3. 解析 `conditions`
4. 从 `conditions` 反推 `foldTypeIds` 与 `simTypeIds`
5. 用 `conditionId` 恢复 `selectedSimTypes`
6. 用 `conditionId` 恢复 `simTypeConfigs`
7. 恢复 `globalSolver`
8. 恢复 `inpSets`
9. 仅在 `conditions` 缺失时回退到 `optParam`

这说明当前代码已经把：

- `inputJson` 作为主恢复来源
- `optParam` 作为历史兼容兜底

## 9. 订单详情与结果页消费边界

后端订单详情当前仍同时返回：

- 顶层冗余字段
- `opt_param`
- `input_json`
- `condition_summary`

建议消费边界：

- 编辑页恢复：只认 `inputJson`
- 订单详情页：优先读 `inputJson`，顶层字段只做兼容兜底
- 列表页：读 `conditionSummary`
- 结果页：逐步切到 `inputJson.conditions`

## 10. 联调必须核对的字段

### 10.1 初始化阶段

- 项目切换后，目标姿态、仿真类型、工况配置是否同步更新
- `conditionConfigs` 中的 `id` 是否稳定作为 `conditionId`
- 默认参数组、默认输出组、默认求解器是否来自工况配置优先，其次才是仿真类型默认值

### 10.2 文件校验阶段

- `originFile.type=1` 时按路径校验
- `originFile.type=2` 时按文件 ID 校验
- `.inp` 文件能否稳定返回 `inpSets`
- 文件不存在但路径合法时是否允许继续提交

### 10.3 提交阶段

- `inputJson.projectInfo.originFile` 与顶层 `originFile` 是否一致
- `conditions` 是否覆盖所有 `selectedSimTypes`
- `conditionId` 是否稳定
- `optParam` 是否只作为兼容字段，不再参与新链路语义判断

### 10.4 编辑态恢复阶段

- 从 `inputJson.conditions` 恢复的 `foldTypeIds`、`simTypeIds` 是否正确
- 同一 `simTypeId` 在多个姿态下时能否恢复为多个 `conditionId`
- `globalSolver`、`inpSets` 能否完整回填

### 10.5 列表与结果阶段

- 列表页是否只依赖 `conditionSummary`
- 结果页是否仍依赖 `optParam`
- 若结果页仍依赖旧结构，需要列出迁移清单再下线 `optParam`

## 11. 当前主要缺口

- 前端提单页运行态已是树状结构，后端 `init-config` 仍是单 `simTypeId` 维度
- 订单表同时保留 `opt_param`、`input_json`、`condition_summary`，语义边界还不够硬
- 结果页、详情页、编辑态对快照消费规范尚未完全统一
- 登录 / SSO、权限模型虽然不是提单配置主链路，但属于上线 P0 并行依赖

## 12. 最快上线建议

如果目标是最快打通参数化和提单流程，建议按下面顺序推进：

1. 冻结主快照协议，以 `inputJson` 为唯一主结构。
2. 冻结 `conditionId` 语义，明确其等于当前工况配置主键。
3. 提交、编辑、详情、结果统一以 `inputJson.conditions` 为中心消费。
4. `optParam` 只保留兼容输出，不再作为任何新页面判断依据。
5. 登录 / SSO 收口为统一用户模型与统一权限模型。

最小上线范围建议：

- 管理员 / 普通用户两级角色
- 单一提单主链路
- 稳定的订单快照
- 稳定的结果查询入口

## 13. 适合保留与建议迁移

适合保留：

- 前端 React 19 + TypeScript + React Hook Form + Zod
- 前端 TanStack Query + Zustand
- 前端当前提单页的树状运行态模型
- 后端 Flask + SQLAlchemy + JWT 基础框架
- 当前 `orders` 表作为过渡承载结构

建议后续迁移或降级：

- `opt_param` 的业务主语义
- 过度依赖前端拼装完整运行态的初始化方式
- 结果页对旧字段的隐式依赖

当前不建议为上线而做的事情：

- 前后端框架迁移
- 大规模配置中心重构
- 先做复杂权限拆分再开始收口提单主链路

