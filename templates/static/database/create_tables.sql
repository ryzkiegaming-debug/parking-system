--(needs to exist before bookings)
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_number` VARCHAR(50) NOT NULL,
  `full_name` VARCHAR(150) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uniq_student_number` (`student_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Parking slots table
CREATE TABLE IF NOT EXISTS `parking_slots` (
  `slot_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `slot_name` VARCHAR(10) NOT NULL,
  `is_available` TINYINT(1) DEFAULT 1,
  `location` VARCHAR(150) DEFAULT 'Nwssu Calbayog City, Samar, Philippines',
  PRIMARY KEY (`slot_id`),
  UNIQUE KEY `uniq_slot_name` (`slot_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert parking slots A1 TO A10
INSERT IGNORE INTO `parking_slots` (`slot_name`) VALUES
('A1'), ('A2'), ('A3'), ('A4'), ('A5'),
('A6'), ('A7'), ('A8'), ('A9'), ('A10');

-- THIS TABLE TO ENTER
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


-- generate_password_hash
INSERT IGNORE INTO `users` (`student_number`, `full_name`, `password_hash`) VALUES
('12345', 'Admin User', 'scrypt:32768:8:1$O2R3EJ0ddKbkgPAU$0b730c33a5cb0efc904ce9628ecb45641590bd79749e000d394356ee00f8b4344eecba02308971becee98ac922b4b7e672a673dbb6a7b4f74c47ec14d858dcb1');

