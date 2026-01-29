-- 菜单表字段迁移脚本
-- 为 menus 表添加新字段: component, menu_type, hidden, permission_code

-- 检查并添加 component 字段
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'menus'
               AND COLUMN_NAME = 'component');
SET @sql := IF(@exist = 0,
    'ALTER TABLE menus ADD COLUMN component VARCHAR(200) COMMENT ''前端组件路径'' AFTER path',
    'SELECT ''component already exists''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 menu_type 字段
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'menus'
               AND COLUMN_NAME = 'menu_type');
SET @sql := IF(@exist = 0,
    'ALTER TABLE menus ADD COLUMN menu_type VARCHAR(20) DEFAULT ''MENU'' COMMENT ''菜单类型'' AFTER component',
    'SELECT ''menu_type already exists''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 hidden 字段
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'menus'
               AND COLUMN_NAME = 'hidden');
SET @sql := IF(@exist = 0,
    'ALTER TABLE menus ADD COLUMN hidden SMALLINT DEFAULT 0 COMMENT ''是否隐藏'' AFTER menu_type',
    'SELECT ''hidden already exists''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 permission_code 字段
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'menus'
               AND COLUMN_NAME = 'permission_code');
SET @sql := IF(@exist = 0,
    'ALTER TABLE menus ADD COLUMN permission_code VARCHAR(50) COMMENT ''所需权限编码'' AFTER hidden',
    'SELECT ''permission_code already exists''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Migration completed!' AS result;
