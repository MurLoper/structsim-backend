# 后端生产部署说明

适用范围：`structsim-backend`

目标：

- 提供 Python 3.12 的本地 Docker 发布方式
- 提供 K3s 内网部署方式
- 统一使用 Gunicorn 多线程支撑内网并发
- 支持外部 MySQL 5.6 只读接入

## 1. 生产服务模型

生产环境统一使用：

- `gunicorn`
- `gthread` worker
- `wsgi:app`

默认并发参数：

- `GUNICORN_WORKERS=2`
- `GUNICORN_THREADS=8`

等价于单实例 `16` 个并发处理线程。若机器规格更高，可按需调整。

启动命令：

```bash
python run.py --init-db && gunicorn -c gunicorn_conf.py wsgi:app
```

## 2. Docker 部署

### 2.1 构建镜像

```bash
cd structsim-backend
docker build -t structsim-backend:py312 .
```

### 2.2 准备环境变量

```bash
cp .env.example .env.production
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env.production
```

至少需要修改：

- `FLASK_ENV=production`
- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `AUTH_LOGIN_RSA_PRIVATE_KEY` 或 `AUTH_LOGIN_RSA_PRIVATE_KEY_PATH`
- `EXTERNAL_MYSQL_*`

### 2.3 启动容器

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

- `-p 6060:6060`：对外暴露 API
- `upload`：申请单上传、源文件、业务落盘
- `shared`：预留给外部自动化或共享目录
- `logs`：容器日志与业务日志目录

### 2.4 验证服务

```bash
curl http://127.0.0.1:6060/health
```

## 3. K3s 内网部署

当前清单路径：

- [`deploy/k3s/structsim-backend.yaml`](../../deploy/k3s/structsim-backend.yaml)

### 3.1 固定部署口径

当前默认配置已经固定为：

- `replicas: 4`
- `Service.type: NodePort`
- `nodePort: 30060`

内网访问方式：

```bash
curl http://<主节点IP>:30060/health
```

### 3.2 镜像导出与导入

导出本地镜像：

```bash
docker save structsim-backend:py312 -o structsim-backend-py312.tar
```

导入到 K3s 节点：

```bash
sudo k3s ctr images import structsim-backend-py312.tar
```

### 3.3 hostPath 目录约束

清单默认使用：

- `/data/structsim/upload -> /mnt/external/upload`
- `/data/structsim/shared -> /mnt/external/shared`
- `/data/structsim/logs -> /mnt/external/logs`

重要前提：

- 所有可能被调度到 Pod 的节点，都必须具备这三组宿主机目录
- 目录缺失时，不允许扩到 `4` 副本

### 3.4 应用部署

```bash
kubectl apply -f deploy/k3s/structsim-backend.yaml
```

### 3.5 查看状态

```bash
kubectl -n structsim get pods -o wide
kubectl -n structsim get svc
kubectl -n structsim logs deploy/structsim-backend
```

### 3.6 自动负载分发边界

当前使用 `NodePort + Service`：

- 请求先到 `主节点IP:30060`
- 再由 Kubernetes Service 分发到 `4` 个 `Ready` Pod

这是 **Pod 级流量分发**，不是应用层网关智能路由。

若 MySQL 连接压力过大，优先：

- 缩容副本数
- 调整 `GUNICORN_WORKERS`
- 调整 `GUNICORN_THREADS`

不要盲目继续扩副本。

## 4. 外部 MySQL 5.6 只读接入

当前已接入同一实例下的多 schema：

- `simulation_project`
- `struct_module`
- `union_opt_kernal`
- `union_opt_conf`
- `sqrs_hw`

用途如下：

- `simulation_project.phase`：项目阶段字典
- `simulation_project.pp_phase`：`project_id -> phase_id` 默认映射
- `struct_module.component`：输出后处理 `component` 字典
- `union_opt_kernal.opt_issues`：订单级优化任务
- `union_opt_kernal.jobs`：工况级任务

这套连接仅用于 **只读查询**：

- 不做迁移
- 不建外键
- 不写回外部库

配置项：

- `EXTERNAL_MYSQL_HOST`
- `EXTERNAL_MYSQL_PORT`
- `EXTERNAL_MYSQL_USER`
- `EXTERNAL_MYSQL_PASSWORD`
- `EXTERNAL_MYSQL_SCHEMA_SIMULATION_PROJECT`
- `EXTERNAL_MYSQL_SCHEMA_STRUCT_MODULE`
- `EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL`
- `EXTERNAL_MYSQL_SCHEMA_UNION_OPT_CONF`
- `EXTERNAL_MYSQL_SCHEMA_SQRS_HW`

## 5. 平台功能入口与权限

平台功能使用路径：

- 公告查看：前端布局顶部公告横幅
- 公告配置：系统配置 -> 平台内容
- 埋点分析：`/analytics`
- 隐私协议：头像菜单 -> 查看隐私协议

权限边界：

- 埋点分析：`VIEW_DASHBOARD`
- 平台内容管理：`MANAGE_CONFIG`
- 隐私协议：所有已登录用户可访问

埋点工作方式：

- 前端本地队列批量上报
- 路由切换自动采集 `page_view`
- 公告曝光/关闭、隐私查看/同意分别采集
- 后端负责写入与汇总

这是内网自有埋点体系，不接外部 SaaS。

## 6. 推荐目录规划

建议统一使用：

```text
/data/structsim/
  upload/
  shared/
  logs/
```

这样 Docker 与 K3s 可以共享同一套目录语义，后续迁移更稳定。
