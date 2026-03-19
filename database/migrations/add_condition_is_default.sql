-- 工况配置表增加 is_default 字段
ALTER TABLE condition_configs ADD COLUMN is_default SMALLINT DEFAULT 0 COMMENT '1=默认仿真类型,0=非默认';
