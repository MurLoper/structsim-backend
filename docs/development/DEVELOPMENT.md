# StructSim Backend 开发规范

> **必读文档** - 所有后端开发者必须遵循的开发规范

## 1. 技术栈与环境

- **Python**: 3.11+
- **Web框架**: Flask 3.x
- **ORM**: SQLAlchemy 2.x
- **数据校验**: Pydantic 2.x
- **认证**: Flask-JWT-Extended
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis (可选)
- **任务队列**: Celery (可选)

## 2. 代码风格

- 格式化: **black**
- import排序: **isort**
- 静态检查: **ruff**
- 类型检查: **mypy**

### 2.1 行数限制

- 模块文件: ≤ 300 行 (警戒 > 500 行)
- 单函数: ≤ 60 行 (警戒 > 100 行)
- Route函数: ≤ 30 行

## 3. 目录结构

```
app/
  __init__.py               # create_app 工厂
  config.py                 # 配置类
  extensions.py             # 扩展初始化
  constants/                # 枚举、常量、错误码
    __init__.py
    error_codes.py
    enums.py
  common/                   # 通用工具
    __init__.py
    response.py             # 统一响应封装
    errors.py               # 异常基类
    pagination.py           # 分页工具
    decorators.py           # 通用装饰器
  api/
    __init__.py
    v1/
      __init__.py
      config/               # 配置中心
        routes.py
        schemas.py
        service.py
        repository.py
      orders/               # 订单管理
        routes.py
        schemas.py
        service.py
        repository.py
      auth/                 # 认证授权
        routes.py
        schemas.py
        service.py
        repository.py
  domain/                   # 领域层(不依赖Flask)
    __init__.py
    rules.py                # 业务规则
  infra/                    # 基础设施层
    db/
      __init__.py
      models/               # ORM模型
      repositories/         # 数据仓储
      session.py
```

## 4. API 设计规范

### 4.1 URL规范

- 版本前缀: `/api/v1/...`
- 资源名词复数: `/orders`, `/projects`
- 分页参数: `page`, `page_size`

### 4.2 统一响应结构

```json
{
  "code": 0,
  "msg": "ok",
  "data": {},
  "trace_id": "abc123"
}
```

### 4.3 错误码规范

| 范围 | 说明 |
|------|------|
| 0 | 成功 |
| 400xxx | 参数错误 |
| 401xxx | 认证错误 |
| 403xxx | 权限错误 |
| 404xxx | 资源不存在 |
| 500xxx | 服务器错误 |

## 5. 分层职责

### 5.1 Routes层

- 只做: 路由定义 + 调用service + 返回response
- 禁止: 复杂业务逻辑、直接SQL操作

### 5.2 Service层

- 业务编排、事务管理
- 调用Repository获取数据
- 调用Domain进行业务校验

### 5.3 Repository层

- 纯数据访问
- CRUD操作封装
- 查询组合

### 5.4 Domain层

- 核心业务规则
- 不依赖Flask
- 可独立单测

## 6. 数据校验

使用Pydantic定义Schema:

```python
from pydantic import BaseModel, Field

class CreateOrderRequest(BaseModel):
    project_id: int = Field(..., gt=0)
    sim_type_ids: list[int] = Field(..., min_length=1)
```

## 7. 异常处理

```python
from app.common.errors import BusinessError, ErrorCode

# 抛出业务异常
raise BusinessError(ErrorCode.PARAM_MISSING, field="project_id")
```

## 8. 日志规范

- 每个请求生成trace_id
- INFO: 请求开始/结束、关键业务节点
- WARNING: 校验失败、可恢复异常
- ERROR: 异常堆栈 + trace_id

## 9. 权限校验

```python
from app.common.decorators import require_permission

@bp.route('/orders', methods=['POST'])
@require_permission('CREATE_ORDER')
def create_order():
    pass
```

## 10. 代码检查清单

- [ ] Route层 ≤ 30行，无SQL，无复杂逻辑
- [ ] 校验统一使用schemas
- [ ] Service只负责编排
- [ ] Repository统一封装
- [ ] 配置中心有缓存
- [ ] 日志有trace_id
- [ ] 权限后端强制校验

