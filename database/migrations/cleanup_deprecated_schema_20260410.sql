-- 废弃结构安全清理脚本
-- 目标：
-- 1. 确保历史 orders.opt_param 已迁入 input_json.opt_param 后彻底删除旧列
-- 2. 对仍被代码兼容使用、但业务上已不再作为主真源的表增加废弃注释
--    - solver_resources：资源池已改为外部接口 / 后端 mock
--    - project_sim_type_rels：项目不再作为仿真类型主关联真源
--    - user_project_permissions：当前主链路尚未消费，仅保留预留说明

SET @schema_name = DATABASE();

-- 1) orders.opt_param -> input_json.opt_param 迁移与清理
SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'opt_param'
    ),
    "
      UPDATE `orders`
      SET `input_json` = JSON_SET(COALESCE(`input_json`, JSON_OBJECT()), '$.opt_param', `opt_param`)
      WHERE `opt_param` IS NOT NULL
        AND (
          `input_json` IS NULL
          OR JSON_EXTRACT(`input_json`, '$.opt_param') IS NULL
        )
    ",
    'SELECT 1'
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
      WHERE table_schema = @schema_name AND table_name = 'orders' AND column_name = 'opt_param'
    ),
    'ALTER TABLE `orders` DROP COLUMN `opt_param`',
    'SELECT 1'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) solver_resources 标记为废弃：资源池已迁移到外部接口 / 后端 mock
SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = @schema_name AND table_name = 'solver_resources'
    ),
    "ALTER TABLE `solver_resources`
     COMMENT = 'DEPRECATED: 本地求解器资源池表，现行业务以公司资源池接口或后端 mock 为主，仅为历史配置兼容保留'",
    'SELECT 1'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3) project_sim_type_rels 标记为废弃：不再作为提单初始化主真源
SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = @schema_name AND table_name = 'project_sim_type_rels'
    ),
    "ALTER TABLE `project_sim_type_rels`
     COMMENT = 'DEPRECATED: 历史项目-仿真类型关系表，当前业务不再作为提单初始化主真源，仅保留历史配置兼容'",
    'SELECT 1'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4) user_project_permissions 标记为预留：主链路暂未实际消费
SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = @schema_name AND table_name = 'user_project_permissions'
    ),
    "ALTER TABLE `user_project_permissions`
     COMMENT = 'RESERVED: 预留的用户-项目权限表，当前主链路未实际启用，后续启用前应补齐仓储与权限过滤逻辑'",
    'SELECT 1'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
