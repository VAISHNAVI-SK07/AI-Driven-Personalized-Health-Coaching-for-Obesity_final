-- MySQL schema for
-- "AI-Driven Platform for Personalized Health Coaching for Obesity"
-- Database name: ai_obesity_coaching

-- NOTE:
-- 1. Run this script once to create the database and tables.
-- 2. It also inserts one default admin account and some sample data.
-- 3. Default admin credentials:
--      Email   : admin@healthcoach.com
--      Password: Admin@123

DROP DATABASE IF EXISTS ai_obesity_coaching;
CREATE DATABASE ai_obesity_coaching
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ai_obesity_coaching;

-- ----------------------------------------
-- Table: admin  (only ONE admin account is intended)
-- ----------------------------------------

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Default admin account (password = Admin@123, hashed using Werkzeug)
INSERT INTO admin (email, password_hash)
VALUES (
    'admin@healthcoach.com',
    'scrypt:32768:8:1$PKn6wA2I5vZY9tk7$6386dce8610f76726701edf42c96ebad939881f07d55cecfb26136544665ab7cfc60ba93622508d5770421bacb9243c29320e3ee8b2ddd93ceaffb3894b61f59'
);

-- ----------------------------------------
-- Table: users
-- ----------------------------------------

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    target_status ENUM('Completed', 'Ongoing', 'Not Completed') DEFAULT 'Ongoing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Sample user accounts (password = User@123)
INSERT INTO users (full_name, email, password_hash, target_status) VALUES
('John Doe', 'john@example.com', 'scrypt:32768:8:1$VqcwQQHZbdZKImHo$fc53891e1c32dbbdd21d0b8821a8ba3cc25c4cb170b8cc44648772ec1a7f7e27f4e1e3db38770bcbb65269ed78334bd51d8bb45b31efcc576e0bc33be94f6276', 'Ongoing'),
('Jane Smith', 'jane@example.com', 'scrypt:32768:8:1$VqcwQQHZbdZKImHo$fc53891e1c32dbbdd21d0b8821a8ba3cc25c4cb170b8cc44648772ec1a7f7e27f4e1e3db38770bcbb65269ed78334bd51d8bb45b31efcc576e0bc33be94f6276', 'Ongoing');

-- ----------------------------------------
-- Table: login_logs (tracks user and admin logins)
-- ----------------------------------------

CREATE TABLE login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    login_time DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------
-- Table: bmi_records (stores BMI calculation history)
-- ----------------------------------------

CREATE TABLE bmi_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    height_cm DECIMAL(5,2) NOT NULL,
    weight_kg DECIMAL(5,2) NOT NULL,
    bmi_value DECIMAL(5,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_bmi_user_date (user_id, created_at)
) ENGINE=InnoDB;

-- Sample BMI history records
INSERT INTO bmi_records (user_id, height_cm, weight_kg, bmi_value, category, created_at) VALUES
-- John: slightly improving BMI over time
(1, 175.0, 95.0, 31.02, 'Obese', '2025-12-01 10:00:00'),
(1, 175.0, 92.0, 30.04, 'Obese', '2026-01-10 10:00:00'),
-- Jane: slightly worsening BMI over time
(2, 162.0, 70.0, 26.67, 'Overweight', '2025-12-05 09:30:00'),
(2, 162.0, 74.0, 28.21, 'Overweight', '2026-01-12 09:30:00');

-- ----------------------------------------
-- Table: daily_tracking (per-user daily progress)
-- ----------------------------------------

CREATE TABLE daily_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    track_date DATE NOT NULL,
    water_completed TINYINT(1) NOT NULL DEFAULT 0,
    food_completed TINYINT(1) NOT NULL DEFAULT 0,
    workout_completed TINYINT(1) NOT NULL DEFAULT 0,
    challenge_completed TINYINT(1) NOT NULL DEFAULT 0,
    progress_percent INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_user_date (user_id, track_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Sample daily tracking for demonstration
INSERT INTO daily_tracking (
    user_id, track_date, water_completed, food_completed,
    workout_completed, challenge_completed, progress_percent
) VALUES
(1, CURDATE(), 1, 1, 0, 0, 50),
(2, CURDATE(), 1, 1, 1, 1, 100);

-- ----------------------------------------
-- Table: admin_messages (notifications from admin to users)
-- ----------------------------------------

CREATE TABLE admin_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_msg_user_date (user_id, created_at)
) ENGINE=InnoDB;

-- Sample admin messages
INSERT INTO admin_messages (admin_id, user_id, message, created_at, is_read) VALUES
(1, 1, 'Great job logging in consistently this week. Keep pushing!', NOW(), 0),
(1, 2, 'Focus on your water intake today and try to get a short walk in.', NOW(), 0);

-- ----------------------------------------
-- Table: motivational_quotes (rotated daily)
-- ----------------------------------------

CREATE TABLE motivational_quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_text TEXT NOT NULL,
    author VARCHAR(255) DEFAULT 'Unknown',
    used_date DATE NULL
) ENGINE=InnoDB;

-- Sample motivational quotes
INSERT INTO motivational_quotes (quote_text, author) VALUES
('The journey of a thousand miles begins with a single step.', 'Lao Tzu'),
('Success is the sum of small efforts, repeated day in and day out.', 'Robert Collier'),
('It does not matter how slowly you go as long as you do not stop.', 'Confucius'),
('Your body can stand almost anything. It''s your mind that you have to convince.', 'Unknown'),
('Discipline is the bridge between goals and accomplishment.', 'Jim Rohn');

-- End of schema and sample data.

