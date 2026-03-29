-- StructSim FK Restore SQL
-- ExportedAt: 2026-03-25T22:01:45.619397

SET FOREIGN_KEY_CHECKS=0;
ALTER TABLE `users` ADD CONSTRAINT `fk_users_department_id` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`);
SET FOREIGN_KEY_CHECKS=1;
