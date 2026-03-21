# 提单初始化与订单快照协议

面向当前前后端联调主链路维护。
**最后更新**: 2026-03-21

## 1. 适用范围

本协议覆盖以下主链路：

1. 提单初始化取数边界
2. 提单页运行时树状结构
3. 订单提交 payload
4. 订单快照回填
5. 列表摘要与结果页消费边界

## 2. 当前协议边界

### 2.1 页面主结构

当前提单页真实结构是树状结构，而不是平铺结构：

```text
项目
├─ 原始文件
├─ 原始姿态
├─ 目标姿态
│  └─ 仿真类型
│     └─ conditionId
│        ├─ params
│        ├─ output
│        ├─ solver
│        └─ careDeviceIds
└─ 项目级附加信息
```

### 2.2 主键语义

当前页面运行态以 `conditionId` 作为“目标姿态 + 仿真类型”组合配置的主键。

`conditionId` 当前来自：

- 后端工况配置 `condition_config.id`
- 若没有显式配置，前端临时使用负数兜底 ID

## 3. 初始化接口现状

当前后端提供：

```text
GET /api/v1/orders/init-config?projectId={id}&simTypeId={id?}
```

当前返回字段主要包括：

- `projectId`
- `projectName`
- `simTypeId`
- `simTypeName`
- `simTypeCode`
- `defaultParamGroup`
- `defaultCondOutGroup`
- `defaultSolver`
- `paramGroupOptions`
- `condOutGroupOptions`
- `solverOptions`

当前必须明确：

- 该接口仍偏单 `simTypeId` 维度
- 当前前端提单页主实现并不直接依赖该接口完成整页装配
- 前端实际还依赖姿态、工况配置、参数组、输出组、资源池、关注器件等多组数据

因此，`init-config` 当前定位应为：

- 配置初始化补充接口
- 不是当前整页运行态的唯一来源

## 4. 提交 payload 协议

前端当前提交 payload 结构如下：

```json
{
  "projectId": 1,
  "modelLevelId": 1,
  "originFile": {},
  "originFoldTypeId": 1,
  "foldTypeIds": [1, 2],
  "participantIds": ["u1", "u2"],
  "remark": "备注",
  "simTypeIds": [101, 102],
  "optParam": {},
  "conditionSummary": {},
  "inputJson": {},
  "clientMeta": {
    "lang": "zh-CN"
  }
}
```

字段定位如下：

| 字段 | 定位 |
| --- | --- |
| `projectId` | 项目标识 |
| `modelLevelId` | 模型层级 |
| `originFile` | 原始文件快照 |
| `originFoldTypeId` | 原始姿态 |
| `foldTypeIds` | 目标姿态集合 |
| `participantIds` | 协作参与人 |
| `remark` | 备注 |
| `simTypeIds` | 已选仿真类型集合 |
| `optParam` | 旧结构兼容映射 |
| `conditionSummary` | 列表摘要 |
| `inputJson` | 主快照 |
| `clientMeta` | 客户端元信息 |

## 5. `inputJson` 协议

`inputJson` 是当前唯一应被视为可信主快照的结构。

推荐用途：

- 编辑态恢复
- 订单详情回显
- 结果页上下文还原

### 5.1 顶层结构

```json
{
  "version": 2,
  "projectInfo": {},
  "conditions": [],
  "globalSolver": {},
  "inpSets": []
}
```

### 5.2 `projectInfo`

保存项目级基础信息：

```json
{
  "projectId": 1,
  "projectName": "项目A",
  "modelLevelId": 1,
  "originFile": {},
  "originFoldTypeId": 1,
  "participantIds": ["u1", "u2"],
  "issueTitle": "标题",
  "remark": "备注"
}
```

### 5.3 `conditions`

`conditions` 是主业务树的展开结果，每一项对应一个 `conditionId`：

```json
{
  "conditionId": 1001,
  "foldTypeId": 1,
  "foldTypeName": "展开态",
  "simTypeId": 101,
  "simTypeName": "静力学",
  "params": {},
  "output": {},
  "solver": {},
  "careDeviceIds": []
}
```

字段含义：

- `conditionId`: 主键
- `foldTypeId`: 目标姿态 ID
- `simTypeId`: 仿真类型 ID
- `params`: 参数配置
- `output`: 输出与工况配置
- `solver`: 求解器配置
- `careDeviceIds`: 关注器件

### 5.4 `globalSolver`

表示项目级全局求解器默认值，供多个 condition 共享或引用。

### 5.5 `inpSets`

表示从 `.inp` 文件解析出的 set 集，用于关注器件和输出相关配置。

## 6. `optParam` 与 `conditionSummary`

### 6.1 `optParam`

当前代码仍输出 `optParam`，但它只是兼容旧结构的复合字典。

当前局限：

- 以 `simTypeId` 为 key
- 无法完整表达同一 `simTypeId` 在多个姿态下的多份配置

因此：

- `optParam` 只能作为兼容字段
- 不应继续承担主语义

### 6.2 `conditionSummary`

`conditionSummary` 的目标是订单列表快速展示，例如：

```json
{
  "姿态A": ["静力学", "模态"],
  "姿态B": ["热仿真"]
}
```

因此：

- 适合列表摘要
- 不适合编辑态回填

## 7. 编辑态回填约束

编辑态恢复顺序建议固定为：

1. `inputJson`
2. 顶层冗余字段兜底
3. `optParam` 仅作为历史兼容兜底

不建议继续依赖：

- 仅 `simTypeIds`
- 仅 `optParam`

原因：

- 这两者都不能完整恢复树状结构

## 8. 协议演进建议

当前建议保留：

- `inputJson`
- `conditionSummary`
- `clientMeta`
- `submitCheck`

当前建议降级：

- `optParam`

后续方向：

- 让详情页、编辑页、结果页统一消费 `inputJson`
- 明确 `version` 的兼容规则
- 视上线节奏决定是否将 `init-config` 升级为 `conditionId` 维度的初始化协议

