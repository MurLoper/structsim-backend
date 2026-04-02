# Platform API

## 1. Bootstrap

`GET /api/v1/platform/bootstrap`

返回：

- 公告轮询周期
- 当前有效公告
- 埋点是否启用
- 当前用户是否已同意隐私协议

## 2. 隐私协议

### 获取隐私协议

`GET /api/v1/platform/privacy-policy`

### 同意隐私协议

`POST /api/v1/platform/privacy-policy/accept`

请求体：

```json
{
  "policyVersion": "1.0.0"
}
```

## 3. 埋点事件

### 批量上报事件

`POST /api/v1/platform/events`

请求体：

```json
{
  "events": [
    {
      "eventName": "page_view",
      "eventType": "navigation",
      "pagePath": "/orders",
      "target": "orders",
      "sessionId": "session-001",
      "metadata": {
        "source": "route"
      },
      "occurredAt": 1712040000
    }
  ]
}
```

## 4. 埋点分析

`GET /api/v1/platform/analytics/summary?days=7`

权限要求：
- `VIEW_DASHBOARD`

返回：

- 总事件数
- 活跃用户数
- 页面访问数
- 公告曝光数
- 隐私协议确认数
- 时间趋势
- 高频事件
- 高频页面

## 5. 平台内容管理

### 获取平台内容

`GET /api/v1/platform/admin/content`

权限要求：
- `MANAGE_CONFIG`

### 更新平台配置

`PUT /api/v1/platform/admin/content`

可更新字段：

- `announcementPollIntervalSeconds`
- `trackingEnabled`
- `privacyPolicyRequired`
- `privacyPolicyTitle`
- `privacyPolicyVersion`
- `privacyPolicySummary`
- `privacyPolicyContent`

### 新建公告

`POST /api/v1/platform/admin/announcements`

### 更新公告

`PUT /api/v1/platform/admin/announcements/:id`

### 删除公告

`DELETE /api/v1/platform/admin/announcements/:id`

以上平台配置与公告管理接口统一要求：
- `MANAGE_CONFIG`
