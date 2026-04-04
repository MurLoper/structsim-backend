# Platform API

适用范围：`structsim-backend` 平台治理相关接口

## 1. 前端入口与权限

平台功能固定入口如下：

- 公告查看：前端布局顶部公告横幅
- 公告配置：系统配置 -> 平台内容
- 埋点分析查看：`/analytics`
- 隐私协议查看：头像菜单 -> 查看隐私协议

权限边界固定如下：

- 埋点分析：`VIEW_DASHBOARD`
- 平台内容与公告管理：`MANAGE_CONFIG`
- 隐私协议查看：所有已登录用户都可访问

## 2. Bootstrap

### `GET /api/v1/platform/bootstrap`

返回当前平台基础配置：

- 公告轮询周期
- 当前有效公告
- 埋点是否启用
- 当前用户是否已同意隐私协议

## 3. 隐私协议

### `GET /api/v1/platform/privacy-policy`

获取当前隐私协议详情，包含：

- 标题
- 版本
- 摘要
- 正文
- 当前用户是否已同意

### `POST /api/v1/platform/privacy-policy/accept`

请求体：

```json
{
  "policyVersion": "1.0.0"
}
```

用于记录当前用户对指定版本隐私协议的确认。

## 4. 埋点事件

### `POST /api/v1/platform/events`

前端通过本地队列批量上报埋点事件。后端只负责写入与统计汇总，不依赖任何外网第三方统计平台。

当前平台埋点体系为内网自有体系，工作方式如下：

- 路由切换自动采集 `page_view`
- 公告曝光、关闭、点击分别采集
- 隐私协议查看、同意分别采集
- 仪表盘、申请单列表、提交页、结果页、平台配置页的关键操作按功能级事件采集

请求体：

```json
{
  "events": [
    {
      "eventName": "orders.result_open",
      "eventType": "navigation",
      "pagePath": "/orders",
      "target": "123",
      "sessionId": "session-001",
      "metadata": {
        "pageKey": "orders.list",
        "featureKey": "orders.result.open",
        "moduleKey": "orders",
        "entityId": 123,
        "result": "success"
      },
      "occurredAt": 1712040000
    }
  ]
}
```

标准 metadata 约定：

- `pageKey`
- `featureKey`
- `moduleKey`
- `result`
- `step`
- `entityId`
- `orderNo`
- `durationMs`

## 5. 埋点分析

### `GET /api/v1/platform/analytics/summary?days=7`

返回：

- 总事件数
- 活跃用户数
- 页面访问数
- 公告曝光数
- 隐私确认数
- 功能事件数
- 成功/失败事件数
- 时间趋势
- 高频事件
- 热门页面
- 热门模块

### `GET /api/v1/platform/analytics/features?days=7`

返回：

- 页面使用次数排行
- 功能使用次数排行
- 模块使用次数排行

说明：

- 页面统计只按 `page_view` 聚合
- 功能统计按 `featureKey + eventName` 聚合

### `GET /api/v1/platform/analytics/funnels?days=7`

返回关键流程转化数据，例如：

- 仪表盘快捷入口 -> 提交成功 -> 结果查看
- 申请单列表 -> 结果查看

### `GET /api/v1/platform/analytics/failures?days=7`

返回失败热点：

- 失败事件排行
- 失败页面排行
- 失败功能排行

## 6. 平台内容管理

### `GET /api/v1/platform/admin/content`

权限要求：`MANAGE_CONFIG`

返回：

- 平台设置
- 公告列表

### `PUT /api/v1/platform/admin/content`

权限要求：`MANAGE_CONFIG`

可更新字段：

- `announcementPollIntervalSeconds`
- `trackingEnabled`
- `privacyPolicyRequired`
- `privacyPolicyTitle`
- `privacyPolicyVersion`
- `privacyPolicySummary`
- `privacyPolicyContent`

### `POST /api/v1/platform/admin/announcements`

权限要求：`MANAGE_CONFIG`

### `PUT /api/v1/platform/admin/announcements/:id`

权限要求：`MANAGE_CONFIG`

### `DELETE /api/v1/platform/admin/announcements/:id`

权限要求：`MANAGE_CONFIG`

公告支持这些能力：

- 启用 / 停用
- 排序
- 生效时间窗
- 是否允许关闭
- 跳转链接
- 创建人与更新人记录
