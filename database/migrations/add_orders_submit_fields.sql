-- orders 提交审计字段与兼容清理
-- 1. 新增 domain_account，作为申请单提交用户域账号
-- 2. 新增 base_dir，作为自动化成功后的工作目录回填字段
-- 3. 将历史 orders.opt_param 迁入 input_json.opt_param 后删除旧列

SET @schema_name = DATABASE();

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'domain_account'
    ),
    'SELECT 1',
    "ALTER TABLE `orders` ADD COLUMN `domain_account` VARCHAR(32) NULL COMMENT '提交用户域账号'"
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE `orders`
SET `domain_account` = LOWER(TRIM(COALESCE(`domain_account`, `created_by`, '')))
WHERE `domain_account` IS NULL OR TRIM(`domain_account`) = '';

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = @schema_name AND table_name = 'orders' AND index_name = 'idx_orders_domain_account'
    ),
    'SELECT 1',
    "ALTER TABLE `orders` ADD INDEX `idx_orders_domain_account` (`domain_account`)"
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'base_dir'
    ),
    'SELECT 1',
    "ALTER TABLE `orders` ADD COLUMN `base_dir` VARCHAR(500) NULL COMMENT '申请单工作目录'"
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE `orders`
SET `input_json` = JSON_SET(COALESCE(`input_json`, JSON_OBJECT()), '$.opt_param', `opt_param`)
WHERE `opt_param` IS NOT NULL
  AND (
    `input_json` IS NULL
    OR JSON_EXTRACT(`input_json`, '$.opt_param') IS NULL
  );

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'opt_param'
    ),
    "ALTER TABLE `orders` DROP COLUMN `opt_param`",
    'SELECT 1'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
