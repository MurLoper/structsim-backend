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
- 单 ClusterIP Service
- 多个 `hostPath` 挂载外部路径
- 本地导入镜像，不依赖公网镜像仓库

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

默认挂载如下：

- `/data/structsim/upload -> /mnt/external/upload`
- `/data/structsim/shared -> /mnt/external/shared`
- `/data/structsim/logs -> /mnt/external/logs`

如果内网路径不同，只改 `hostPath.path` 即可。

### 3.4 应用部署

```bash
kubectl apply -f deploy/k3s/structsim-backend.yaml
```

### 3.5 查看运行状态

```bash
kubectl -n structsim get pods
kubectl -n structsim get svc
kubectl -n structsim logs deploy/structsim-backend
```

### 3.6 内网访问

默认是 `ClusterIP`，适合通过内网网关或 Ingress 访问。  
如果需要临时直连验证，可执行：

```bash
kubectl -n structsim port-forward svc/structsim-backend 6060:6060
```

然后访问：

```bash
curl http://127.0.0.1:6060/health
```

## 4. 并发建议

默认单实例配置：

- `2` workers
- `8` threads

适合中小规模内网接口并发。建议：

- 4 核机器：保持 `2 x 8`
- 8 核机器：可尝试 `4 x 8`
- 如果接口等待 MySQL/外部 IO 较多，优先加 `threads`

不建议一开始就把 `workers` 开太大，否则会放大数据库连接占用。

## 5. 平台功能相关说明

本次部署已包含：

- 公告配置接口
- 公告轮询接口
- 隐私协议接口
- 埋点事件写入接口
- 埋点分析汇总接口

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
