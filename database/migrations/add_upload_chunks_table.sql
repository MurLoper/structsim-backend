-- 上传分片表修复迁移
-- 目的：修复历史库缺少 upload_chunks 导致上传接口报错
-- 执行时间: 2026-03-21

CREATE TABLE IF NOT EXISTS `upload_chunks` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `upload_id` VARCHAR(36) NOT NULL COMMENT '上传会话UUID',
  `chunk_index` INT NOT NULL COMMENT '分片索引',
  `chunk_hash` VARCHAR(64) DEFAULT NULL COMMENT '分片SHA-256哈希',
  `uploaded_at` INT NOT NULL COMMENT '上传时间戳',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_upload_chunk` (`upload_id`, `chunk_index`),
  KEY `idx_upload_id` (`upload_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件上传分片记录表';
