# 后端生产部署指南

适用范围：`structsim-backend`

目标：
- 提供 Python 3.12 的本地 Docker 镜像部署方式
- 提供 K3s 内网部署方式
- 默认使用多线程 Gunicorn 以支撑一定并发
- 保持部署方式简洁，优先 `-v`、`-p` 和 `hostPath`

## 1. 生产服务模式

生产环境统一使用：

- `gunicorn`
- `gthread` worker
- `wsgi:app`

默认并发参数：

- `GUNICORN_WORKERS=2`
- `GUNICORN_THREADS=8`

等价于单实例约 `16` 个并发处理线程。  
如果内网机器 CPU 更高，可以按需调整。

启动命令：

```bash
python run.py --init-db && gunicorn -c gunicorn_conf.py wsgi:app
```

说明：
- `python run.py --init-db` 用于初始化表并触发自动升级脚本
- `gunicorn_conf.py` 统一读取环境变量，避免在文档里堆太长命令

## 2. 本地 Docker 发布模式

### 2.1 构建 Python 3.12 镜像

```bash
cd structsim-backend
docker build -t structsim-backend:py312 .
```

### 2.2 准备生产环境变量

建议复制一份：

```bash
cp .env.example .env.production
```

Windows PowerShell 可用：

```powershell
Copy-Item .env.example .env.production
```

至少修改这些值：

- `FLASK_ENV=production`
- `DATABASE_URL`
- `LEGACY_MYSQL_URL`
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `UPLOAD_FOLDER=/mnt/external/upload`

### 2.3 运行容器

```bash
docker run -d \
  --name structsim-backend \
  --restart unless-stopped \
  -p 6060:6060 \
  -v /data/structsim/upload:/mnt/external/upload \
  -v /data/structsim/shared:/mnt/external/shared \
  -v /data/structsim/logs:/mnt/external/logs \
  --env-file .env.production \
  structsim-backend:py312
```

说明：
- `-p 6060:6060`：对外暴露接口端口
- `-v /data/structsim/upload:/mnt/external/upload`：申请单、上传文件、落盘内容
- `-v /data/structsim/shared:/mnt/external/shared`：预留给外部自动化或共享目录
- `-v /data/structsim/logs:/mnt/external/logs`：预留日志目录

### 2.4 验证服务

```bash
curl http://127.0.0.1:6060/health
```

返回包含 `status=healthy` 即表示服务正常。

### 2.5 更新镜像

```bash
docker stop structsim-backend
docker rm structsim-backend
docker build -t structsim-backend:py312 .
docker run -d --name structsim-backend --restart unless-stopped -p 6060:6060 \
  -v /data/structsim/upload:/mnt/external/upload \
  -v /data/structsim/shared:/mnt/external/shared \
  -v /data/structsim/logs:/mnt/external/logs \
  --env-file .env.production \
  structsim-backend:py312
```

## 3. K3s 内网部署

K3s 方案使用：

- 单 Deployment
- 单 NodePort Service
- 多个 `hostPath` 挂载外部路径
- 本地导入镜像，不依赖公网镜像仓库
- `4` 个副本做 Pod 级流量分发

清单位于：

- [`deploy/k3s/structsim-backend.yaml`](../../deploy/k3s/structsim-backend.yaml)

### 3.1 导出本地镜像

```bash
docker save structsim-backend:py312 -o structsim-backend-py312.tar
```

### 3.2 导入 K3s 节点

在 K3s 节点执行：

```bash
sudo k3s ctr images import structsim-backend-py312.tar
```

### 3.3 调整清单中的关键项

需要先改这些配置：

- `DATABASE_URL`
- `LEGACY_MYSQL_URL`
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `hostPath.path`

清单默认已固定：

- `replicas: 4`
- `type: NodePort`
- `nodePort: 30060`

默认挂载如下：

- `/data/structsim/upload -> /mnt/external/upload`
- `/data/structsim/shared -> /mnt/external/shared`
- `/data/structsim/logs -> /mnt/external/logs`

如果内网路径不同，只改 `hostPath.path` 即可。

重要前提：

- 所有可能调度到 Pod 的节点，都必须预先存在相同目录：
  - `/data/structsim/upload`
  - `/data/structsim/shared`
  - `/data/structsim/logs`
- 如果任一节点目录缺失，不允许直接扩到 `4` 副本
- 这份清单依赖 K3s `Service` 在 `4` 个 `Ready` Pod 之间做流量分发，不做网关层策略路由

### 3.4 应用部署

```bash
kubectl apply -f deploy/k3s/structsim-backend.yaml
```

### 3.5 查看运行状态

```bash
kubectl -n structsim get pods -o wide
kubectl -n structsim get svc
kubectl -n structsim logs deploy/structsim-backend
```

### 3.6 内网访问

当前清单使用 `NodePort`，其他内网服务器可直接访问：

```bash
curl http://<主节点IP>:30060/health
```

说明：

- 外部请求先到 `主节点IP:30060`
- 再经由 Kubernetes `NodePort + Service` 转发到 `4` 个 `Ready` Pod
- 这是 Pod 级别的自动负载分发，不是应用层网关智能路由

如需在主节点本机快速验证，也可执行：

```bash
curl http://127.0.0.1:30060/health
```

## 4. 并发建议

默认单实例配置：

- `2` workers
- `8` threads

配合当前 K3s `4` 副本部署，整体可提供更高的内网并发承载。建议：

- 4 核机器：保持 `2 x 8`
- 8 核机器：可尝试 `4 x 8`
- 如果接口等待 MySQL/外部 IO 较多，优先加 `threads`

不建议一开始就把 `workers` 开太大，否则会放大数据库连接占用。
如果 MySQL 连接压力过大，优先缩容副本数或调低 `GUNICORN_WORKERS/GUNICORN_THREADS`，不要盲目继续扩副本。

## 5. 平台功能相关说明

本次部署已包含：

- 公告配置接口
- 公告轮询接口
- 隐私协议接口
- 埋点事件写入接口
- 埋点分析汇总接口

平台功能入口固定为：

- 公告查看：前端布局顶部公告横幅
- 公告配置：系统配置 -> 平台内容
- 埋点分析查看：`/analytics`
- 隐私协议查看：头像菜单 -> 查看隐私协议

权限边界固定为：

- 埋点分析：`VIEW_DASHBOARD`
- 平台内容与公告管理：`MANAGE_CONFIG`
- 隐私协议查看：所有已登录用户可访问

埋点工作方式：

- 前端本地队列批量上报事件
- 路由切换自动采集 `page_view`
- 公告曝光与关闭分别记录
- 隐私协议查看与同意分别记录
- 后端只负责写入与汇总分析

这是平台内网自有埋点体系，不接入第三方 SaaS，也不依赖外网统计平台。

后端启动时会自动检查并升级这些表：

- `platform_settings`
- `announcements`
- `privacy_policy_acceptances`
- `tracking_events`

升级开关：

```bash
AUTO_PLATFORM_FEATURES_UPGRADE=true
```

## 6. 推荐的内网目录规划

建议统一规划为：

```text
/data/structsim/
  upload/
  shared/
  logs/
```

这样 Docker 和 K3s 可以共用同一套目录语义，后续迁移更省事。
