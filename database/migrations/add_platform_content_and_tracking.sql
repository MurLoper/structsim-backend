CREATE TABLE IF NOT EXISTS platform_settings (
  `key` VARCHAR(64) NOT NULL PRIMARY KEY COMMENT '配置键',
  value_json JSON NOT NULL COMMENT '配置值(JSON)',
  description VARCHAR(255) NULL COMMENT '配置说明',
  updated_by VARCHAR(32) NULL COMMENT '最后更新人域账号',
  created_at BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
  updated_at BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间'
) COMMENT='平台设置';

CREATE TABLE IF NOT EXISTS announcements (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(120) NOT NULL COMMENT '公告标题',
  content TEXT NOT NULL COMMENT '公告正文',
  level VARCHAR(16) NOT NULL DEFAULT 'info' COMMENT '公告等级',
  is_active TINYINT NOT NULL DEFAULT 1 COMMENT '1=启用,0=停用',
  dismissible TINYINT NOT NULL DEFAULT 1 COMMENT '1=可关闭,0=不可关闭',
  sort INT NOT NULL DEFAULT 100 COMMENT '排序值',
  start_at BIGINT NULL COMMENT '生效开始时间戳',
  end_at BIGINT NULL COMMENT '生效结束时间戳',
  link_text VARCHAR(60) NULL COMMENT '链接文案',
  link_url VARCHAR(255) NULL COMMENT '链接地址',
  created_by VARCHAR(32) NULL COMMENT '创建人域账号',
  updated_by VARCHAR(32) NULL COMMENT '最后更新人域账号',
  created_at BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
  updated_at BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间',
  KEY idx_announcements_active (is_active, sort, updated_at),
  KEY idx_announcements_window (start_at, end_at)
) COMMENT='公告表';

CREATE TABLE IF NOT EXISTS privacy_policy_acceptances (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  domain_account VARCHAR(32) NOT NULL COMMENT '用户域账号',
  policy_version VARCHAR(32) NOT NULL COMMENT '已同意版本',
  accepted_at BIGINT NOT NULL DEFAULT 0 COMMENT '同意时间',
  accepted_ip VARCHAR(64) NULL COMMENT '同意时IP',
  created_at BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
  updated_at BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间',
  KEY idx_privacy_acceptance_user (domain_account, policy_version, accepted_at)
) COMMENT='隐私协议同意记录';

CREATE TABLE IF NOT EXISTS tracking_events (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  event_name VARCHAR(64) NOT NULL COMMENT '事件名',
  event_type VARCHAR(32) NOT NULL COMMENT '事件类型',
  page_path VARCHAR(255) NULL COMMENT '页面路径',
  target VARCHAR(120) NULL COMMENT '事件目标',
  session_id VARCHAR(64) NULL COMMENT '会话标识',
  domain_account VARCHAR(32) NULL COMMENT '用户域账号',
  metadata_json JSON NULL COMMENT '事件元数据',
  created_at BIGINT NOT NULL DEFAULT 0 COMMENT '事件时间',
  KEY idx_tracking_events_name (event_name, created_at),
  KEY idx_tracking_events_type (event_type, created_at),
  KEY idx_tracking_events_page (page_path, created_at),
  KEY idx_tracking_events_user (domain_account, created_at)
) COMMENT='前端埋点事件';
