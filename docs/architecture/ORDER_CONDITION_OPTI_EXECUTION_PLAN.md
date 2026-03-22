# 订单 Condition 运行实体改造执行稿

面向当前 `structsim-backend` 仓库的可开工执行清单。  
**最后更新**：2026-03-22

## 1. 目标

本执行稿聚焦第一阶段最小可落地改造：

1. `orders` 增加 `opt_issue_id`
2. 新增 `order_condition_opti`
3. 提单创建/更新时自动拆分 `input_json.conditions`
4. 结果查询支持按 `order_condition_id` 查询
5. 开发环境先用正式接口 + 后端 mock 数据打通结果链路

本阶段暂不做：

- 真实自动化库接入
- 复杂跨库关联
- 完整图表聚合分析
- 自动报告

## 2. 当前代码落点

### 2.1 Model 层

- `app/models/order.py`
- `app/models/order_condition_opti.py`
- `app/models/__init__.py`

### 2.2 Orders 模块

- `app/api/v1/orders/schemas.py`
- `app/api/v1/orders/routes.py`
- `app/api/v1/orders/service.py`
- `app/api/v1/orders/repository.py`

### 2.3 Results 模块

- `app/api/v1/results/routes.py`
- `app/api/v1/results/service.py`
- `app/api/v1/results/schemas.py`
- `app/api/v1/results/repository.py`

### 2.4 文档与迁移

- `database/migrations/*`
- `database/README.md`
- `database/MIGRATION.md`
- `docs/architecture/*`

## 3. 数据库任务

### 3.1 `orders` 表升级

任务：

- 新增 `opt_issue_id INT NULL`
- 新增 `condition_summary JSON NULL`
- 补充必要索引

要求：

- 不加外键
- 兼容旧库平滑升级

### 3.2 新建 `order_condition_opti`

建议字段最小集：

- `id`
- `order_id`
- `order_no`
- `opt_issue_id`
- `opt_job_id`
- `condition_id`
- `fold_type_id`
- `fold_type_name`
- `sim_type_id`
- `sim_type_name`
- `algorithm_type`
- `round_total`
- `output_count`
- `solver_id`
- `care_device_ids`
- `remark`
- `running_module`
- `process`
- `status`
- `statistics_json`
- `result_summary_json`
- `condition_snapshot`
- `external_meta`
- `created_at`
- `updated_at`

建议约束：

- `UNIQUE(order_id, condition_id)`
- `UNIQUE(opt_job_id)`

## 4. Model 改造

### 4.1 `Order`

要求：

- 增加 `opt_issue_id`
- 增加 `condition_summary`
- `to_dict()` 返回上述字段

### 4.2 `OrderConditionOpti`

要求：

- 定义 SQLAlchemy 模型
- 提供 `to_dict()` / `to_list_dict()`
- 支持列表摘要与详情返回

## 5. Orders 模块改造

### 5.1 Schema 扩展

- `OrderCreate` 增加 `condition_summary`
- `OrderCreate` 增加可选 `opt_issue_id`
- `OrderUpdate` 增加 `input_json`
- `OrderUpdate` 增加 `condition_summary`
- `OrderUpdate` 增加 `opt_issue_id`

### 5.2 Repository 扩展

建议能力：

- `create_order_condition_optis(order_id, rows)`
- `replace_order_condition_optis(order_id, rows)`
- `get_order_condition_optis(order_id)`
- `get_order_condition_opti_by_id(order_condition_id)`
- `get_order_condition_opti_by_job_id(opt_job_id)`
- `update_order_condition_opti_job_mapping(order_condition_id, opt_job_id)`

### 5.3 Service 拆分 condition 实体

内部步骤：

1. 创建/更新 `orders`
2. 从 `input_json.conditions` 提取 condition 列表
3. 转换成 `order_condition_opti` 行数据
4. 全量写入或替换 condition 记录

## 6. Results 模块改造

### 6.1 新增 condition 级结果入口

- `GET /results/order/<int:order_id>/conditions`
- `GET /results/order-condition/<int:order_condition_id>`
- `GET /results/order-condition/<int:order_condition_id>/rounds`

### 6.2 接口职责

`GET /results/order/<order_id>/conditions`

- 返回订单下所有 `order_condition_opti` 摘要
- 供前端选择某个工况方案

`GET /results/order-condition/<order_condition_id>`

- 返回 condition 摘要
- 返回 round schema
- 返回当前结果来源标记

`GET /results/order-condition/<order_condition_id>/rounds`

- 返回当前方案轮次数据
- 当前阶段走正式接口，内部返回 mock 数据

## 7. Mock 方案执行任务

### 7.1 当前推荐

第一阶段优先保留正式 results 接口路径，在接口内部返回 mock JSON，不单独新增 mock 表，也不再单独开 `/results/mock/...` 路由。

### 7.2 正式接口承载 mock 的约定

- `GET /results/order-condition/<int:order_condition_id>`
- `GET /results/order-condition/<int:order_condition_id>/rounds`

说明：

- 当前开发环境无法接入真实自动化库。
- 因此前端继续调用正式接口，后端在 service 内部填充 mock 数据。
- 后续自动化库接入后，直接替换正式接口内部业务逻辑，不改接口路径、不改前端请求。

### 7.3 返回结构建议

condition 摘要：

```json
{
  "orderConditionId": 1,
  "orderId": 100,
  "optIssueId": 9001,
  "optJobId": 9101,
  "conditionId": 101,
  "foldTypeName": "展开态",
  "simTypeName": "贝叶斯优化",
  "algorithmType": "BAYESIAN",
  "solverId": "abaqus_2024",
  "roundTotal": 12,
  "process": 86.5,
  "status": 1,
  "resultSource": "mock"
}
```

rounds 数据：

```json
{
  "resultSource": "mock",
  "items": [
    {
      "roundIndex": 1,
      "params": {
        "param1": 1.1,
        "param2": 2.2,
        "param3": 3.3
      },
      "outputs": {
        "output1": 10.5,
        "output1Weighted": 3.2,
        "output2": 20.5,
        "output2Weighted": 5.8,
        "output3": 30.5,
        "output3Weighted": 8.1
      },
      "runningModule": "SOLVE",
      "process": 100,
      "status": 2,
      "finalResult": 17.1,
      "moduleDetails": [
        {
          "moduleCode": "PREPARE",
          "statusText": "已完成",
          "progress": 100,
          "durationSec": 15
        },
        {
          "moduleCode": "SOLVE",
          "statusText": "已完成",
          "progress": 100,
          "durationSec": 230
        }
      ]
    }
  ],
  "total": 1
}
```

### 7.4 状态约定建议

- `0`: 待运行
- `1`: 运行中
- `2`: 完成
- `3`: 失败

## 8. API 变更清单

### 8.1 本阶段新增

- `GET /orders/:id/conditions`
- `GET /results/order/:id/conditions`
- `GET /results/order-condition/:id`
- `GET /results/order-condition/:id/rounds`

### 8.2 本阶段保留不动

- `GET /orders`
- `GET /orders/:id`
- `POST /orders`
- `PUT /orders/:id`
- `GET /results/order/:id/sim-types`
- `GET /results/sim-type/:id/rounds`

## 9. 执行顺序

### Step 1

- 改 `orders` 表
- 新建 `order_condition_opti` 表
- 新建 SQLAlchemy 模型

### Step 2

- 扩展 `orders` schema
- 扩展 repository
- 扩展 service
- 提单提交后自动拆 condition

### Step 3

- 新增 `orders/:id/conditions`
- 新增 `results/order/:id/conditions`

### Step 4

- 保留正式 condition 结果接口
- 在正式接口内部填充 mock rounds / mock progress / mock moduleDetails
- 用正式接口先打通结果页展示和联调

### Step 5

- 前端切到 condition 级结果入口
- 继续收口页面文案、概览卡片和流程展示语义

## 9.1 当前进度快照

截至 2026-03-22，当前实际进度为：

- Step 1：已完成
- Step 2：已基本完成
- Step 3：已基本完成
- Step 4：已完成第一版，当前通过正式 `results` 路由返回 mock 数据
- Step 5：已继续推进，结果页主链路已切到工况方案视角，dashboard 侧命名与 mock 展示已进一步收口

已落地内容：

- `orders.opt_issue_id`
- `orders.condition_summary`
- `order_condition_opti` 表结构 / 模型 / 自动升级脚本
- 提单创建与更新时按 `input_json.conditions` 自动拆分并全量写入
- `GET /orders/:id/conditions`
- `GET /results/order/:id/conditions`
- `GET /results/order-condition/:id`
- `GET /results/order-condition/:id/rounds`
- condition 级 mock rounds / mock progress / mock moduleDetails
- 结果页 `useResultsData` 主数据流已改为工况方案命名，概览/分析/流程页统一消费 condition 级结果
- 结果页筛选、导出、流程图、结果表已统一围绕“工况方案”展示 mock 数据

当前明确采用的阶段策略：

- 没有真实 `opt_job_id` 回填时，先允许为空
- 结果页优先打通 mock 链路，不等待自动化库真实接入
- 前端继续调用正式接口，mock 数据由后端 service 内部填充
- 优先完成页面可见效果、交互收口与联调演示

当前剩余缺口：

- 前端仍有少量历史文件名和旧接口类型名沿用 `sim-type` 语义，但 dashboard 页面主链路已完成代码级收口
- 真实自动化库回填与真实 `opt_job_id` 映射暂缓到第二阶段
- 真实数据库执行与联调验证仍待网络 / 数据库连通后完成

## 10. 验收清单

### 10.1 提单写入

- 新建订单后 `orders` 有记录
- `orders.opt_issue_id` 可为空但字段存在
- `order_condition_opti` 按 `inputJson.conditions` 成功拆出多条记录

### 10.2 更新提单

- 更新订单后 `order_condition_opti` 成功全量替换
- 无重复 condition 行

### 10.3 查询

- 能通过 `order_id` 查到 condition 列表
- 能通过 `order_condition_id` 查到 condition 摘要
- 能通过正式 `results` 接口查到 mock round 数据

### 10.4 数据库导入导出

- 无外键导致的导入失败
- 索引不会阻碍内网同步流程

## 11. 当前明确不做的内容

- 自动化库真实连接
- 真实跨库查询
- 完整图表后端聚合
- condition 版本历史
- 复杂统计缓存

这些内容放到第二阶段处理。

## 12. 当前建议

当前主目标已经不是继续扩字段，而是把“正式接口承载 mock 数据”的联调流程和页面展示彻底收口。

优先级建议：

1. 保持正式接口路径不变，继续在后端 service 内部维护 mock 返回。
2. 前端结果页全部切到 condition 级入口，并收口旧 `sim-type` 语义。
3. 页面先把工况方案结果、流程进度、失败轮次、数据源展示清楚。
4. 等自动化库可用后，再把接口内部 mock 逻辑替换为真实逻辑。
