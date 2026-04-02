# Platform API

## 平台功能使用路径

- 公告查看：前端布局顶部公告横幅
- 公告配置：系统配置 -> 平台内容
- 埋点分析查看：`/analytics`
- 隐私协议查看：头像菜单 -> 查看隐私协议

权限边界：

- 埋点分析：`VIEW_DASHBOARD`
- 平台内容与公告管理：`MANAGE_CONFIG`
- 隐私协议查看：所有已登录用户可访问

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

埋点实现方式：

- 前端通过本地队列批量上报
- 路由切换自动采集 `page_view`
- 公告曝光/关闭分别采集
- 隐私协议查看/同意分别采集
- 后端负责事件写入与汇总，不依赖第三方统计平台

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
