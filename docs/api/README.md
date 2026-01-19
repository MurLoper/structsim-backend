# API 文档

## 概览

StructSim AI Platform 后端提供 RESTful API，基于 Flask 3.x 构建。

**Base URL**: `http://127.0.0.1:5000/api/v1`

---

## API 分类

### 认证 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/auth/login` | POST | 用户登录 |
| `/auth/logout` | POST | 用户登出 |
| `/auth/refresh` | POST | 刷新Token |

### 基础配置 API (7组)

| 资源 | 端点前缀 | CRUD |
|------|----------|------|
| 项目 | `/config/projects` | ✅ |
| 仿真类型 | `/config/sim-types` | ✅ |
| 参数定义 | `/config/param-defs` | ✅ |
| 求解器 | `/config/solvers` | ✅ |
| 工况定义 | `/config/condition-defs` | ✅ |
| 输出定义 | `/config/output-defs` | ✅ |
| 姿态类型 | `/config/fold-types` | ✅ |

### 组合配置 API (2组)

| 资源 | 端点前缀 | 操作 |
|------|----------|------|
| 参数组合 | `/config/param-groups` | CRUD + 参数管理 |
| 工况输出组合 | `/config/cond-out-groups` | CRUD + 工况/输出管理 |

### 关联配置 API (4组)

| 资源 | 端点前缀 | 操作 |
|------|----------|------|
| 项目-仿真类型 | `/config/relations/project-sim-types` | 关联管理 |
| 仿真类型-参数组合 | `/config/relations/sim-type-param-groups` | 关联管理 |
| 仿真类型-工况输出组合 | `/config/relations/sim-type-cond-out-groups` | 关联管理 |
| 仿真类型-求解器 | `/config/relations/sim-type-solvers` | 关联管理 |

### 订单 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/orders` | GET | 获取订单列表 |
| `/orders` | POST | 创建订单 |
| `/orders/{id}` | GET | 获取订单详情 |
| `/orders/{id}` | PUT | 更新订单 |
| `/orders/{id}` | DELETE | 删除订单 |
| `/orders/init-config` | GET | 获取初始化配置 |

---

## 统一响应格式

### 成功响应

```json
{
  "code": 0,
  "msg": "ok",
  "data": { ... },
  "trace_id": "abc123"
}
```

### 错误响应

```json
{
  "code": 400001,
  "msg": "参数错误",
  "data": null,
  "trace_id": "abc123"
}
```

### 错误码范围

| 范围 | 描述 |
|------|------|
| 400xxx | 参数错误 |
| 401xxx | 认证错误 |
| 403xxx | 权限错误 |
| 404xxx | 资源不存在 |
| 409xxx | 业务冲突 |
| 500xxx | 服务器错误 |

---

## 认证

使用 JWT Token 认证。

### 请求头

```
Authorization: Bearer <token>
```

### Token 刷新

Token 过期后，使用 refresh token 获取新 token。

---

## 分页

### 请求参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

### 响应格式

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

---

## 待完成

- [ ] Swagger/OpenAPI 集成
- [ ] 详细的请求/响应示例
- [ ] 错误码完整列表

---

**最后更新**: 2024-01-18
