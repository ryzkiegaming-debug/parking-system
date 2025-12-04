-- Run this script inside phpMyAdmin (MySQL/MariaDB) to bootstrap the project DB

CREATE DATABASE IF NOT EXISTS `nwssu_parking_db`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `nwssu_parking_db`;

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_number` VARCHAR(30) NOT NULL,
  `full_name` VARCHAR(150) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uniq_student_number` (`student_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `parking_slots` (
  `slot_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `slot_name` VARCHAR(10) NOT NULL,
  `is_available` TINYINT(1) DEFAULT 1,
  `location` VARCHAR(150) DEFAULT 'Nwssu Calbayog City, Samar, Philippines',
  PRIMARY KEY (`slot_id`),
  UNIQUE KEY `uniq_slot_name` (`slot_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `bookings` (
  `booking_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `slot_id` INT UNSIGNED NOT NULL,
  `entry_date` DATE NOT NULL,
  `entry_time` TIME NOT NULL,
  `exit_date` DATE NOT NULL,
  `exit_time` TIME NOT NULL,
  `status` ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
  `booked_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`booking_id`),
  UNIQUE KEY `uniq_slot_datetime` (`slot_id`, `entry_date`, `entry_time`),
  CONSTRAINT `fk_bookings_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_bookings_slot`
    FOREIGN KEY (`slot_id`) REFERENCES `parking_slots` (`slot_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO `parking_slots` (`slot_name`) VALUES
('A1'), ('A2'), ('A3'), ('A4'), ('A5'),
('A6'), ('A7'), ('A8'), ('A9'), ('A10');

-- Insert default test user for direct login
-- Username: 12345, Password: admin123
-- (This uses a pre-generated bcrypt hash for the password "admin123")
-- To generate a new hash, run: echo password_hash('your_password', PASSWORD_DEFAULT);
INSERT IGNORE INTO `users` (`student_number`, `full_name`, `password_hash`) VALUES
('12345', 'Admin User', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi');

