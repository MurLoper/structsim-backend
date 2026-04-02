-- 将历史 orders.created_by / domain_account 中遗留的旧 users.id 数字值
-- 回填为新的唯一账号 users.domain_account

UPDATE orders o
JOIN users u ON u.id = CAST(o.created_by AS UNSIGNED)
SET o.created_by = LOWER(TRIM(u.domain_account)),
    o.domain_account = LOWER(TRIM(u.domain_account))
WHERE o.created_by REGEXP '^[0-9]+$'
  AND u.valid = 1;
