# StructSim AI Platform Backend

`structsim-backend` 是平台后端 API 服务，负责以下能力：

- 认证与 SSO
- 配置中心
- 申请单提交、查询与编辑
- 结果分析与外部优化结果聚合
- RBAC 权限控制
- 平台公告、隐私协议、埋点与分析

## 环境要求

- Python 3.12
- MySQL 8.0+ 作为主业务库
- Redis 可选
- 可选的外部 MySQL 5.6 只读实例，用于项目阶段、输出 component 字典和优化结果聚合

## 快速开始

```bash
cd structsim-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py --init-db
python run.py
```

默认地址：

- `http://127.0.0.1:6060`
- 健康检查：`/health`
- API 前缀：`/api/v1`

## 生产启动

生产环境统一使用 Gunicorn：

```bash
python run.py --init-db && gunicorn -c gunicorn_conf.py wsgi:app
```

默认并发参数：

- `GUNICORN_WORKERS=2`
- `GUNICORN_THREADS=8`

可通过环境变量调整：

- `GUNICORN_WORKERS`
- `GUNICORN_THREADS`
- `GUNICORN_TIMEOUT`

## Docker 与 K3s 部署

完整部署文档见：

- [生产部署说明](./docs/deployment/PRODUCTION_DEPLOYMENT.md)

关键文件：

- [Dockerfile](./Dockerfile)
- [gunicorn_conf.py](./gunicorn_conf.py)
- [wsgi.py](./wsgi.py)
- [deploy/k3s/structsim-backend.yaml](./deploy/k3s/structsim-backend.yaml)

当前 K3s 默认口径：

- `4` 个副本
- `NodePort: 30060`
- 其他内网服务器通过 `http://<主节点IP>:30060` 访问

## 外部 MySQL 5.6 只读接入

当前已接入一套同实例多 schema 的只读外部库，用于补齐提交页项目阶段、输出后处理 component 字典，以及结果分析中的外部优化链路：

- `simulation_project`
- `struct_module`
- `union_opt_kernal`
- `union_opt_conf`
- `sqrs_hw`

主要用途：

- `simulation_project.phase`：阶段字典
- `simulation_project.pp_phase`：`project_id -> phase_id` 默认映射
- `struct_module.component`：输出后处理 `component` 字典
- `union_opt_kernal.opt_issues`：订单级优化任务
- `union_opt_kernal.jobs`：工况级任务

详细说明见：

- [外部数据接入说明](./docs/architecture/EXTERNAL_DATA_INTEGRATION.md)

## 平台治理能力

本轮平台治理已包含：

- 顶部公告轮询与后台配置
- 隐私协议展示、强制确认与版本管理
- 页面级、功能级、流程级埋点
- `/analytics` 分析页

平台功能入口：

- 公告查看：前端布局顶部公告横幅
- 公告配置：系统配置 -> 平台内容
- 埋点分析：`/analytics`
- 隐私协议：头像菜单 -> 查看隐私协议

权限要求：

- 埋点分析：`VIEW_DASHBOARD`
- 平台内容管理：`MANAGE_CONFIG`

接口说明见：

- [平台 API 文档](./docs/api/PLATFORM_API.md)

## 文档入口

- [文档索引](./docs/README.md)
- [开发规范](./docs/development/DEVELOPMENT.md)
- [生产部署说明](./docs/deployment/PRODUCTION_DEPLOYMENT.md)
- [平台 API 文档](./docs/api/PLATFORM_API.md)
- [外部数据接入说明](./docs/architecture/EXTERNAL_DATA_INTEGRATION.md)

## 测试与校验

```bash
pytest
python -m compileall app
```
