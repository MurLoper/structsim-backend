# API 设计规范

## RESTful API 设计原则

### 1. URL 设计

#### 1.1 版本控制
- 使用URL路径版本：`/api/v1/...`
- 主版本号变更时创建新版本

#### 1.2 资源命名
- 使用名词复数：`/orders`, `/users`, `/projects`
- 避免动词：❌ `/getOrders`, ✅ `/orders`
- 使用小写字母和连字符：`/sim-types`

#### 1.3 层级关系
```
GET    /api/v1/orders              # 获取订单列表
GET    /api/v1/orders/:id          # 获取单个订单
POST   /api/v1/orders              # 创建订单
PUT    /api/v1/orders/:id          # 更新订单
DELETE /api/v1/orders/:id          # 删除订单
GET    /api/v1/orders/:id/result   # 获取订单结果
```

### 2. HTTP 方法

| 方法 | 用途 | 幂等性 |
|------|------|--------|
| GET | 查询资源 | ✅ |
| POST | 创建资源 | ❌ |
| PUT | 更新资源（全量） | ✅ |
| PATCH | 更新资源（部分） | ❌ |
| DELETE | 删除资源 | ✅ |

### 3. 状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | OK | 成功 |
| 201 | Created | 创建成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器错误 |

### 4. 统一响应格式

#### 4.1 成功响应
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    // 业务数据
  },
  "trace_id": "abc123"
}
```

#### 4.2 错误响应
```json
{
  "code": 400001,
  "msg": "参数错误",
  "data": null,
  "trace_id": "abc123"
}
```

#### 4.3 分页响应
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  },
  "trace_id": "abc123"
}
```

### 5. 查询参数

#### 5.1 分页
```
GET /api/v1/orders?page=1&pageSize=20
```

#### 5.2 过滤
```
GET /api/v1/orders?status=1&projectId=10
```

#### 5.3 排序
```
GET /api/v1/orders?sortBy=createdAt&order=desc
```

#### 5.4 字段选择
```
GET /api/v1/orders?fields=id,name,status
```

### 6. 请求体设计

#### 6.1 创建资源
```json
POST /api/v1/orders
{
  "projectId": 1,
  "simTypeIds": [1, 2],
  "remark": "测试订单"
}
```

#### 6.2 更新资源
```json
PUT /api/v1/orders/1
{
  "remark": "更新备注",
  "status": 2
}
```

### 7. 错误码设计

| 范围 | 说明 | 示例 |
|------|------|------|
| 0 | 成功 | 0 |
| 400xxx | 参数错误 | 400001: 参数缺失 |
| 401xxx | 认证错误 | 401001: 未登录 |
| 403xxx | 权限错误 | 403001: 无权限 |
| 404xxx | 资源不存在 | 404001: 订单不存在 |
| 500xxx | 服务器错误 | 500001: 内部错误 |

### 8. 认证授权

#### 8.1 JWT Token
```
Authorization: Bearer <token>
```

#### 8.2 Token 刷新
```
POST /api/v1/auth/refresh
{
  "refreshToken": "..."
}
```

### 9. 最佳实践

#### 9.1 使用 HTTPS
- 生产环境必须使用 HTTPS
- 保护敏感数据传输

#### 9.2 API 文档
- 使用 Swagger/OpenAPI
- 保持文档与代码同步

#### 9.3 版本兼容
- 向后兼容
- 废弃功能提前通知

#### 9.4 性能优化
- 使用缓存
- 分页查询
- 字段过滤

#### 9.5 安全性
- 参数校验
- SQL注入防护
- XSS防护
- CSRF防护

### 10. 示例

#### 10.1 完整的API示例
```python
@orders_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    """获取订单列表（分页）"""
    try:
        query_params = {
            'page': request.args.get('page', 1, type=int),
            'pageSize': request.args.get('pageSize', 20, type=int),
            'status': request.args.get('status', type=int),
            'projectId': request.args.get('projectId', type=int)
        }
        validated = OrderQuery(**query_params)
        
        result = orders_service.get_orders(
            page=validated.page,
            page_size=validated.pageSize,
            status=validated.status,
            project_id=validated.projectId
        )
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
```

