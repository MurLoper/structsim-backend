-- 为 orders 表添加 condition_summary 字段
-- 用于列表页快速展示工况概览，避免加载完整 input_json
-- 执行时间: 2025-01-18

ALTER TABLE orders ADD COLUMN IF NOT EXISTS condition_summary JSON COMMENT '工况概览 {姿态名: [仿真类型名,...]}';

