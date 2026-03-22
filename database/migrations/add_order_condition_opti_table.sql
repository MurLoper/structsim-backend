-- 订单 condition 运行实体升级
-- 兼容重复执行，避免依赖 ADD COLUMN IF NOT EXISTS
-- 执行时间: 2026-03-22

SET @schema_name = DATABASE();

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'opt_issue_id'
  ),
  'SELECT 1',
  "ALTER TABLE `orders` ADD COLUMN `opt_issue_id` INT NULL COMMENT '自动优化申请单ID'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.statistics
    WHERE table_schema = @schema_name AND table_name = 'orders' AND index_name = 'idx_orders_opt_issue_id'
  ),
  'SELECT 1',
  "ALTER TABLE `orders` ADD INDEX `idx_orders_opt_issue_id` (`opt_issue_id`)"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'condition_summary'
  ),
  'SELECT 1',
  "ALTER TABLE `orders` ADD COLUMN `condition_summary` JSON NULL COMMENT '工况概览 {姿态名: [仿真类型名,...]}'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  EXISTS(
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = @schema_name AND table_name = 'order_condition_opti'
  ),
  'SELECT 1',
  "CREATE TABLE `order_condition_opti` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `order_id` BIGINT NOT NULL COMMENT '主单ID',
    `order_no` VARCHAR(50) DEFAULT NULL COMMENT '主单编号冗余',
    `opt_issue_id` INT NOT NULL COMMENT '自动优化申请单ID',
    `opt_job_id` INT DEFAULT NULL COMMENT '自动化方案作业ID',
    `condition_id` BIGINT NOT NULL COMMENT 'condition标识',
    `fold_type_id` INT NOT NULL COMMENT '姿态ID',
    `fold_type_name` VARCHAR(100) DEFAULT NULL COMMENT '姿态名称快照',
    `sim_type_id` INT NOT NULL COMMENT '仿真类型ID',
    `sim_type_name` VARCHAR(100) DEFAULT NULL COMMENT '仿真类型名称快照',
    `algorithm_type` VARCHAR(32) DEFAULT NULL COMMENT '算法类型',
    `round_total` INT DEFAULT 0 COMMENT '轮次数量概览',
    `output_count` INT DEFAULT 0 COMMENT '输出数量概览',
    `solver_id` VARCHAR(64) DEFAULT NULL COMMENT '求解器标识，包含类型和版本语义',
    `care_device_ids` JSON DEFAULT NULL COMMENT '关注器件ID列表',
    `remark` TEXT COMMENT 'condition级备注',
    `running_module` VARCHAR(64) DEFAULT NULL COMMENT '当前运行模块',
    `process` DECIMAL(5,2) DEFAULT 0 COMMENT '进度百分比',
    `status` SMALLINT DEFAULT 0 COMMENT '状态',
    `statistics_json` JSON DEFAULT NULL COMMENT '统计摘要',
    `result_summary_json` JSON DEFAULT NULL COMMENT '结果摘要',
    `condition_snapshot` JSON NOT NULL COMMENT '完整condition快照',
    `external_meta` JSON DEFAULT NULL COMMENT '外部扩展信息',
    `created_at` INT DEFAULT NULL,
    `updated_at` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_oco_order_condition` (`order_id`, `condition_id`),
    UNIQUE KEY `uk_oco_opt_job_id` (`opt_job_id`),
    KEY `idx_oco_opt_issue_id` (`opt_issue_id`),
    KEY `idx_oco_order_status` (`order_id`, `status`),
    KEY `idx_oco_order_simtype` (`order_id`, `sim_type_id`),
    KEY `idx_oco_order_foldtype` (`order_id`, `fold_type_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='订单condition优化运行实体表'"
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
