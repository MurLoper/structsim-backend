# 后端文档目录

面向 `structsim-backend` 当前代码实现的后端文档索引。
**最后更新**: 2026-03-21

## 1. 首先阅读

如果当前目标是收口上线主链路，建议按以下顺序阅读：

1. [后端现状与开发计划](./architecture/CURRENT_STATUS_AND_PLAN.md)
2. [登录与 SSO 说明](./SSO.md)
3. [提单初始化与订单快照协议](./architecture/SUBMISSION_PROTOCOL.md)
4. [提单主链路字段清单与联调清单](./architecture/SUBMISSION_FIELD_CHECKLIST.md)
5. [配置驱动提单系统设计](./architecture/CONFIG_SYSTEM_DESIGN.md)

## 2. 架构文档

| 文档 | 用途 |
| --- | --- |
| [CURRENT_STATUS_AND_PLAN.md](./architecture/CURRENT_STATUS_AND_PLAN.md) | 当前现状、P0 问题与阶段计划 |
| [SSO.md](./SSO.md) | 登录模式、SSO 现状与收口方案 |
| [SUBMISSION_PROTOCOL.md](./architecture/SUBMISSION_PROTOCOL.md) | 提单协议、快照边界与兼容字段 |
| [SUBMISSION_FIELD_CHECKLIST.md](./architecture/SUBMISSION_FIELD_CHECKLIST.md) | 字段清单、恢复逻辑与联调检查项 |
| [CONFIG_SYSTEM_DESIGN.md](./architecture/CONFIG_SYSTEM_DESIGN.md) | 配置驱动提单的目标结构与收口方向 |
| [API_DESIGN.md](./architecture/API_DESIGN.md) | 通用 API 设计规范 |
| [DATABASE.md](./architecture/DATABASE.md) | 数据库结构说明 |

## 3. 研发规范

| 文档 | 用途 |
| --- | --- |
| [DEVELOPMENT.md](./development/DEVELOPMENT.md) | Flask / Python 开发规范 |
| [CODE_REVIEW.md](./development/CODE_REVIEW.md) | 代码审查清单 |
| [API_REFERENCE.md](./api/API_REFERENCE.md) | 接口参考 |

## 4. 当前主判断

当前后端最需要收口的不是框架迁移，而是业务边界：

- 统一登录 / SSO 用户模型
- 明确提单主快照以 `input_json` 为准
- 明确 `opt_param` 只是兼容字段
- 明确 `condition_summary` 只是列表摘要
- 统一编辑页、详情页、结果页的快照消费方式

## 5. 与前端对应关系

对应前端主文档：

- [前端文档目录](../../structsim-ai-platform/docs/README.md)
- [前端现状与开发计划](../../structsim-ai-platform/docs/architecture/CURRENT_STATUS_AND_PLAN.md)

