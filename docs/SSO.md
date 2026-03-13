# SSO单点登录集成指南

## 概述

本项目支持SSO（单点登录）模式，可通过配置快速切换普通登录和SSO登录。

## 后端配置

### 1. SSO路由

SSO服务已集成到后端，提供以下接口：

- `POST /api/v1/sso/login` - SSO登录
- `GET /api/v1/sso/verify` - 验证token
- `POST /api/v1/sso/logout` - 登出

### 2. 使用SSO中间件

在需要SSO认证的路由上使用装饰器：

```python
from app.middleware.sso_auth import sso_required

@app.route('/api/protected')
@sso_required
def protected_route():
    user = g.current_user
    return jsonify({'user': user.username})
```

## 前端配置

### 1. 环境变量

在 `.env` 文件中配置：

```bash
# 开发环境 - 普通登录
VITE_SSO_ENABLED=false

# 内网环境 - SSO登录
VITE_SSO_ENABLED=true
VITE_SSO_SERVER_URL=http://sso.company.com
```

### 2. 使用SSO服务

```typescript
import { ssoLogin, verifySSOToken, ssoLogout } from '@/services/ssoService';
import { SSO_CONFIG } from '@/config/sso';

// 检查是否启用SSO
if (SSO_CONFIG.enabled) {
  // SSO登录
  const { access_token, user } = await ssoLogin(username, password);

  // 验证token
  const user = await verifySSOToken();

  // 登出
  await ssoLogout();
}
```

## 切换模式

### 开发环境（普通登录）

```bash
# .env
VITE_SSO_ENABLED=false
```

### 内网环境（SSO登录）

```bash
# .env.production
VITE_SSO_ENABLED=true
VITE_SSO_SERVER_URL=http://internal-sso.company.com
```

## API接口

### 登录

```bash
POST /api/v1/sso/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

# 响应
{
  "access_token": "eyJ...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

### 验证Token

```bash
GET /api/v1/sso/verify
Authorization: Bearer eyJ...

# 响应
{
  "valid": true,
  "user": {...}
}
```

### 登出

```bash
POST /api/v1/sso/logout
Authorization: Bearer eyJ...

# 响应
{
  "message": "登出成功"
}
```

## 注意事项

1. SSO token默认有效期24小时
2. 前端自动在请求头添加 `Authorization: Bearer <token>`
3. Token过期后自动跳转登录页
4. 支持一键切换SSO和普通登录模式
