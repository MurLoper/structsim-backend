-- 将 doe_default_value 重命名为 enum_values，删除 bayesian_default_value
-- min_val, max_val 已存在无需添加

ALTER TABLE param_group_param_rels RENAME COLUMN doe_default_value TO enum_values;
ALTER TABLE param_group_param_rels DROP COLUMN bayesian_default_value;

