# 结果页与详情页快照消费迁移清单

面向当前订单列表、编辑页、结果页对订单快照字段的实际消费路径梳理。
**最后更新**: 2026-03-22

## 1. 目的

本文只解决一个问题：

当前哪些页面已经切到 `inputJson`，哪些页面仍依赖顶层冗余字段，哪些字段可以降级，哪些字段暂时不能动。

## 2. 当前页面消费现状

### 2.1 提单编辑页

页面：

- `structsim-ai-platform/src/pages/submission/index.tsx`

当前消费方式：

- 优先读取 `inputJson` / `input_json`
- 从 `inputJson.conditions` 恢复 `foldTypeIds`、`simTypeIds`
- 用 `conditionId` 恢复运行态配置
- 只有 `conditions` 缺失时才回退到 `optParam`

结论：

- 编辑页已经基本完成主快照切换
- `optParam` 在编辑页只剩历史兼容兜底用途

### 2.2 订单列表页

页面：

- `structsim-ai-platform/src/pages/orders/OrderList.tsx`

当前消费方式：

- 优先读取 `conditionSummary`
- 若 `conditionSummary` 缺失，则降级为 `simTypeIds`

结论：

- 列表页当前不依赖 `inputJson`
- 列表页也不依赖 `optParam`
- `conditionSummary` 仍然有保留价值

### 2.3 结果页主入口

页面：

- `structsim-ai-platform/src/pages/dashboard/hooks/useResultsData.ts`
- `structsim-ai-platform/src/pages/dashboard/Results.tsx`

当前消费方式：

- 调用 `ordersApi.getOrder(orderId)`
- 默认使用 `orderDetail.simTypeIds` 初始化仿真类型筛选
- 若 `simTypeIds` 不存在，再降级为 `results/order/:id/sim-types` 返回的结果集合

结论：

- 结果页当前不依赖 `optParam`
- 结果页也还没有切到 `inputJson.conditions`
- 结果页仍依赖订单详情顶层冗余字段 `simTypeIds`

### 2.4 结果明细表与流程视图

页面：

- `SimTypeResultTable.tsx`
- `ProcessView.tsx`

当前消费方式：

- 只消费结果接口返回的 `simTypeResults` 和 `rounds`
- 不直接消费 `inputJson`
- 不直接消费 `optParam`

结论：

- 结果子视图本身对订单快照耦合较低
- 真正的耦合点在 `useResultsData`

## 3. 后端当前返回结构

来源：

- `app/models/order.py`
- `app/api/v1/orders/service.py`

订单详情当前同时返回：

- `sim_type_ids`
- `fold_type_ids`
- `opt_param`
- `input_json`
- `condition_summary`

订单列表当前返回：

- `sim_type_ids`
- `fold_type_ids`
- `condition_summary`

## 4. 字段当前状态分类

### 4.1 必须保留

- `input_json`
- `condition_summary`
- `sim_type_ids`

说明：

- `input_json` 是编辑页主快照
- `condition_summary` 是列表页主摘要
- `sim_type_ids` 仍被结果页默认筛选依赖

### 4.2 可视为兼容字段

- `opt_param`
- `fold_type_ids`

说明：

- `opt_param` 当前主要被编辑页兜底兼容使用
- `fold_type_ids` 仍有价值，但不是结果页当前主依赖

### 4.3 可以逐步弱化的字段依赖

- 结果页对 `sim_type_ids` 的依赖

替代方向：

- 从 `inputJson.conditions` 推导出 `simTypeIds`
- 再与 `/results/order/:id/sim-types` 做交集校验

## 5. 当前风险点

### 5.1 结果页筛选维度仍偏平铺

当前结果页只认 `simTypeIds`，没有识别：

- 同一 `simTypeId` 在多个目标姿态下的多个 `condition`
- 树状结构中的 `conditionId`

风险：

- 当结果视图后续需要细化到姿态或工况维度时，现有筛选模型不够用

### 5.2 列表页与详情页消费边界不同

列表页读 `conditionSummary`，编辑页读 `inputJson`，结果页读 `simTypeIds`。

风险：

- 同一订单在不同页面中的语义来源不统一
- 后续字段裁剪时容易误伤某个页面

### 5.3 `optParam` 虽然主链路已降级，但还不能直接删除

原因：

- 编辑页仍保留对历史订单的兜底恢复逻辑
- 旧库中的历史订单未必都有完整 `input_json.conditions`

## 6. 最小迁移顺序

建议按以下顺序推进：

1. 结果页先从 `inputJson.conditions` 计算默认 `simTypeIds`
2. 保留当前 `orderDetail.simTypeIds` 作为兜底
3. 明确结果页暂不处理 `conditionId` 维度，只完成快照来源统一
4. 等历史订单验证完成后，再评估是否可下线结果页对顶层 `simTypeIds` 的强依赖
5. 最后再评估 `optParam` 是否可从详情接口中降级或按需返回

## 7. 推荐落地方案

### 7.1 结果页第一阶段

目标：

- 不改结果接口
- 只改结果页默认筛选来源

做法：

- 优先从 `orderDetail.inputJson.conditions` 提取 `simTypeId`
- 若 `inputJson` 缺失，再回退到 `orderDetail.simTypeIds`
- 若仍缺失，再回退到 `simTypeResults`

收益：

- 快照来源与编辑页统一
- 改动范围小
- 风险可控

### 7.2 结果页第二阶段

目标：

- 让结果页识别姿态维度

做法：

- 引入 `conditionId -> foldTypeId + simTypeId` 映射
- 根据需要决定筛选 UI 是否升级到姿态 / 工况维度

说明：

- 这一步不是最快上线必需项

### 7.3 历史订单兼容

必须保留：

- 编辑页从 `optParam` 兜底恢复
- 结果页从 `simTypeIds` 兜底恢复

直到确认历史订单全部具备稳定的 `input_json.conditions`。

## 8. `optParam` 何时可以真正降级

必须同时满足以下条件：

1. 编辑页已不再需要用 `optParam` 恢复历史订单
2. 结果页和详情页都不再消费 `optParam`
3. 历史订单数据已补齐或确认不再需要编辑

在此之前：

- 可以在文档中降级其语义
- 不建议直接删除接口返回或数据库字段

## 9. 当前结论

当前真实状态是：

- 编辑页：主用 `inputJson`
- 列表页：主用 `conditionSummary`
- 结果页：主用 `simTypeIds`，尚未切到 `inputJson.conditions`
- `optParam`：已退居兼容字段，但仍不能立刻删除

因此，下一步最合适的动作不是大改结果接口，而是先把结果页的默认快照来源统一到 `inputJson.conditions`。

