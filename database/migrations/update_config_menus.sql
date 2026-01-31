-- 更新配置管理菜单结构
-- 执行时间: 2026-01-31

-- 更新配置管理父菜单路径
UPDATE menus SET path = '/config' WHERE id = 4;

-- 更新配置子菜单
UPDATE menus SET
    name = 'Basic Config',
    title_i18n_key = 'nav.config.basic',
    icon = 'Cube',
    path = '/config/basic',
    component = 'pages/configuration/BasicConfig'
WHERE id = 41;

UPDATE menus SET
    name = 'Groups Config',
    title_i18n_key = 'nav.config.groups',
    icon = 'Folder',
    path = '/config/groups',
    component = 'pages/configuration/GroupsConfig'
WHERE id = 42;

UPDATE menus SET
    name = 'Relations Config',
    title_i18n_key = 'nav.config.relations',
    icon = 'Link',
    path = '/config/relations',
    component = 'pages/configuration/RelationsConfig'
WHERE id = 43;

UPDATE menus SET
    name = 'System Config',
    title_i18n_key = 'nav.config.system',
    icon = 'Server',
    path = '/config/system',
    component = 'pages/configuration/SystemConfig'
WHERE id = 44;

UPDATE menus SET
    name = 'Permissions',
    title_i18n_key = 'nav.config.permissions',
    icon = 'Shield',
    path = '/config/permissions',
    component = 'pages/configuration/PermissionsConfig'
WHERE id = 45;

-- 更新新建仿真路径
UPDATE menus SET path = '/create' WHERE id = 3;
