-- StructSim FK Restore SQL
-- ExportedAt: 2026-04-11T00:04:19.309382

SET FOREIGN_KEY_CHECKS=0;
ALTER TABLE `users` ADD CONSTRAINT `fk_users_department_id` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`);
SET FOREIGN_KEY_CHECKS=1;
