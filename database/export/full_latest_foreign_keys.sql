-- StructSim FK Restore SQL
-- ExportedAt: 2026-04-10T23:09:46.240380

SET FOREIGN_KEY_CHECKS=0;
ALTER TABLE `users` ADD CONSTRAINT `fk_users_department_id` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`);
SET FOREIGN_KEY_CHECKS=1;
