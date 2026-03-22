-- 用户身份字段升级（MySQL）
-- 目标：
-- 1. domain_account 作为业务唯一标识
-- 2. user_name / real_name 取代旧的 username / name
-- 3. 删除 users.username / users.name 历史字段

ALTER TABLE users ADD COLUMN IF NOT EXISTS domain_account VARCHAR(32) NULL COMMENT '域账号';
ALTER TABLE users ADD COLUMN IF NOT EXISTS lc_user_id VARCHAR(64) NULL COMMENT '外部平台用户ID';
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_name VARCHAR(100) NULL COMMENT '用户展示名';
ALTER TABLE users ADD COLUMN IF NOT EXISTS real_name VARCHAR(100) NULL COMMENT '真实姓名';

UPDATE users
SET domain_account = LOWER(TRIM(COALESCE(domain_account, username, '')))
WHERE domain_account IS NULL OR TRIM(domain_account) = '';

UPDATE users
SET user_name = COALESCE(NULLIF(TRIM(user_name), ''), NULLIF(TRIM(name), ''), domain_account, username)
WHERE user_name IS NULL OR TRIM(user_name) = '';

UPDATE users
SET real_name = COALESCE(NULLIF(TRIM(real_name), ''), NULLIF(TRIM(name), ''), user_name, domain_account, username)
WHERE real_name IS NULL OR TRIM(real_name) = '';

ALTER TABLE users MODIFY COLUMN domain_account VARCHAR(32) NOT NULL COMMENT '域账号';

DROP INDEX `username` ON users;
ALTER TABLE users DROP COLUMN username;
ALTER TABLE users DROP COLUMN name;

CREATE UNIQUE INDEX uq_users_domain_account ON users(domain_account);
CREATE UNIQUE INDEX uq_users_lc_user_id ON users(lc_user_id);

ALTER TABLE orders MODIFY COLUMN created_by VARCHAR(32) NULL COMMENT '创建人域账号';

ALTER TABLE upload_files MODIFY COLUMN user_id VARCHAR(32) NOT NULL COMMENT '上传用户标识(域账号)';
CREATE INDEX idx_upload_files_user_id ON upload_files(user_id);
