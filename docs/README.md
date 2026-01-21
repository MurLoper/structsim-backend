# 后端文档目录

> **版本**: v2.0
> **最后更新**: 2025-01-18
> **状态**: ✅ 生产就绪

本目录包含后端项目的所有文档。

---

## 📁 目录结构

```
docs/
├── README.md                     # 本文件
├── architecture/                 # 架构设计文档
│   ├── API_DESIGN.md             # API设计规范
│   ├── CONFIG_SYSTEM_DESIGN.md   # 配置系统设计
│   ├── DATABASE.md               # 数据库设计文档 ✨ 新增
│   └── REFACTORING_SUMMARY.md    # 重构总结
├── api/                          # API文档
│   ├── README.md                 # API文档索引
│   └── API_REFERENCE.md          # API参考文档 ✨ 新增
└── development/                  # 开发规范（必读）
    ├── DEVELOPMENT.md            # 后端开发规范
    └── CODE_REVIEW.md            # 代码审查清单
```

---

## 📖 文档分类

### 🏗️ 架构设计（必读）

| 文档 | 描述 | 状态 |
|------|------|------|
| [API设计规范](./architecture/API_DESIGN.md) | RESTful API设计规范 | ✅ 已更新 |
| [配置系统设计](./architecture/CONFIG_SYSTEM_DESIGN.md) | 配置管理系统架构 | ✅ 已更新 |
| [数据库设计文档](./architecture/DATABASE.md) | 完整的数据库表结构设计 | ✨ 新增 |
| [重构总结](./architecture/REFACTORING_SUMMARY.md) | 模块重构记录 | ✅ 已更新 |

### 📝 API文档

| 文档 | 描述 | 状态 |
|------|------|------|
| [API参考文档](./api/API_REFERENCE.md) | 完整的API接口文档 | ✨ 新增 |

### 💻 开发规范（必读）

| 文档 | 描述 | 状态 |
|------|------|------|
| [后端开发规范](./development/DEVELOPMENT.md) | Python + Flask 开发规范 | ✅ 已更新 |
| [代码审查清单](./development/CODE_REVIEW.md) | 代码审查标准 | ✅ 已更新 |

---

## 🚀 快速开始

### 新加入项目的开发者请按以下顺序阅读：

#### 第一步：了解架构
1. ✅ **必读**: [API设计规范](./architecture/API_DESIGN.md)
2. ✅ **数据库**: [数据库设计文档](./architecture/DATABASE.md)
3. ✅ **配置系统**: [配置系统设计](./architecture/CONFIG_SYSTEM_DESIGN.md)

#### 第二步：学习规范
1. ✅ **必读**: [后端开发规范](./development/DEVELOPMENT.md)
2. ✅ **代码审查**: [代码审查清单](./development/CODE_REVIEW.md)

#### 第三步：API文档
1. ✅ **API参考**: [API参考文档](./api/API_REFERENCE.md)

---

## 🎯 核心技术栈

### 框架与工具
- **Flask 3.0** - Web 框架
- **Python 3.14** - 编程语言
- **SQLAlchemy 2.0** - ORM
- **MySQL 8.0+** - 数据库

### 核心库
- **Pydantic 2.x** - 数据验证
- **Flask-CORS** - 跨域支持
- **PyJWT** - JWT 认证

### 开发工具
- **pytest** - 单元测试
- **black** - 代码格式化
- **flake8** - 代码检查

---

## 📦 项目特性

### ✅ 已实现功能

#### 核心功能
- ✅ RESTful API 设计
- ✅ JWT 认证和授权
- ✅ RBAC 权限管理
- ✅ 统一响应格式
- ✅ 错误处理和日志

#### 配置管理
- ✅ 项目管理
- ✅ 仿真类型管理
- ✅ 参数定义管理
- ✅ 参数组管理
- ✅ 求解器管理
- ✅ 工况定义管理
- ✅ 输出定义管理
- ✅ 姿态类型管理
- ✅ 参数模板集管理
- ✅ 工况输出集管理

#### 数据库设计
- ✅ 完整的表结构设计
- ✅ 索引优化
- ✅ 外键约束
- ✅ 软删除支持

### 🚧 开发中功能

- 🚧 订单管理完善
- 🚧 结果数据管理
- 🚧 文件上传和管理
- 🚧 异步任务处理
- 🚧 数据库迁移工具（Alembic）

---

## 📊 API 概览

### 认证 API
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息

### 配置管理 API
- `GET /api/v1/config/projects` - 获取项目列表
- `POST /api/v1/config/projects` - 创建项目
- `PUT /api/v1/config/projects/:id` - 更新项目
- `DELETE /api/v1/config/projects/:id` - 删除项目

### 权限管理 API
- `GET /api/v1/rbac/roles` - 获取角色列表
- `GET /api/v1/rbac/permissions` - 获取权限列表

详细信息请查看 [API参考文档](./api/API_REFERENCE.md)

---

## 🗄️ 数据库设计

### 核心表
- `projects` - 项目表
- `sim_types` - 仿真类型表
- `param_defs` - 参数定义表
- `solvers` - 求解器表
- `condition_defs` - 工况定义表
- `output_defs` - 输出定义表
- `fold_types` - 姿态类型表

### 关系表
- `param_tpl_sets` - 参数模板集表
- `param_tpl_set_rels` - 参数模板集关联表
- `cond_out_sets` - 工况输出集表
- `cond_out_set_rels` - 工况输出集关联表
- `param_groups` - 参数组表
- `param_group_param_rels` - 参数组关联表

详细信息请查看 [数据库设计文档](./architecture/DATABASE.md)

---

## 🔧 开发规范

### 代码规范
- ✅ PEP 8 代码风格
- ✅ 类型注解
- ✅ 文档字符串
- ✅ 单元测试

### API 规范
- ✅ RESTful 设计
- ✅ 统一响应格式
- ✅ 错误码规范
- ✅ 版本控制

### 数据库规范
- ✅ 命名规范（小写下划线）
- ✅ 索引设计
- ✅ 外键约束
- ✅ 软删除

---

## 🔗 相关链接

### 项目文档
- [项目总览](../../README.md)
- [前端文档](../../../structsim-ai-platform/docs/README.md)

### 外部资源
- [Flask 文档](https://flask.palletsprojects.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [MySQL 文档](https://dev.mysql.com/doc/)

---

## 📞 联系方式

如有问题或建议，请联系：
- **后端团队负责人**: [待补充]
- **技术支持**: [待补充]

---

**最后更新**: 2025-01-18
**文档版本**: v2.0
**维护者**: 后端团队