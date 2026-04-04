# 登录与 SSO 说明

适用范围：`structsim-backend` 当前认证实现

## 1. 当前统一口径

平台认证链路统一采用：

1. 登录或 SSO 回调只负责认证并签发 `token`
2. 前端拿到 `token` 后，再调用 `GET /api/v1/auth/session`
3. 会话接口返回最新的：
   - 用户信息
   - 权限
   - 菜单

也就是说：

- 登录接口不再直接返回用户信息快照
- SSO 回调接口也不再直接返回用户信息快照
- 页面刷新、SSO 回调完成、重新进入系统时，前端都以 `/auth/session` 为唯一会话真源

## 2. 登录密码安全

当前密码传输采用 **RSA-OAEP**。

前端链路：

1. `GET /api/v1/auth/public-key`
2. 前端使用返回的公钥加密密码
3. `POST /api/v1/auth/login`

登录请求体：

```json
{
  "domainAccount": "z00012345",
  "passwordCiphertext": "<base64-ciphertext>",
  "keyId": "auth-login-default"
}
```

后端处理顺序：

1. 读取密文与 `keyId`
2. 用私钥解密
3. 调用公司账号密码验证接口
4. 验证通过后签发平台 `token`

说明：

- 这是应用层附加保护
- 不能替代 HTTPS / TLS
- 生产环境仍要求内网网关或服务层具备 TLS 保护

## 3. 认证接口

### `GET /api/v1/auth/public-key`

返回登录加密所需公钥：

- `keyId`
- `algorithm`
- `publicKeyPem`

### `POST /api/v1/auth/login`

账号密码登录，只返回：

```json
{
  "token": "<jwt>"
}
```

### `POST /api/v1/auth/sso/callback`

SSO 回调换取平台 token，只返回：

```json
{
  "token": "<jwt>"
}
```

### `GET /api/v1/auth/session`

当前会话唯一真源，返回：

- `user`
- `menus`

### `GET /api/v1/auth/verify`

兼容接口，当前仍保留，但内部口径等同于 `/auth/session`。前端不应再把它作为长期主流程。

### `GET /api/v1/auth/me`

辅助接口，仅返回当前用户信息。

### `GET /api/v1/auth/menus`

辅助接口，仅返回当前菜单树。

## 4. JWT identity 统一规则

平台内部统一使用 `domain_account` 作为 JWT identity 和业务主键。

固定约束：

- 订单关联用户：只认 `domain_account`
- 会话用户：只认 `domain_account`
- SSO 回调映射：只认 `domain_account`
- 菜单和权限归属：只认 `domain_account`

不再允许把以下字段当作用户主键继续扩散：

- `user.id`
- 历史 `lcUserId`
- 显示名称
- 邮箱

## 5. 配置项

当前与登录加密相关的环境变量：

- `AUTH_LOGIN_RSA_KEY_ID`
- `AUTH_LOGIN_RSA_PRIVATE_KEY`
- `AUTH_LOGIN_RSA_PUBLIC_KEY`
- `AUTH_LOGIN_RSA_PRIVATE_KEY_PATH`
- `AUTH_LOGIN_RSA_PUBLIC_KEY_PATH`

说明：

- 私钥优先从环境变量或挂载文件读取
- 私钥不得提交到代码仓库
- 开发/测试环境允许后端自动生成稳定的本地开发密钥对，方便联调并避免公钥缓存后解密失败

账号密码登录与用户资料同步相关环境变量：

- `AUTH_COMPANY_PASSWORD_VERIFY_URL`
- `AUTH_COMPANY_PASSWORD_VERIFY_METHOD`
- `AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT`
- `AUTH_GET_USER_INFO_URL`
- `AUTH_GET_USER_INFO_METHOD`
- `AUTH_GET_USER_INFO_TIMEOUT`
- `AUTH_DEFAULT_ROLE_CODE`

当前固定口径：

- 公司验密接口只负责校验账号密码是否有效
- 用户真实资料统一通过 `AUTH_GET_USER_INFO_URL` 拉取
- `AUTH_GET_USER_INFO_URL` 固定携带：
  - `domain_account`
  - 上一步验密或公司认证接口返回的 `access_token`
- 后端会同步补充 `Authorization: Bearer <access_token>` 请求头，以兼容偏 SSO 风格的公司接口
- 新用户首次登录后会自动写入本地 `users` 表
- 若本地无角色，则自动分配默认角色，默认使用 `GUEST`

## 6. 会话一致性原则

前端必须遵守以下规则：

- 有 token 但无 session：阻塞业务页渲染并拉取 `/auth/session`
- 无 token：立即清空持久化登录态
- token 失效：统一回登录页
- 不允许只靠本地缓存的 `user/menus/permissions` 判定“已登录”

目标是避免出现这类分裂状态：

- 页面看起来已登录
- 但接口实际已 401

## 7. SSO 与普通登录关系

平台长期保留两种接入方式：

- 公司账号密码登录
- 公司 SSO 回调登录

但二者后续统一收敛到同一条会话链：

- 登录成功 -> token
- token -> `/auth/session`

因此：

- SSO 不再维护一套独立会话模型
- 普通登录也不再返回独立用户快照
