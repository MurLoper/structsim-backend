# 代码审查清单

> 代码审查必备文档 - 确保代码质量的最后一道防线

## 1. 架构与设计

### 1.1 分层架构
- [ ] Routes层只做路由定义和参数校验
- [ ] Service层只做业务逻辑编排
- [ ] Repository层只做数据访问
- [ ] Schemas层使用Pydantic定义数据结构

### 1.2 职责分离
- [ ] 没有跨层调用（如Routes直接调用Repository）
- [ ] 没有循环依赖
- [ ] 单一职责原则

## 2. 代码规范

### 2.1 行数限制
- [ ] 模块文件 ≤ 300行
- [ ] 单函数 ≤ 60行
- [ ] Route函数 ≤ 30行

### 2.2 命名规范
- [ ] 变量名清晰表意
- [ ] 函数名动词开头
- [ ] 类名名词，PascalCase
- [ ] 常量全大写

### 2.3 代码风格
- [ ] 使用black格式化
- [ ] 使用isort排序import
- [ ] 通过ruff静态检查

## 3. 数据校验

### 3.1 输入校验
- [ ] 所有API输入使用Pydantic校验
- [ ] 必填字段使用Field(..., description="...")
- [ ] 数值范围使用gt, lt等约束

### 3.2 输出校验
- [ ] 统一使用success()和error()返回
- [ ] 包含trace_id
- [ ] 错误码规范使用

## 4. 异常处理

### 4.1 异常捕获
- [ ] 使用BusinessError和NotFoundError
- [ ] 不使用裸except
- [ ] 记录异常日志

### 4.2 错误响应
- [ ] 返回合适的HTTP状态码
- [ ] 错误信息清晰
- [ ] 不暴露敏感信息

## 5. 数据库操作

### 5.1 查询优化
- [ ] 避免N+1查询
- [ ] 使用分页
- [ ] 添加索引

### 5.2 事务管理
- [ ] 在Service层管理事务
- [ ] 正确处理事务回滚

## 6. 安全性

### 6.1 认证授权
- [ ] 敏感接口使用@jwt_required()
- [ ] 权限检查在后端强制执行
- [ ] Token过期处理

### 6.2 数据安全
- [ ] SQL注入防护（使用ORM）
- [ ] XSS防护
- [ ] 敏感数据加密

## 7. 性能

### 7.1 缓存
- [ ] 配置数据使用缓存
- [ ] 缓存失效策略

### 7.2 查询优化
- [ ] 避免全表扫描
- [ ] 使用合适的索引
- [ ] 分页查询

## 8. 日志

### 8.1 日志级别
- [ ] INFO: 关键业务节点
- [ ] WARNING: 可恢复异常
- [ ] ERROR: 异常堆栈

### 8.2 日志内容
- [ ] 包含trace_id
- [ ] 不记录敏感信息
- [ ] 日志清晰易读

## 9. 测试

### 9.1 单元测试
- [ ] 核心业务逻辑有测试
- [ ] 测试覆盖率 > 80%
- [ ] 测试用例清晰

### 9.2 集成测试
- [ ] API接口测试
- [ ] 数据库操作测试

## 10. 文档

### 10.1 代码注释
- [ ] 复杂逻辑有注释
- [ ] 函数有docstring
- [ ] 注释与代码同步

### 10.2 API文档
- [ ] 接口说明清晰
- [ ] 参数说明完整
- [ ] 示例代码正确

## 审查通过标准

- ✅ 所有检查项通过
- ✅ 代码风格统一
- ✅ 无明显性能问题
- ✅ 无安全隐患
- ✅ 测试通过

## 常见问题

### 问题1：Routes层包含业务逻辑
❌ 错误示例：
```python
@bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    # 直接在Routes层处理业务逻辑
    if not data.get('projectId'):
        return error(...)
    order = Order(**data)
    db.session.add(order)
    db.session.commit()
    return success(order.to_dict())
```

✅ 正确示例：
```python
@bp.route('/orders', methods=['POST'])
def create_order():
    try:
        validated = OrderCreate(**request.get_json())
        user_id = get_jwt_identity()
        result = orders_service.create_order(validated.model_dump(), user_id)
        return success(result, "创建成功")
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
```

### 问题2：缺少异常处理
❌ 错误示例：
```python
def get_order(order_id: int):
    order = Order.query.get(order_id)
    return order.to_dict()  # order可能为None
```

✅ 正确示例：
```python
def get_order(order_id: int):
    order = self.repository.get_order_by_id(order_id)
    if not order:
        raise NotFoundError("订单不存在")
    return order.to_dict()
```

### 问题3：缺少数据校验
❌ 错误示例：
```python
@bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    # 直接使用未校验的数据
    result = orders_service.create_order(data)
    return success(result)
```

✅ 正确示例：
```python
@bp.route('/orders', methods=['POST'])
def create_order():
    try:
        validated = OrderCreate(**request.get_json())
        result = orders_service.create_order(validated.model_dump())
        return success(result)
    except ValidationError as e:
        return error(ErrorCode.VALIDATION_ERROR, str(e), http_status=400)
```

