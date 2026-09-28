-- ==========================================================
-- LittleCare - Child Healthcare Platform Database Schema
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

-- 2. Children Table (Child Health Profiles linked to Parent)
CREATE TABLE IF NOT EXISTS children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    gender ENUM('male', 'female', 'other') NOT NULL DEFAULT 'male',
    blood_group VARCHAR(10) DEFAULT NULL,
    birth_weight_kg DECIMAL(5,2) DEFAULT NULL,
    birth_height_cm DECIMAL(5,2) DEFAULT NULL,
    allergies TEXT DEFAULT NULL,
    medical_notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_parent_id (parent_id),
    INDEX idx_child_dob (dob)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Master Vaccines Catalog (Standard IAP / WHO Pediatric Immunization Schedule)
CREATE TABLE IF NOT EXISTS vaccines_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dose_number VARCHAR(50) NOT NULL,
    recommended_age_weeks INT NOT NULL,
    recommended_age_label VARCHAR(50) NOT NULL,
    prevents_disease VARCHAR(255) NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    notes TEXT DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Child Immunization Records (Tracking per Child)
CREATE TABLE IF NOT EXISTS child_vaccinations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    vaccine_id INT NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('pending', 'completed', 'overdue') DEFAULT 'pending',
    administered_date DATE DEFAULT NULL,
    administered_by VARCHAR(100) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines_master(id) ON DELETE CASCADE,
    INDEX idx_child_vaccine (child_id, vaccine_id),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Child Growth Records (Height, Weight & BMI Logs)
CREATE TABLE IF NOT EXISTS growth_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    record_date DATE NOT NULL,
    age_months INT NOT NULL,
    weight_kg DECIMAL(5,2) NOT NULL,
    height_cm DECIMAL(5,2) NOT NULL,
    head_circumference_cm DECIMAL(5,2) DEFAULT NULL,
    bmi DECIMAL(4,1) DEFAULT NULL,
    growth_status VARCHAR(50) DEFAULT 'Healthy Weight',
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
    INDEX idx_child_growth (child_id, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Doctors Directory (Verified Pediatric Specialists)
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    qualification VARCHAR(100) NOT NULL,
    experience_years INT NOT NULL,
    hospital VARCHAR(150) NOT NULL,
    consultation_fee INT NOT NULL,
    rating DECIMAL(2,1) DEFAULT 4.9,
    available_days VARCHAR(100) DEFAULT 'Mon - Sat',
    available_time VARCHAR(100) DEFAULT '10:00 AM - 05:00 PM',
    avatar VARCHAR(10) DEFAULT '👨‍⚕️'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL,
    child_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    time_slot VARCHAR(50) NOT NULL,
    reason_symptoms TEXT NOT NULL,
    status ENUM('confirmed', 'completed', 'cancelled') DEFAULT 'confirmed',
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    INDEX idx_parent_appointments (parent_id),
    INDEX idx_child_appointments (child_id),
    INDEX idx_doctor_appointments (doctor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
