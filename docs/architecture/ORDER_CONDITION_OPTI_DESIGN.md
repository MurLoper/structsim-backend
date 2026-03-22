# 订单与 Condition 运行实体拆分设计

面向“尽快打通提单、自动化流程、结果查询”的数据模型设计稿。
**最后更新**: 2026-03-22

## 1. 设计目标

本设计解决以下问题：

1. 保留 `orders` 作为主单入口
2. 为每个 `condition` 建立独立运行实体
3. 接入自动化库中的 `opt_issue_id` 与 `opt_job_id`
4. 让结果查询按单个方案进行，而不是只能按整单模糊查看

## 2. 已确认前提

根据当前确认，以下前提已固定：

1. `opt_issue_id` 与 `opt_job_id` 都是 `INT`，来源于其他数据库的主键
2. `order_condition_opti` 当前不存在，需要新建
3. 当前 `orders` 表中的数据可以视为过渡或假数据，后续应由提单提交流程自动填充
4. 第一阶段不建议加外键
5. 导出当前数据库后需要能同步到内网数据库，因此不能因为强外键约束导致导入失败
6. `final_result` 不是通用字段含义
7. DOE 不展示 `final_result`
8. 贝叶斯才展示 `final_result`
9. 贝叶斯没有单独的 `weighted_score` 字段需要本地落库
10. 加权规则在提单输出配置中已定义，自动化流程会计算并写入结果库

## 3. 当前问题

当前模型的主要问题是：

- `orders.input_json.conditions` 虽然保存了完整快照，但没有拆成可检索、可关联、可追踪的 condition 级实体
- 结果页当前更多依赖 `simTypeIds`，还没有真正建立到单个 `condition` 运行实例的稳定映射
- 自动化库的 `opt_issue_id`、`opt_job_id` 还没有在当前业务库中形成清晰主从关系
- `conditionSummary` 只适合列表摘要，不适合结果、统计、报表

## 4. 目标模型

建议收口为三层模型：

```text
orders
  1 -> 1 opt_issue_id
  1 -> n order_condition_opti

order_condition_opti
  n -> 1 order_id
  1 -> 1 opt_job_id
  1 -> 1 condition 快照

automation_db
  opt_issue_id -> issue / 主单
  opt_job_id -> job / 方案
```

核心关系：

- `order_id` 与 `opt_issue_id` 一一对应
- `order_condition_opti` 中每条记录对应一个 `condition`
- 每条 `order_condition_opti` 记录最终映射一个 `opt_job_id`

## 5. 主单表 `orders` 调整建议

### 5.1 保留职责

`orders` 继续负责：

- 提单入口
- 权限控制
- 项目上下文
- 主快照
- 列表筛选
- 主单级状态与备注

### 5.2 建议新增字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `opt_issue_id` | INT | 提交申请单后生成的自动优化申请单 ID |

### 5.3 建议保留字段

- `project_id`
- `model_level_id`
- `origin_file_*`
- `origin_fold_type_id`
- `fold_type_ids`
- `participant_uids`
- `remark`
- `sim_type_ids`
- `input_json`
- `condition_summary`
- `client_meta`
- `created_by`
- `status`
- `progress`

### 5.4 `orders` 新定位

`orders` 不再承担所有 condition 的运行明细承载职责。

它的定位改为：

- 主单头
- 快照总入口
- 快速筛选入口
- 外部自动化主单映射入口

## 6. 新表 `order_condition_opti`

### 6.1 表职责

`order_condition_opti` 用于保存：

- `order_id` 下每个 `condition` 的独立运行实体
- 结果查询主入口
- 与外部 `opt_job_id` 的映射
- condition 级摘要
- condition 级完整快照

### 6.2 推荐字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `order_id` | BIGINT NOT NULL | 主单 ID |
| `order_no` | VARCHAR(50) | 冗余主单编号，便于检索和审计 |
| `opt_issue_id` | INT NOT NULL | 对应主单自动优化申请单 ID |
| `opt_job_id` | INT | 对应外部自动化 job ID |
| `condition_id` | BIGINT NOT NULL | 当前提单中的 condition 标识 |
| `fold_type_id` | INT NOT NULL | 姿态 ID |
| `fold_type_name` | VARCHAR(100) | 姿态名称快照 |
| `sim_type_id` | INT NOT NULL | 仿真类型 ID |
| `sim_type_name` | VARCHAR(100) | 仿真类型名称快照 |
| `algorithm_type` | VARCHAR(32) | 算法类型，如 `DOE` / `BAYESIAN` |
| `round_total` | INT DEFAULT 0 | 轮次数量概览 |
| `output_count` | INT DEFAULT 0 | 输出数量概览 |
| `solver_id` | VARCHAR(64) / INT | 求解器标识，当前自动化流程中该字段同时表达类型和版本 |
| `care_device_ids` | JSON | 关注器件 ID 列表 |
| `remark` | TEXT | condition 级备注 |
| `running_module` | VARCHAR(64) | 当前运行模块摘要 |
| `process` | DECIMAL(5,2) | 进度百分比 |
| `status` | SMALLINT | 运行状态 |
| `statistics_json` | JSON | condition 级统计摘要 |
| `result_summary_json` | JSON | 结果摘要 |
| `condition_snapshot` | JSON NOT NULL | 完整 condition 快照 |
| `external_meta` | JSON | 外部库附加映射信息 |
| `created_at` | BIGINT | 创建时间 |
| `updated_at` | BIGINT | 更新时间 |

### 6.3 最小必须字段

如果以“最快上线”为目标，最小必须字段是：

- `id`
- `order_id`
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
- `process`
- `status`
- `condition_snapshot`
- `created_at`
- `updated_at`

### 6.4 为什么必须保留 `condition_snapshot`

因为拆散字段永远不够表达完整业务语义。

`condition_snapshot` 至少应保留：

```json
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
```

建议原则：

- 拆散字段用于索引、筛选、汇总、展示
- `condition_snapshot` 用于完整语义保真

## 7. 约束与索引策略

### 7.1 当前阶段原则

当前阶段明确建议：

- 不加数据库外键
- 只加必要索引
- 只加必要唯一约束

原因：

- 当前数据库需要导出后同步到内网库
- 过早加外键会提升导入失败风险
- 当前仍处于结构收口期，外键过多会增加迁移成本

### 7.2 当前建议加的约束

建议至少增加：

```text
UNIQUE(order_id, condition_id)
UNIQUE(opt_job_id)
```

说明：

- `UNIQUE(order_id, condition_id)` 保证一个主单下一个 condition 只落一条运行实体
- `UNIQUE(opt_job_id)` 保证一个外部 job 只映射一条 condition 实体

### 7.3 当前建议加的索引

```text
INDEX idx_orders_opt_issue_id (opt_issue_id)

INDEX idx_oco_order_id (order_id)
INDEX idx_oco_opt_issue_id (opt_issue_id)
INDEX idx_oco_opt_job_id (opt_job_id)
INDEX idx_oco_status (status)
INDEX idx_oco_order_status (order_id, status)
INDEX idx_oco_order_simtype (order_id, sim_type_id)
INDEX idx_oco_order_foldtype (order_id, fold_type_id)
```

### 7.4 上线后建议补充的外键

这部分只作为后续优化建议，不建议第一阶段就加。

建议补充的外键：

- `order_condition_opti.order_id -> orders.id`

可选外键：

- `order_condition_opti.sim_type_id -> sim_types.id`
- `order_condition_opti.fold_type_id -> fold_types.id`

当前不建议加的外键：

- 指向外部自动化库的 `opt_issue_id`
- 指向外部自动化库的 `opt_job_id`

原因：

- 跨库主键不应在当前库做强外键
- 当前导数、同步、导入流程对强外键不友好

## 8. 推荐 SQL 草案

```sql
ALTER TABLE orders
ADD COLUMN opt_issue_id INT NULL COMMENT '自动优化申请单ID',
ADD INDEX idx_orders_opt_issue_id (opt_issue_id);

CREATE TABLE order_condition_opti (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL COMMENT '主单ID',
  order_no VARCHAR(50) NULL COMMENT '主单编号冗余',
  opt_issue_id INT NOT NULL COMMENT '自动优化申请单ID',
  opt_job_id INT NULL COMMENT '自动化方案作业ID',
  condition_id BIGINT NOT NULL COMMENT 'condition标识',
  fold_type_id INT NOT NULL COMMENT '姿态ID',
  fold_type_name VARCHAR(100) NULL COMMENT '姿态名称快照',
  sim_type_id INT NOT NULL COMMENT '仿真类型ID',
  sim_type_name VARCHAR(100) NULL COMMENT '仿真类型名称快照',
  algorithm_type VARCHAR(32) NULL COMMENT '算法类型',
  round_total INT DEFAULT 0 COMMENT '轮次数量概览',
  output_count INT DEFAULT 0 COMMENT '输出数量概览',
  solver_id VARCHAR(64) NULL COMMENT '求解器标识，包含类型和版本语义',
  care_device_ids JSON NULL COMMENT '关注器件ID列表',
  remark TEXT NULL COMMENT 'condition级备注',
  running_module VARCHAR(64) NULL COMMENT '当前运行模块',
  process DECIMAL(5,2) DEFAULT 0 COMMENT '进度百分比',
  status SMALLINT DEFAULT 0 COMMENT '状态',
  statistics_json JSON NULL COMMENT '统计摘要',
  result_summary_json JSON NULL COMMENT '结果摘要',
  condition_snapshot JSON NOT NULL COMMENT '完整condition快照',
  external_meta JSON NULL COMMENT '外部扩展信息',
  created_at BIGINT NOT NULL,
  updated_at BIGINT NOT NULL,

  UNIQUE KEY uk_oco_order_condition (order_id, condition_id),
  UNIQUE KEY uk_oco_opt_job_id (opt_job_id),
  KEY idx_oco_order_id (order_id),
  KEY idx_oco_opt_issue_id (opt_issue_id),
  KEY idx_oco_opt_job_id (opt_job_id),
  KEY idx_oco_status (status),
  KEY idx_oco_order_status (order_id, status),
  KEY idx_oco_order_simtype (order_id, sim_type_id),
  KEY idx_oco_order_foldtype (order_id, fold_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单condition优化运行实体表';
```

## 9. 与当前 `inputJson` 的映射关系

当前提单提交结构中的：

```json
{
  "inputJson": {
    "conditions": [
      {
        "conditionId": 101,
        "foldTypeId": 1,
        "foldTypeName": "A",
        "simTypeId": 11,
        "simTypeName": "DOE",
        "params": {},
        "output": {},
        "solver": {},
        "careDeviceIds": []
      }
    ]
  }
}
```

提交后建议落库方式：

- `orders.input_json` 原样保留
- `inputJson.conditions` 每一项拆成一条 `order_condition_opti`
- `orders.opt_issue_id` 在创建自动化主单后回填
- `order_condition_opti.opt_job_id` 在创建外部 job 后逐条回填

其中映射规则建议如下：

| inputJson 字段 | order_condition_opti 字段 |
| --- | --- |
| `conditionId` | `condition_id` |
| `foldTypeId` | `fold_type_id` |
| `foldTypeName` | `fold_type_name` |
| `simTypeId` | `sim_type_id` |
| `simTypeName` | `sim_type_name` |
| `solver.solverId / code` | `solver_id` |
| `careDeviceIds` | `care_device_ids` |
| `output` 派生 | `output_count` |
| `params.optParams.algType` | `algorithm_type` |
| 当前完整节点 | `condition_snapshot` |

## 10. 与自动化库的关联方式

### 10.1 issue 层

`orders.opt_issue_id` 对应自动化库主申请单。

建议用途：

- 查询该订单对应外部主流程
- 查询该订单下所有方案
- 做主单级结果汇总

### 10.2 job 层

`order_condition_opti.opt_job_id` 对应自动化库中的一个具体方案。

建议用途：

- 查询单个 condition 的轮次结果
- 查询单个方案进度
- 查询单个方案统计与图表数据

### 10.3 推荐查询入口

推荐结果页主查询入口改为：

1. 前端先拿 `order_id`
2. 查询 `order_condition_opti` 列表
3. 用户选择一个 `order_condition_id`
4. 后端根据其 `opt_job_id` 去自动化库查询真实结果

这样结果页主实体会从“主单”切到“方案”。

## 11. `final_result` 的业务语义

`final_result` 不属于 `order_condition_opti`。
它属于轮次级结果字段，应位于结果数据或 mock 轮次数据中。

### 11.1 DOE

- `final_result = NULL`
- 前端不展示 `final_result`

### 11.2 贝叶斯

- `final_result` 表示单一轮次根据加权规则计算出的总结果
- 该值由自动化流程计算后入库
- 当前业务库只负责查询与展示
- 该值用于寻优和下一批次参数生成的判断依据

### 11.3 当前明确不需要的字段

当前不建议新增：

- `weighted_score`

原因：

- 贝叶斯没有额外独立的 `weighted_score` 字段需求
- 加权逻辑已经由提单输出配置定义
- 自动化库会直接写入最终可消费结果

## 12. 统计与进度

统计信息当前允许两种来源：

1. 查询接口实时计算
2. 本地根据完整结果生成摘要

适合统计的内容包括：

- 当前 condition 的计算进度
- 完成轮次
- 失败比例
- 成功比例
- 最优轮次
- 输出结果概览

因此：

- `statistics_json` 可以保留
- 但不强制要求第一阶段就落全量统计

## 13. 结果页目标结构

### 13.1 最小结果页主入口

最小结果页应按 `order_condition_id` 展示一个方案。

### 13.2 DOE 表格建议

表头可先固定为：

```text
轮次,param1,param2,param3,output1,output2,output3,running_module,process,status
```

说明：

- DOE 不展示 `final_result`
- DOE 不展示输出加权列

### 13.3 贝叶斯表格建议

表头建议为：

```text
轮次,param1,param2,param3,output1,output1_加权,output2,output2_加权,output3,output3_加权,running_module,process,final_result
```

说明：

- 贝叶斯展示 `final_result`
- 每个输出项可带对应加权结果列
- 不新增单独 `weighted_score` 总字段
- `process` 建议结合 `running_module + status` 以进度条形式展示
- 颜色用于区分状态
- 悬浮提示展示完整模块信息卡片

模块信息卡片建议至少包含：

- 模块名称
- 模块状态
- 模块完成进度
- 模块耗时
- 是否失败及失败原因

### 13.4 图表建议分阶段推进

P0：

- 参数趋势图
- 输出趋势图
- 轮次结果表
- 进度与统计摘要

P1：

- 2D 参数-输出散点图
- 3D 参数-输出散点图
- 帕累托图

P2：

- 3D 响应曲面图
- 自动报告
- 结果摘要与标注分析

## 14. 开发环境 mock 方案

由于当前开发环境无法连接自动化结果库，建议第一阶段直接使用 mock。

### 14.1 方案一：mock 表

可选建立以下 mock 表：

```text
mock_opt_issues
mock_opt_jobs
mock_opt_params
mock_opt_resps
mock_opt_rounds
mock_opt_data
```

推荐关系：

- `mock_opt_issues.id`
- `mock_opt_jobs.issue_id -> mock_opt_issues.id`
- `mock_opt_rounds.job_id -> mock_opt_jobs.id`
- `mock_opt_data.round_id -> mock_opt_rounds.id`
- `mock_opt_data.resp_config_id -> mock_opt_resps.id`

### 14.2 方案二：mock JSON 直返

也可以不建表，直接通过 mock 接口返回 JSON。

推荐返回结构：

```json
{
  "issueId": 1001,
  "jobId": 2001,
  "rounds": [
    {
      "roundIndex": 1,
      "params": {},
      "outputs": {},
      "runningModule": "solver",
      "process": 100,
      "status": 2,
      "finalResult": null
    }
  ],
  "statistics": {
    "totalRounds": 10,
    "completedRounds": 8,
    "failedRounds": 2
  }
}
```

如果是贝叶斯，可扩展为：

```json
{
  "issueId": 1001,
  "jobId": 2001,
  "rounds": [
    {
      "roundIndex": 1,
      "params": {
        "param1": 1.1,
        "param2": 2.2
      },
      "outputs": {
        "output1": 10.5,
        "output1Weighted": 3.5,
        "output2": 20.5,
        "output2Weighted": 6.0,
        "output3": 30.5,
        "output3Weighted": 9.2
      },
      "runningModule": "post_process",
      "process": 100,
      "status": 2,
      "finalResult": 18.7,
      "moduleDetails": [
        {
          "module": "prepare",
          "status": 2,
          "progress": 100,
          "durationSec": 12
        },
        {
          "module": "solver",
          "status": 2,
          "progress": 100,
          "durationSec": 248
        }
      ]
    }
  ]
}
```

### 14.3 当前推荐

如果目标是更快推进，优先推荐：

- 先做 mock 接口
- 直接返回 mock JSON
- 后续你自己补充真实查询逻辑

原因：

- 改动更小
- 不依赖当前环境数据库联通
- 便于前端先行联调结果页

## 15. 最快上线建议

### 15.1 第一阶段必须完成

1. `orders` 增加 `opt_issue_id`
2. 新增 `order_condition_opti`
3. 提单提交时同步拆分 `inputJson.conditions`
4. 结果查询改为支持 `order_condition_id -> opt_job_id`
5. 列表页继续保留 `simTypeIds` 快速筛选
6. 开发环境先用 mock 接口 / mock JSON 打通结果链路

### 15.2 第二阶段再做

1. condition 级状态与统计实时同步
2. 结果图表增强
3. 自动报告
4. 高级工业分析图

### 15.3 当前不建议先做

- 大规模重构现有提单页
- 一次性铺完所有图表
- 先做复杂权限细分再做结果主链路
- 第一阶段就上大量数据库外键

## 16. 需要继续确认的点

当前还建议你后续继续确认：

1. `order_condition_opti` 是否允许保留历史版本，还是始终一条记录覆盖更新
2. `statistics_json` 是只做缓存，还是作为正式展示来源
3. mock 接口是直接挂在当前后端，还是单独走 mock 模块

## 17. 当前结论

如果目标是更快推进，这套模型比继续强化 `conditionSummary` 或继续堆在 `orders.input_json` 上更合理。

核心原因：

- `simTypeIds` 继续负责主单快速筛选
- `orders` 继续做主单头
- `order_condition_opti` 成为真正的方案实体
- `opt_issue_id` 与 `opt_job_id` 把当前业务库和自动化库串起来
- 第一阶段不加外键，更适合当前导数与内网同步方式
- 开发环境先用 mock，更符合当前环境限制
