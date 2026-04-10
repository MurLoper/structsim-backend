# 提单初始化与快照协议

最后更新：2026-04-10

## 1. 目标

这份文档只说明当前提单主链路的协议边界，避免再把“用户上下文、项目上下文、默认工况模板、申请单实例”混在一起。

当前统一口径：

- 项目不直接关联仿真类型
- 项目也不直接关联 `conditionId`
- `conditionId` 只在提单时作为申请单内工况配置主键
- 默认快速提单链路以默认工况配置展开为真源
- 可见项目列表、资源池列表属于用户权限上下文，提单页懒加载
- 项目阶段、参与人候选、项目文件相关信息属于项目上下文

## 2. 四层数据边界

### 2.1 用户基础会话

由 `GET /api/v1/auth/session` 返回，只保留首屏必须信息：

- 当前用户
- 权限
- 菜单
- 提单限制
  - 用户可提单上限
  - 日提单上限
  - 当日已用
  - 当日剩余
- 最近常用项目 ID 列表

注意：

- 不在 session 中返回可见项目列表
- 不在 session 中返回资源池列表

### 2.2 懒加载用户上下文

进入提单页后并行加载：

- 可见项目列表
- 用户资源池列表
- 默认资源池

规则：

1. 最近常用项目优先作为默认项目
2. 若最近常用项目不在可见项目列表中，则顺延到下一条可见常用项目
3. 若最近常用全部失效，则回退到可见项目第一项
4. 资源池接口未配置或调用失败时，由后端直接返回 mock 资源池

## 3. 项目上下文接口

### 3.1 正式接口

```http
GET /api/v1/orders/init-project-config?projectId={id}&simTypeId={id?}
```

### 3.2 兼容接口

```http
GET /api/v1/orders/init-config?projectId={id}&simTypeId={id?}
```

兼容接口仅作薄包装，内部转发到新实现，不再承载独立逻辑。

### 3.3 当前职责

项目上下文接口只负责返回和当前项目直接相关的数据：

- `projectId`
- `projectName`
- `phases`
- `defaultPhaseId`
- `participantCandidates`
- 项目源文件相关默认项
- 默认工况展开后得到的：
  - `defaultParamGroup`
  - `defaultCondOutGroup`
  - `defaultSolver`
  - `paramGroupOptions`
  - `condOutGroupOptions`
  - `solverOptions`

### 3.4 阶段规则

默认阶段：

```sql
SELECT phase_id
FROM simlation_project.pp_phase
WHERE pp_record_id = :project_id
ORDER BY pp_phase_id DESC
LIMIT 1
```

阶段列表：

- 先从 `pp_phase` 中取当前项目出现过的 `phase_id`
- 再关联 `phase` 表取名称
- 去重后返回
- 若阶段名称缺失或乱码，后端兜底为 `阶段-{phaseId}`

### 3.5 参与人候选规则

参与人候选集来源是全量用户，但按项目上下文排序后返回。

排序优先级固定为：

1. 已勾选用户
2. 当前项目历史常选参与人
3. 其余用户

说明：

- 参与人是提单全局字段，不是工况级字段
- 参与人为可选可不选
- 历史常选参与人当前先基于历史订单统计

## 4. 默认快速提单链路

默认快速提单不新增独立模板体系，继续使用“默认工况配置展开”。

默认值来源：

- 折叠态 / 展开态下的默认工况
- `condition_config` 中的默认参数组
- `condition_config` 中的默认输出组
- `condition_config` 中的默认求解器

参数组和输出组过滤规则：

- 显式关联当前项目：可用
- 未关联任何项目：视为全部项目可用

关注器件不属于默认模板核心项，不做默认值。

## 5. 提交快照协议

`inputJson` 是当前唯一可信主快照。

推荐结构：

```json
{
  "version": 2,
  "projectInfo": {},
  "conditions": [],
  "globalSolver": {},
  "inpSets": []
}
```

说明：

- `projectInfo` 保存项目级信息
- `conditions` 保存本次提单实例中实际勾选的工况配置
- `conditionId` 只在这里作为申请单内主键使用

`optParam` 仅作为历史兼容字段保留，不再作为新链路主语义。

## 6. 结果

当前提单初始化正式分层如下：

1. `auth/session`：用户基础会话
2. 用户懒加载查询：可见项目、资源池
3. `orders/init-project-config`：项目上下文
4. `inputJson.conditions`：申请单实例级工况配置

后续所有联调、回填和问题定位，都应按这四层判断来源，不再把旧的 `init-config` 当作整页唯一初始化接口。
