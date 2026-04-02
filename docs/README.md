# 后端文档索引

## 首先阅读

- [`../README.md`](../README.md)
- [`deployment/PRODUCTION_DEPLOYMENT.md`](./deployment/PRODUCTION_DEPLOYMENT.md)
- [`development/DEVELOPMENT.md`](./development/DEVELOPMENT.md)

## 开发规范

- [`development/DEVELOPMENT.md`](./development/DEVELOPMENT.md)
- [`development/CODE_REVIEW.md`](./development/CODE_REVIEW.md)

## 架构与接口

- [`architecture/API_DESIGN.md`](./architecture/API_DESIGN.md)
- [`architecture/CONFIG_SYSTEM_DESIGN.md`](./architecture/CONFIG_SYSTEM_DESIGN.md)
- [`architecture/SUBMISSION_PROTOCOL.md`](./architecture/SUBMISSION_PROTOCOL.md)
- [`api/API_REFERENCE.md`](./api/API_REFERENCE.md)
- [`api/PLATFORM_API.md`](./api/PLATFORM_API.md)

## 部署

- [`deployment/PRODUCTION_DEPLOYMENT.md`](./deployment/PRODUCTION_DEPLOYMENT.md)

## 当前口径

当前文档以“代码现状”为准。  
后端生产部署默认使用：

- Python 3.12
- Gunicorn `gthread`
- Docker 本地镜像
- K3s `hostPath` 挂载
