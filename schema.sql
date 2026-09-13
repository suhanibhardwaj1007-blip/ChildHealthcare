-- ==========================================================
-- Child Healthcare Platform - Database Schema
-- Database: MySQL
-- ==========================================================

CREATE DATABASE IF NOT EXISTS child_healthcare_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE child_healthcare_db;

-- 1. Users Table (Parents, Guardians, Pediatricians, Staff)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('parent', 'doctor', 'admin') DEFAULT 'parent',
    profile_image VARCHAR(255) DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Initial Demo Parent and Doctor (Optional Seed)
-- Passwords will be securely hashed when users register via the web interface.
