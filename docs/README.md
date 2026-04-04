# 后端文档索引

## 优先阅读

- [项目总览](../README.md)
- [生产部署说明](./deployment/PRODUCTION_DEPLOYMENT.md)
- [开发规范](./development/DEVELOPMENT.md)

## 架构与集成

- [API 设计](./architecture/API_DESIGN.md)
- [配置系统设计](./architecture/CONFIG_SYSTEM_DESIGN.md)
- [提交协议](./architecture/SUBMISSION_PROTOCOL.md)
- [外部数据接入说明](./architecture/EXTERNAL_DATA_INTEGRATION.md)

## API 文档

- [API 参考](./api/API_REFERENCE.md)
- [平台 API 文档](./api/PLATFORM_API.md)

## 部署

- [生产部署说明](./deployment/PRODUCTION_DEPLOYMENT.md)
- [SSO 接入说明](./SSO.md)

## 当前默认口径

当前文档统一以代码现状为准：

- Python 3.12
- Gunicorn `gthread`
- Docker 本地镜像部署
- K3s `hostPath + NodePort`
- 外部 MySQL 5.6 只读聚合
