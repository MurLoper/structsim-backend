-- 参数组合支持默认算法 + DOE文件元数据
-- 兼容低版本MySQL（不依赖 ADD COLUMN IF NOT EXISTS）
-- 执行时间: 2026-03-21

SET @schema_name = DATABASE();

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = @schema_name AND table_name = 'param_groups' AND column_name = 'alg_type'
  ),
  'SELECT 1',
  "ALTER TABLE `param_groups` ADD COLUMN `alg_type` SMALLINT DEFAULT 2 COMMENT '默认算法: 1=贝叶斯, 2=DOE枚举, 5=DOE文件'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = @schema_name AND table_name = 'param_groups' AND column_name = 'doe_file_name'
  ),
  'SELECT 1',
  "ALTER TABLE `param_groups` ADD COLUMN `doe_file_name` VARCHAR(255) NULL COMMENT 'DOE文件名'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = @schema_name AND table_name = 'param_groups' AND column_name = 'doe_file_heads'
  ),
  'SELECT 1',
  "ALTER TABLE `param_groups` ADD COLUMN `doe_file_heads` JSON NULL COMMENT 'DOE文件表头'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = @schema_name AND table_name = 'param_groups' AND column_name = 'doe_file_data'
  ),
  'SELECT 1',
  "ALTER TABLE `param_groups` ADD COLUMN `doe_file_data` JSON NULL COMMENT 'DOE文件数据'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
