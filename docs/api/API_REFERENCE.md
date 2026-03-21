# 后端 API 参考文档

面向当前仓库的接口参考摘要，优先描述主链路与稳定接口。

**最后更新**: 2026-03-21

---

## 📋 目录

1. [API 概述](#1-api-概述)
2. [认证 API](#2-认证-api)
3. [配置管理 API](#3-配置管理-api)
4. [权限管理 API](#4-权限管理-api)
5. [订单管理 API](#5-订单管理-api)
6. [结果 API](#6-结果-api)
7. [错误处理](#7-错误处理)

---

## 1. API 概述

### 1.1 基础信息

- **Base URL**: `http://127.0.0.1:6060/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **命名约定**: 前端可使用 `camelCase`，服务端内部为 `snake_case`

### 1.2 统一响应格式

```json
{
  "code": 0,           // 0=成功, 其他=失败
  "msg": "ok",         // 提示信息
  "data": {},          // 响应数据
  "trace_id": "abc123" // 追踪ID
}
```

### 1.3 分页响应格式

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [],       // 数据列表
    "total": 100,      // 总记录数
    "page": 1,         // 当前页码
    "page_size": 20,   // 每页大小
    "pages": 5         // 总页数
  },
  "trace_id": "abc123"
}
```

### 1.4 错误码

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| 0 | 成功 | 200 |
| 400001 | 参数验证失败 | 400 |
| 401001 | 未认证 | 401 |
| 403001 | 无权限 | 403 |
| 404001 | 资源不存在 | 404 |
| 500001 | 服务器错误 | 500 |

---

## 2. 认证 API

### 2.1 用户登录

**接口**: `POST /auth/login`

**请求参数**:
```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

**响应示例**:
```json
{
  "code": 0,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "realName": "管理员",
      "email": "admin@example.com",
      "roles": ["admin"]
    }
  },
  "trace_id": "abc123"
}
```

### 2.2 用户登出

**接口**: `POST /auth/logout`

**请求头**:
```
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "code": 0,
  "msg": "登出成功",
  "data": null,
  "trace_id": "abc123"
}
```

### 2.3 获取当前用户信息

**接口**: `GET /auth/me`

**请求头**:
```
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": 1,
    "username": "admin",
    "realName": "管理员",
    "email": "admin@example.com",
    "roles": ["admin"],
    "permissions": ["config:read", "config:write"]
  },
  "trace_id": "abc123"
}
```

### 2.4 校验 token

**接口**: `GET /auth/verify`

**说明**:

- 返回当前用户信息与菜单树
- 前端登录恢复和页面初始化优先使用该接口

### 2.5 刷新 token

**接口**: `POST /auth/refresh`

### 2.6 登录心跳

**接口**: `GET /auth/heartbeat`

---

## 3. 配置管理 API

### 3.1 项目管理

#### 3.1.1 获取项目列表

**接口**: `GET /config/projects`

**查询参数**:
- `page` (可选): 页码，默认 1
- `page_size` (可选): 每页大小，默认 20
- `valid` (可选): 是否有效，1=有效，0=禁用

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "项目A",
      "code": "PROJECT_A",
      "defaultSimTypeId": 1,
      "defaultSolverId": 1,
      "valid": 1,
      "sort": 100,
      "remark": "备注",
      "createdAt": 1705564800,
      "updatedAt": 1705564800
    }
  ],
  "trace_id": "abc123"
}
```

#### 3.1.2 获取单个项目

**接口**: `GET /config/projects/:id`

**路径参数**:
- `id`: 项目ID

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": 1,
    "name": "项目A",
    "code": "PROJECT_A",
    "defaultSimTypeId": 1,
    "defaultSolverId": 1,
    "valid": 1,
    "sort": 100,
    "remark": "备注",
    "createdAt": 1705564800,
    "updatedAt": 1705564800
  },
  "trace_id": "abc123"
}
```

#### 3.1.3 创建项目

**接口**: `POST /config/projects`

**请求参数**:
```json
{
  "name": "项目A",
  "code": "PROJECT_A",
  "defaultSimTypeId": 1,
  "defaultSolverId": 1,
  "valid": 1,
  "sort": 100,
  "remark": "备注"
}
```

**响应示例**:
```json
{
  "code": 0,
  "msg": "创建成功",
  "data": {
    "id": 1,
    "name": "项目A",
    "code": "PROJECT_A",
    ...
  },
  "trace_id": "abc123"
}
```

#### 3.1.4 更新项目

**接口**: `PUT /config/projects/:id`

**路径参数**:
- `id`: 项目ID

**请求参数**:
```json
{
  "name": "项目A（已更新）",
  "defaultSimTypeId": 2,
  "remark": "更新后的备注"
}
```

**响应示例**:
```json
{
  "code": 0,
  "msg": "更新成功",
  "data": {
    "id": 1,
    "name": "项目A（已更新）",
    ...
  },
  "trace_id": "abc123"
}
```

#### 3.1.5 删除项目

**接口**: `DELETE /config/projects/:id`

**路径参数**:
- `id`: 项目ID

**响应示例**:
```json
{
  "code": 0,
  "msg": "删除成功",
  "data": null,
  "trace_id": "abc123"
}
```

---

### 3.2 仿真类型管理

#### 3.2.1 获取仿真类型列表

**接口**: `GET /config/sim-types`

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "结构分析",
      "code": "STRUCTURE",
      "category": "STRUCTURE",
      "defaultParamTplSetId": 1,
      "defaultCondOutSetId": 1,
      "defaultSolverId": 1,
      "supportAlgMask": 3,
      "nodeIcon": "structure.svg",
      "colorTag": "#FF5500",
      "valid": 1,
      "sort": 100
    }
  ],
  "trace_id": "abc123"
}
```

#### 3.2.2 创建仿真类型

**接口**: `POST /config/sim-types`

**请求参数**:
```json
{
  "name": "结构分析",
  "code": "STRUCTURE",
  "category": "STRUCTURE",
  "defaultParamTplSetId": 1,
  "defaultCondOutSetId": 1,
  "defaultSolverId": 1,
  "supportAlgMask": 3,
  "nodeIcon": "structure.svg",
  "colorTag": "#FF5500",
  "valid": 1,
  "sort": 100
}
```

---

### 3.3 参数定义管理

#### 3.3.1 获取参数定义列表

**接口**: `GET /config/param-defs`

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "厚度",
      "key": "thickness",
      "valType": 1,
      "unit": "mm",
      "minVal": 0.1,
      "maxVal": 10.0,
      "precision": 2,
      "defaultVal": "1.0",
      "enumOptions": null,
      "required": 1,
      "valid": 1,
      "sort": 100
    }
  ],
  "trace_id": "abc123"
}
```

#### 3.3.2 创建参数定义

**接口**: `POST /config/param-defs`

**请求参数**:
```json
{
  "name": "厚度",
  "key": "thickness",
  "valType": 1,
  "unit": "mm",
  "minVal": 0.1,
  "maxVal": 10.0,
  "precision": 2,
  "defaultVal": "1.0",
  "required": 1,
  "valid": 1,
  "sort": 100
}
```

#### 3.3.3 更新参数定义

**接口**: `PUT /config/param-defs/:id`

**请求参数** (驼峰命名):
```json
{
  "name": "厚度（已更新）",
  "minVal": 0.2,
  "maxVal": 20.0,
  "defaultVal": "2.0"
}
```

**注意**: 
- ✅ 前端发送驼峰命名 (`minVal`, `maxVal`, `defaultVal`)
- ✅ 后端自动转换为下划线命名 (`min_val`, `max_val`, `default_val`)
- ✅ 使用 Pydantic 字段别名实现

---

### 3.4 参数组管理

#### 3.4.1 获取参数组列表

**接口**: `GET /config/param-groups`

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "材料参数组",
      "description": "材料相关参数",
      "valid": 1,
      "sort": 100,
      "params": [
        {
          "paramDefId": 1,
          "paramDef": {
            "id": 1,
            "name": "厚度",
            "key": "thickness"
          }
        }
      ]
    }
  ],
  "trace_id": "abc123"
}
```

---

## 4. 权限管理 API

### 4.1 获取角色列表

**接口**: `GET /rbac/roles`

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "管理员",
      "code": "admin",
      "description": "系统管理员",
      "permissions": ["*"]
    }
  ],
  "trace_id": "abc123"
}
```

### 4.2 获取权限列表

**接口**: `GET /rbac/permissions`

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "配置读取",
      "code": "config:read",
      "resource": "config",
      "action": "read"
    }
  ],
  "trace_id": "abc123"
}
```

---

## 5. 订单管理 API

### 5.1 获取订单列表

**接口**: `GET /orders`

**查询参数**:
- `page`: 页码
- `page_size`: 每页大小
- `status`: 订单状态

**响应示例**:
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": 1,
        "orderNo": "ORD20250118001",
        "projectId": 1,
        "simTypeId": 1,
        "status": "pending",
        "createdAt": 1705564800
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  },
  "trace_id": "abc123"
}
```

---

### 5.2 获取订单详情

**接口**: `GET /orders/:id`

### 5.3 创建订单

**接口**: `POST /orders`

**说明**:

- 当前订单创建接口是提单主链路核心接口
- 请求体重点字段包括 `projectId`、`modelLevelId`、`originFile`、`foldTypeIds`、`participantIds`、`simTypeIds`、`inputJson`、`optParam`

### 5.4 文件校验

**接口**: `POST /orders/verify-file`

### 5.5 统计接口

- `GET /orders/statistics`
- `GET /orders/trends`
- `GET /orders/status-distribution`

说明：

- `GET /orders/:id/result` 在当前代码中仍为空实现，不作为主结果接口

---

## 6. 结果 API

### 6.1 获取订单下的仿真类型结果

**接口**: `GET /results/order/:order_id/sim-types`

### 6.2 获取单个仿真类型结果详情

**接口**: `GET /results/sim-type/:result_id`

### 6.3 获取轮次分页数据

**接口**: `GET /results/sim-type/:result_id/rounds`

### 6.4 更新结果状态

- `PATCH /results/sim-type/:result_id/status`
- `PATCH /results/round/:round_id/status`

---

## 7. 错误处理

### 6.1 验证错误

**响应示例**:
```json
{
  "code": 400001,
  "msg": "参数验证失败: name字段必填",
  "data": {
    "errors": [
      {
        "field": "name",
        "message": "name字段必填"
      }
    ]
  },
  "trace_id": "abc123"
}
```

### 6.2 认证错误

**响应示例**:
```json
{
  "code": 401001,
  "msg": "未认证，请先登录",
  "data": null,
  "trace_id": "abc123"
}
```

### 6.3 权限错误

**响应示例**:
```json
{
  "code": 403001,
  "msg": "无权限访问该资源",
  "data": null,
  "trace_id": "abc123"
}
```

### 6.4 资源不存在

**响应示例**:
```json
{
  "code": 404001,
  "msg": "项目不存在",
  "data": null,
  "trace_id": "abc123"
}
```

---
