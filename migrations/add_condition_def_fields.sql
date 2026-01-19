-- 为 condition_defs 表添加缺失的字段
-- 执行时间: 2024-01-17

-- 添加 category 字段
ALTER TABLE condition_defs ADD COLUMN category VARCHAR(50) COMMENT '工况分类';

-- 添加 unit 字段
ALTER TABLE condition_defs ADD COLUMN unit VARCHAR(20) COMMENT '单位';

-- 重命名 schema 字段为 condition_schema (避免与 SQL 关键字冲突)
ALTER TABLE condition_defs CHANGE COLUMN `schema` condition_schema JSON COMMENT '工况参数schema定义';

-- 添加 created_at 和 updated_at 字段（如果不存在）
ALTER TABLE condition_defs ADD COLUMN IF NOT EXISTS created_at INT COMMENT '创建时间';
ALTER TABLE condition_defs ADD COLUMN IF NOT EXISTS updated_at INT COMMENT '更新时间';

