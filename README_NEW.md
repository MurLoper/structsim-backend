# StructSim AI Platform - 后端 API

基于 Flask 的 RESTful API 服务。

## 📚 文档

详细文档请查看 [docs/](./docs/) 目录：
- **开发规范（必读）**: [DEVELOPMENT.md](./docs/development/DEVELOPMENT.md)
- **代码审查清单**: [CODE_REVIEW.md](./docs/development/CODE_REVIEW.md)
- **API设计规范**: [API_DESIGN.md](./docs/architecture/API_DESIGN.md)
- **重构总结**: [REFACTORING_SUMMARY.md](./docs/architecture/REFACTORING_SUMMARY.md)

## 🚀 快速开始

### 环境要求
- Python 3.11+
- MySQL 8.0+ (可选，开发环境使用 SQLite)

### 安装步骤

1. 创建虚拟环境：
```bash
cd structsim-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库等信息
```

4. 初始化数据库：
```bash
python run.py --init-db
python run.py --seed
```

5. 启动开发服务器：
```bash
python run.py
# 或指定参数：
python run.py --host 127.0.0.1 --port 5000
```

## 📁 项目结构

```
structsim-backend/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── extensions.py        # 扩展初始化
│   ├── api/
│   │   ├── __init__.py      # API 蓝图
│   │   └── v1/              # API v1
│   │       ├── auth/        # 认证模块
│   │       ├── orders/      # 订单模块
│   │       └── config/      # 配置模块
│   ├── common/              # 通用工具
│   │   ├── response.py      # 统一响应
│   │   ├── errors.py        # 异常定义
│   │   └── pagination.py    # 分页工具
│   ├── constants/           # 常量定义
│   │   ├── error_codes.py   # 错误码
│   │   └── enums.py         # 枚举
│   └── models/              # 数据模型
├── docs/                    # 文档目录
│   ├── development/         # 开发规范
│   └── architecture/        # 架构设计
├── config.py                # 配置文件
├── requirements.txt         # Python 依赖
├── run.py                   # 应用入口
└── seed.py                  # 数据库种子
```

## 🛠️ 技术栈

- **Web框架**: Flask 3.x
- **ORM**: SQLAlchemy 2.x
- **数据校验**: Pydantic 2.x
- **认证**: Flask-JWT-Extended
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis (可选)

## 📝 开发规范

### 四层架构
- **Routes层**: 路由定义 + 参数校验
- **Service层**: 业务逻辑 + 事务管理
- **Repository层**: 数据访问
- **Schemas层**: 数据校验 (Pydantic)

### 代码规范
- 遵循 [DEVELOPMENT.md](./docs/development/DEVELOPMENT.md)
- 模块文件 ≤ 300 行
- 单函数 ≤ 60 行
- Route函数 ≤ 30 行

## 🔌 API 端点

### 认证模块 (`/api/v1/auth`)
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户
- `GET /users` - 获取用户列表
- `POST /logout` - 用户登出

### 订单模块 (`/api/v1/orders`)
- `GET /orders` - 获取订单列表（分页）
- `GET /orders/:id` - 获取订单详情
- `POST /orders` - 创建订单
- `PUT /orders/:id` - 更新订单
- `DELETE /orders/:id` - 删除订单
- `GET /orders/:id/result` - 获取订单结果

### 配置模块 (`/api/v1/config`)
- `GET/POST/PUT/DELETE /sim-types` - 仿真类型管理
- `GET/POST/PUT/DELETE /param-defs` - 参数定义管理
- `GET/POST/PUT/DELETE /solvers` - 求解器管理
- `GET/POST/PUT/DELETE /condition-defs` - 工况定义管理
- `GET/POST/PUT/DELETE /output-defs` - 输出定义管理
- `GET/POST/PUT/DELETE /fold-types` - 姿态类型管理

## 📊 统一响应格式

### 成功响应
```json
{
  "code": 0,
  "msg": "ok",
  "data": {},
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

## 🔧 环境变量

```bash
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=sqlite:///structsim.db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

## 🧪 测试

```bash
# 运行测试（待添加）
pytest

# 代码检查
ruff check .

# 格式化代码
black .
isort .
```

## 🔗 相关链接

- [前端项目](../structsim-ai-platform/)
- [项目文档](../README.md)
- [开发规范](./docs/development/DEVELOPMENT.md)
- [API设计规范](./docs/architecture/API_DESIGN.md)

## 📄 许可证

内部项目，保留所有权利。

