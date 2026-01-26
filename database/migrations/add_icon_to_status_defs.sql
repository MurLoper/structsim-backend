-- 添加 icon 字段到 status_defs 表
-- 用于支持状态图标配置

-- 添加 icon 列
ALTER TABLE status_defs ADD COLUMN icon VARCHAR(100) COMMENT '图标样式';

-- 更新现有数据，添加图标配置
UPDATE status_defs SET icon = 'icon-weikaishi' WHERE code = 'NOT_STARTED';
UPDATE status_defs SET icon = 'icon-yunxingzhong' WHERE code = 'RUNNING';
UPDATE status_defs SET icon = 'icon-yiwancheng' WHERE code = 'COMPLETED';
UPDATE status_defs SET icon = 'icon-yunxingshibai' WHERE code = 'FAILED';
UPDATE status_defs SET icon = 'icon-caogaoxiang' WHERE code = 'DRAFT';
UPDATE status_defs SET icon = 'icon-shoudongzhongzhi' WHERE code = 'CANCELLED';
UPDATE status_defs SET icon = 'icon-qidongzhong' WHERE code = 'STARTING';
UPDATE status_defs SET icon = 'icon-xiaomokuaiwancheng' WHERE code = 'PARTIAL_COMPLETED';

-- 更新状态配置数据，使用完整的状态定义
-- 删除旧的状态配置
DELETE FROM status_defs;

-- 插入新的状态配置
INSERT INTO status_defs (id, name, code, type, color, icon, valid, sort, created_at, updated_at) VALUES
(0, '未开始', 'NOT_STARTED', 'PROCESS', '#808080', 'icon-weikaishi', 1, 0, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(1, '运行中', 'RUNNING', 'PROCESS', '#0000FF', 'icon-yunxingzhong', 1, 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(2, '已完成', 'COMPLETED', 'FINAL', '#008000', 'icon-yiwancheng', 1, 2, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(3, '运行失败', 'FAILED', 'FINAL', '#FF0000', 'icon-yunxingshibai', 1, 3, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(4, '草稿箱', 'DRAFT', 'PROCESS', '#0000FF', 'icon-caogaoxiang', 1, 4, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(5, '手动终止', 'CANCELLED', 'FINAL', '#FFA500', 'icon-shoudongzhongzhi', 1, 5, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(6, '启动中', 'STARTING', 'PROCESS', '#800080', 'icon-qidongzhong', 1, 6, UNIX_TIMESTAMP(), UNIX_TIMESTAMP()),
(7, '小模块完成', 'PARTIAL_COMPLETED', 'PROCESS', '#0000FF', 'icon-xiaomokuaiwancheng', 1, 7, UNIX_TIMESTAMP(), UNIX_TIMESTAMP());

