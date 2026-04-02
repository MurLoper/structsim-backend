# StructSim AI Platform Backend

`structsim-backend` 是平台后端 API 服务，负责：

- 认证与 SSO
- 配置中心
- 申请单提交与查询
- 结果查询
- RBAC 权限
- 平台公告、隐私协议、埋点与统计

## 环境要求

- Python 3.12 推荐
- MySQL 8.0+
- Redis 可选

## 快速开始

```bash
cd structsim-backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python run.py --init-db
python run.py
```

默认接口地址：

- `http://127.0.0.1:6060`
- 健康检查：`/health`
- API 前缀：`/api/v1`

## 生产启动

生产环境统一使用 Gunicorn：

```bash
python run.py --init-db && gunicorn -c gunicorn_conf.py wsgi:app
```

默认使用：

- `2` workers
- `8` threads

可通过环境变量调整：

- `GUNICORN_WORKERS`
- `GUNICORN_THREADS`
- `GUNICORN_TIMEOUT`

## Docker 与 K3s 部署

完整教程见：

- [`docs/deployment/PRODUCTION_DEPLOYMENT.md`](./docs/deployment/PRODUCTION_DEPLOYMENT.md)

关键文件：

- [`Dockerfile`](./Dockerfile)
- [`gunicorn_conf.py`](./gunicorn_conf.py)
- [`wsgi.py`](./wsgi.py)
- [`deploy/k3s/structsim-backend.yaml`](./deploy/k3s/structsim-backend.yaml)

当前 K3s 默认口径：

- `4` 副本
- `NodePort: 30060`
- 其他内网服务器通过 `http://<主节点IP>:30060` 访问

## 平台功能接口

本轮新增平台能力：

- `GET /api/v1/platform/bootstrap`
- `GET /api/v1/platform/privacy-policy`
- `POST /api/v1/platform/privacy-policy/accept`
- `POST /api/v1/platform/events`
- `GET /api/v1/platform/analytics/summary`
- `GET /api/v1/platform/admin/content`
- `PUT /api/v1/platform/admin/content`
- `POST /api/v1/platform/admin/announcements`
- `PUT /api/v1/platform/admin/announcements/:id`
- `DELETE /api/v1/platform/admin/announcements/:id`

权限要求：
- 埋点分析汇总：`VIEW_DASHBOARD`
- 平台内容与公告管理：`MANAGE_CONFIG`

对应表结构：

- `platform_settings`
- `announcements`
- `privacy_policy_acceptances`
- `tracking_events`

启动时会自动执行平台表结构升级，开关为：

```bash
AUTO_PLATFORM_FEATURES_UPGRADE=true
```

## 文档入口

- [`docs/README.md`](./docs/README.md)
- [`docs/development/DEVELOPMENT.md`](./docs/development/DEVELOPMENT.md)
- [`docs/deployment/PRODUCTION_DEPLOYMENT.md`](./docs/deployment/PRODUCTION_DEPLOYMENT.md)

## 测试与校验

```bash
pytest
python -m compileall app
```
