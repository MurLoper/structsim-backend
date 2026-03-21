# StructSim AI Platform - 后端 API

基于 Flask 的 RESTful API 服务，负责认证鉴权、配置中心、订单管理、结果查询、RBAC 和文件上传。

## 📚 文档

详细文档请查看 [docs/](./docs/) 目录：
- **开发规范（必读）**: [DEVELOPMENT.md](./docs/development/DEVELOPMENT.md)
- **代码审查清单**: [CODE_REVIEW.md](./docs/development/CODE_REVIEW.md)
- **API设计规范**: [API_DESIGN.md](./docs/architecture/API_DESIGN.md)
- **提单协议**: [SUBMISSION_PROTOCOL.md](./docs/architecture/SUBMISSION_PROTOCOL.md)
- **后端现状与计划**: [CURRENT_STATUS_AND_PLAN.md](./docs/architecture/CURRENT_STATUS_AND_PLAN.md)
- **登录与SSO**: [SSO.md](./docs/SSO.md)

## 🚀 快速开始

### 环境要求
- Python 3.11+
- MySQL 8.0+（可选）
- Redis（可选）

说明：

- 默认开发模式可直接使用 SQLite
- 如需查询历史结果，可额外配置 `LEGACY_MYSQL_URL`

### 安装步骤

1. 创建虚拟环境：
```bash
cd structsim-backend
python -m venv venv
venv\Scripts\activate     # Windows PowerShell
# source venv/bin/activate  # macOS / Linux
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
copy .env.example .env
# Windows 下可使用记事本或编辑器修改 .env
```

如果你使用 macOS / Linux，可改为：

```bash
cp .env.example .env
```

4. 初始化数据库：
```bash
# 创建表结构
python run.py --init-db

# 如需修复上传分片表（历史库）
python database/import_mysql.py --sql-file "database/migrations/add_upload_chunks_table.sql"
```

**详细的数据库导出/覆盖同步说明请参考：[database/README.md](./database/README.md)**

5. 启动开发服务器：
```bash
python run.py
# 或指定参数：
python run.py --host 127.0.0.1 --port 6060
```

默认监听端口是 `6060`，与前端 Vite 代理配置保持一致。

## 📁 项目结构

```
structsim-backend/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── extensions.py        # 扩展初始化
│   ├── api/
│   │   ├── __init__.py      # 兼容旧接口蓝图
│   │   └── v1/              # API v1
│   │       ├── auth/        # 认证模块
│   │       ├── config/      # 配置中心
│   │       ├── orders/      # 订单模块
│   │       ├── rbac/        # 用户/角色/权限
│   │       ├── results/     # 结果查询与状态更新
│   │       ├── sso.py       # SSO 相关接口
│   │       └── upload/      # 文件上传
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
├── database/                # 数据导入导出、迁移与初始化数据
├── migrations/              # Flask-Migrate 迁移
└── run.py                   # 应用入口
```

## 🛠️ 技术栈

- **Web框架**: Flask 3.x
- **ORM**: SQLAlchemy 2.x
- **数据校验**: Pydantic 2.x
- **认证**: Flask-JWT-Extended
- **数据库**: SQLite（开发）/ MySQL（生产）
- **缓存**: Redis (可选)
- **文档**: Flasgger / OpenAPI

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
- `GET /verify` - 校验 token 并返回用户与菜单
- `POST /refresh` - 刷新访问令牌
- `GET /heartbeat` - 登录状态心跳检查

### 订单模块 (`/api/v1/orders`)
- `GET /orders` - 获取订单列表（分页）
- `GET /orders/:id` - 获取订单详情
- `POST /orders` - 创建订单
- `PUT /orders/:id` - 更新订单
- `DELETE /orders/:id` - 删除订单
- `GET /statistics` - 获取订单统计
- `GET /trends` - 获取趋势数据
- `GET /status-distribution` - 获取状态分布
- `POST /verify-file` - 校验源文件
- `POST /parse-param-excel` - 解析参数 Excel
- `POST /merge-params` - 合并参数
- `POST /validate-params` - 校验参数

说明：

- `GET /orders/:id/result` 在当前代码中仍为空实现，不应作为主要结果查询接口使用
- 结果查询请优先使用 `/api/v1/results/*`

### 配置模块 (`/api/v1/config`)
- `GET/POST/PUT/DELETE /sim-types` - 仿真类型管理
- `GET/POST/PUT/DELETE /projects` - 项目管理
- `GET/POST/PUT/DELETE /param-defs` - 参数定义管理
- `GET/POST/PUT/DELETE /solvers` - 求解器管理
- `GET/POST/PUT/DELETE /condition-defs` - 工况定义管理
- `GET/POST/PUT/DELETE /output-defs` - 输出定义管理
- `GET/POST/PUT/DELETE /fold-types` - 姿态类型管理
- `GET /base-data` - 聚合基础配置数据
- `GET/PUT /status-defs` - 状态定义
- `GET /working-conditions` - 工况配置

### 结果模块 (`/api/v1/results`)
- `GET /order/:order_id/sim-types` - 获取订单下各仿真类型结果
- `GET /sim-type/:result_id` - 获取单个仿真类型结果详情
- `GET /sim-type/:result_id/rounds` - 获取轮次分页数据
- `PATCH /sim-type/:result_id/status` - 更新仿真类型结果状态
- `PATCH /round/:round_id/status` - 更新轮次状态

### RBAC 模块 (`/api/v1/rbac`)
- `GET/POST/PUT/DELETE /users` - 用户管理
- `GET/POST/PUT/DELETE /roles` - 角色管理
- `GET/POST/PUT/DELETE /permissions` - 权限管理

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
LEGACY_MYSQL_URL=mysql+pymysql://user:password@host:3306/legacy_db?charset=utf8mb4
UPLOAD_FOLDER=./storage
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

## 🧪 测试

```bash
# 运行测试
pytest

# 覆盖率
pytest --cov=app --cov-report=term-missing
```

## 🔗 相关链接

- [前端项目](../structsim-ai-platform/)
- [开发规范](./docs/development/DEVELOPMENT.md)
- [API设计规范](./docs/architecture/API_DESIGN.md)

## 📄 许可证

内部项目，保留所有权利。
